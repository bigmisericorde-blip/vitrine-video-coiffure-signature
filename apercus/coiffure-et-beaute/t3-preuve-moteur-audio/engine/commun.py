"""Contrat et contrôle des médias du moteur de revue (Python ≥ 3.11, outils locaux)."""
from contextlib import contextmanager
from fractions import Fraction
from hashlib import file_digest, sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import fcntl
import json
import re
import shutil
import subprocess as sp
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
W, H, FPS, N, SECS, SR = 720, 1280, 30, 900, 30, 48000
TAKES = ('S1', 'S2', 'S3', 'S4')
TRACKS = ('01', '02', '03', '04')
MAX_TAKE = 48 * 1024**2

class Erreur(ValueError):
    def __init__(self, code, message, prise=None):
        super().__init__(message)
        self.code, self.prise = code, prise

    def as_dict(self):
        return {'code': self.code, 'message': str(self), **({'prise': self.prise} if self.prise else {})}


def exige(condition, code, message, prise=None):
    if not condition:
        raise Erreur(code, message, prise)


def sha(path):
    with path.open('rb') as f:
        return file_digest(f, 'sha256').hexdigest()


def objsha(obj):
    return sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def jsonunique(text):
    def pairs(items):
        d = {}
        for k, v in items:
            exige(k not in d, 'JSON', 'Un même champ apparaît plusieurs fois.')
            d[k] = v
        return d
    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=lambda _: exige(False, 'JSON', 'Valeur JSON invalide.'))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise Erreur('JSON', 'Le document JSON est illisible.') from exc


def lire(path):
    return jsonunique(path.read_text(encoding='utf-8'))


def ecrire(path, obj):
    with TemporaryDirectory(prefix='.t3-', dir=path.parent) as t:
        p = Path(t) / 'data.json'
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        p.replace(path)


@contextmanager
def verrou(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('ab') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield


def loi():
    return lire(ROOT/'contrat.json')


def lire_fiche(obj):
    cadre = loi()['fiche']
    exige(isinstance(obj, dict) and set(obj) <= set(cadre), 'FICHE', 'Fiche incomplète ou champ inconnu.')
    d = {}
    for k, regle in cadre.items():
        val = obj.get(k, '')
        exige(isinstance(val, str), 'FICHE', f'Champ {k} : utilise du texte.')
        s = unicodedata.normalize('NFC', val).strip()
        if 'choix' in regle:
            exige(s in regle['choix'], 'FICHE', 'Choisis une action dans la liste.')
        else:
            exige(len(s) <= regle['max'] and (s or not regle['requis']), 'FICHE', f'Champ {k} vide ou trop long (maximum {regle["max"]}).')
            # Profil de revue français/latin, sans codes de contrôle ni balises.
            exige(all((' ' <= c <= '~' and c not in '<>') or (0xA0 <= ord(c) <= 0x24F and unicodedata.category(c) != 'Cf')
                      or c in '–—’‘“”«»… €' for c in s), 'FICHE', f'Champ {k} : un caractère n’est pas pris en charge.')
        d[k] = s
    exige(d['action'] != 'aucune' or not d['cible'], 'FICHE', 'Enlève la destination si aucune action n’est demandée.')
    return d


class Outils:
    def __init__(self, ffmpeg=None, ffprobe=None):
        cache = Path.home()/'.cache/vv-signature'
        self.ff = str(ffmpeg or shutil.which('ffmpeg') or cache/'ffmpeg')
        self.fp = str(ffprobe or shutil.which('ffprobe') or cache/'t1-tools/ffprobe')

    def run(self, exe, args, timeout=85):
        try:
            return sp.run([exe, *map(str, args)], stdin=sp.DEVNULL, capture_output=True, timeout=timeout, check=True)
        except (OSError, sp.SubprocessError) as e:
            raise Erreur('MEDIA', 'FFmpeg n’a pas pu traiter ce média (format, ressource ou délai).') from e

    def ffmpeg(self, args, info=False, timeout=85):
        return self.run(self.ff, ['-nostdin', '-hide_banner', '-v', 'info' if info else 'error', '-xerror', *args], timeout)

    def sonde(self, file, args=('-show_streams','-show_format'), fmt='mov'):
        return json.loads(self.run(self.fp, ['-v','error','-protocol_whitelist','file,pipe', '-f', fmt,
                                             *args, '-of','json','-i', file]).stdout)

    def niveaux(self, file, fmt):
        r = self.ffmpeg(['-protocol_whitelist','file,pipe','-f',fmt,'-i',file,'-map','0:a:0',
                         '-af','ebur128=peak=true:framelog=verbose','-f','null','-'], True)
        s = r.stderr.decode(errors='replace').rsplit('Summary:',1)[-1]
        i = re.search(r'\bI:\s+([-\d.]+)\s+LUFS', s)
        p = re.search(r'True peak:\s*Peak:\s+([-\d.]+)\s+dBFS', s)
        exige(i and p, 'AUDIO', 'Impossible de mesurer la piste.')
        return {'lufs_i': float(i[1]), 'dbtp': float(p[1])}

    def signature(self, mp4, muet):
        z = self.sonde(mp4)
        s = [j for j in z['streams'] if j['codec_type']=='video']
        exige(len(z['streams'])==(1 if muet else 2) and len(s)==1, 'SORTIE', 'Flux inattendus dans le MP4.')
        v=s[0]
        exige((v['codec_name'],v['width'],v['height'],v.get('pix_fmt'),v.get('avg_frame_rate'),v.get('color_space'))
               ==('h264',W,H,'yuv420p','30/1','bt709') and v.get('duration')=='30.000000', 'SORTIE', 'Profil image non conforme.')
        packets = self.sonde(mp4, ['-select_streams','v:0','-show_packets','-show_entries','packet=pts,dts,duration,flags'])['packets']
        tb=Fraction(v['time_base']); pts=sorted(Fraction(x['pts'])*tb for x in packets)
        exige(pts==[Fraction(i,FPS) for i in range(N)] and all(int(x['duration'])*tb==Fraction(1,FPS) for x in packets),
               'SORTIE', 'Cadence ou nombre d’images non conformes.')
        stamp = [[str(Fraction(x[k])*tb) for k in ('pts','dts','duration')]+[x['flags']] for x in packets]
        cap=self.ffmpeg(['-protocol_whitelist','file,pipe','-f','mov','-i',mp4,'-map','0:v:0','-c:v','copy',
                         '-bsf:v','h264_mp4toannexb','-f','h264','pipe:1']).stdout
        return {'h264_sha256':sha256(cap).hexdigest(),'temps_sha256':objsha(stamp),'images':N,'fps':FPS,'secondes':SECS}
