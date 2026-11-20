#!/usr/bin/env python3
"""Assemble un spot coiffure avec une piste licenciée. Aucun téléchargement réseau."""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path

from core import CASE, HERE, PLAN, ROOT, ffmpeg, load, require, save, sha, validate

PLAN_SON = HERE / 'afrobeat.json'
FORMAT = 'aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo'


def run(*args):
    return subprocess.run([ffmpeg(), '-hide_banner', '-nostdin', '-loglevel', 'info',
                           '-filter_threads', '1', '-filter_complex_threads', '1',
                           *map(str, args)], capture_output=True, check=True)


def measure(path, filters='anull'):
    log = run('-i', path, '-map', '0:a:0', '-af',
              filters + ',loudnorm=I=-20:LRA=7:TP=-1.5:print_format=json',
              '-f', 'null', '-').stderr.decode(errors='replace')
    stats = json.loads(re.findall(r'\{\s*"input_i"[^}]*\}', log)[-1])
    i, tp = (float(stats[k]) for k in ('input_i', 'input_tp'))
    require(math.isfinite(i) and math.isfinite(tp), 'Piste vide ou volume non mesurable')
    return i, tp


def length_audio(path):
    raw = run('-i', path, '-map', '0:a:0', '-ac', 1, '-ar', 8000,
              '-f', 's16le', '-').stdout
    return len(raw) / (2 * 8000)


def image_hash(path):
    return run('-i', path, '-map', '0:v:0', '-c:v', 'copy', '-hash', 'sha256',
               '-f', 'hash', '-').stdout.decode().strip()


def gain(path, filters, target, peak):
    current, tp = measure(path, filters)
    g = min(target - current, peak - tp)
    return f'{filters},volume={g:.5f}dB'


def timing(piste, case, plan):
    """Deux iris espacés d’un nombre entier de pulsations ; ne retime pas l’image."""
    fps = case['sortie']['fps']
    first, second = [c['at'] / fps for c in plan['cuts'] if c['id'] == 'iris_vert']
    push = next(c['at'] / fps for c in plan['cuts'] if c['id'] == 'ui_push')
    bpm = piste['bpm']
    require(type(bpm) in (int, float) and 85 <= bpm <= 145, 'BPM source hors plage : vérifier la pulsation mesurée')
    period = 60 / bpm
    beat = piste['temps_fort_s']
    earliest = piste.get('depuis_s', 0)
    require(all(type(a) in (int, float) and math.isfinite(a) and a >= 0 for a in (beat, earliest)),
            'Repère sonore invalide')
    # La référence est 120 BPM, pas un prétexte à accélérer de 20 % un fond validé.
    grid_candidates = [60 * n / (second - first) for n in range(12, 31)]
    near_goal = [t for t in grid_candidates if 114 <= t <= 126 and .88 <= t / bpm <= 1.12]
    moderate = [t for t in grid_candidates if .90 <= t / bpm <= 1.10]
    candidates = near_goal or sorted(moderate, key=lambda t: abs(t - 120))[:1] or [bpm]
    original = piste.get('depart_original', False)
    require(type(original) is bool and (not original or earliest == 0),
            'Une piste à attaque originale doit démarrer à 0:00')

    def offset(t, phase, grid):
        dt = t - phase
        return dt - round(dt / grid) * grid

    if piste.get('tempo_natif') is True:
        require(original, 'Le tempo natif est réservé à un début source conservé')
        target = bpm
    elif original:
        # Garder le premier coup ; choisir le tempo qui approche les iris, sans sauter l’intro.
        target = min(candidates, key=lambda t: (abs(offset(first, beat * bpm / t, 60 / t)), abs(t - bpm)))
    else:
        target = min(candidates, key=lambda t: (abs(t - bpm), abs(t - 120)))
    speed = target / bpm
    start = 0 if original else earliest + (beat - first * speed - earliest) % period
    grid, phase = 60 / target, (beat - start) / speed
    return {'bpm_source': bpm, 'bpm_sortie': round(target, 3), 'vitesse': speed,
            'debut_s': start, 'depart_original': original, 'iris_s': [first, second],
            'ecart_grille_iris_ms': [round(1000 * offset(t, phase, grid)) for t in (first, second)],
            'ecart_grille_push_ms': round(1000 * offset(push, phase, grid))}


LICENCES = {
    'pixabay': ('https://pixabay.com/service/license-summary/', 'Pixabay Content License'),
    'fma': ('https://creativecommons.org/licenses/by/4.0/', 'CC BY 4.0'),
    'freevibevault': ('https://creativecommons.org/licenses/by/4.0/', 'CC BY 4.0'),
}
MODIFICATIONS = 'Extrait de 30 s, calage, niveau, égalisation et fondus adaptés au film.'


def source_officielle(t, candidats):
    ident, source, plate = t['id'], t.get('source', ''), t.get('plateforme')
    if not isinstance(ident, str) or not isinstance(source, str) or plate not in LICENCES:
        return False
    if t.get('licence') != LICENCES[plate][0]:
        return False
    if plate == 'pixabay':
        return (ident in candidats and re.fullmatch(r'[0-9]{5,8}', ident) is not None
                and re.fullmatch(r'https://pixabay\.com/music/[a-z0-9-]+-' + ident + '/', source) is not None
                and t.get('content_id') in ('enregistre', 'badge-non-affiche'))
    if plate == 'freevibevault':
        return (re.fullmatch(r'fvv-[a-z0-9]{24}', ident) is not None
                and source == 'https://freevibevault.com/track/' + ident[4:]
                and t.get('licence_editeur') == 'https://freevibevault.com/license'
                and t.get('content_id') == 'non-verifie')
    return (re.fullmatch(r'fma-[0-9]{5,8}', ident) is not None
            and re.fullmatch(r'https://freemusicarchive\.org/music/(?:[a-z0-9-]+/){3}', source) is not None
            and t.get('content_id') == 'non-verifie')


def attribution(t):
    label = LICENCES[t['plateforme']][1]
    return f"{t['titre']} — {t['auteur']} | {t['source']} | {label} : {t['licence']} | {MODIFICATIONS}"


def selected_tracks(cfg, originals):
    require(cfg.get('schema') == 'vv.coiffure.afrobeat/1.2' and cfg.get('page') == 1,
            'Plan sonore validé et historique des tendances page 1 attendus')
    items = cfg['pistes']
    require(len(items) == 4 and len({t['id'] for t in items}) == 4,
            'Il faut exactement quatre pistes différentes et validées')
    require(len({t['sha256'] for t in items}) == 4, 'Fichier audio en double')
    slots = cfg.get('selection_finale', [])
    require([r['position'] for r in slots] == [1, 2, 3, 4]
            and [r['id'] for r in slots] == [t['id'] for t in items],
            'Les pistes doivent suivre les quatre choix validés dans l’ordre')
    require(slots[0].get('depart_original') is True, 'La piste n°1 doit conserver son attaque originale')
    excluded = set(cfg.get('ecartes_par_utilisateur', []))
    for slot, t in zip(slots, items):
        ident = t['id']
        require(ident not in excluded, f'Piste {ident} écartée par l’utilisateur')
        if slot.get('depart_original'):
            require(t.get('depart_original') is True and t.get('depuis_s', 0) == 0,
                    f'La piste {ident} doit conserver son attaque originale à 0:00')
        require(source_officielle(t, cfg['candidats']), 'Lien de source ou licence commerciale non vérifiés')
        require(all(isinstance(t[k], str) and t[k].strip() for k in ('titre', 'auteur', 'intro_0_3_s')),
                'Documenter le titre, l’auteur et le contrôle de l’introduction')
        name = t['fichier']
        require(re.fullmatch(r'[a-zA-Z0-9_.-]+\.(?:mp3|wav)', name) is not None,
                'Le fichier doit être un MP3/WAV local, sans chemin')
        path = originals / name
        require(path.is_file() and sha(path) == t['sha256'], f'Source manquante ou différente : {name}')
    return items


def render(master, source, piste, output, case, plan, voice=None):
    duration = case['sortie']['frames'] / case['sortie']['fps']
    sync = timing(piste, case, plan)
    start, speed = sync['debut_s'], sync['vitesse']
    source_duration = length_audio(source)
    require(start + duration * speed + .07 <= source_duration and piste['temps_fort_s'] < source_duration,
            f"Piste {piste['id']} trop courte pour le passage choisi")
    fade_in = .005 if sync['depart_original'] else .035
    music = (f'atrim=start={start:.8f},asetpts=PTS-STARTPTS,{FORMAT},'
             f'atempo={speed:.8f},atrim=duration={duration},'
             f'highpass=f=40,equalizer=f=2900:t=q:w=0.85:g=-2,'
             f'afade=t=in:d={fade_in},afade=t=out:st={duration-.55}:d=0.55')
    music = gain(source, music, -24 if voice else -20, -2.1)
    credit = attribution(piste) if piste.get('plateforme') in LICENCES else None
    metadata = ['-metadata', f"title=Signature Coiffure · {piste['titre']}", '-metadata', 'comment=' + credit] if credit else []
    require(output.resolve() != master.resolve(), 'Ne pas remplacer le master muet')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as folder:
        temp = Path(folder) / 'contrôle.mp4'
        son = None
        audio_inputs = ['-i', source]
        graph = f'[1:a:0]{music}[a]'
        if voice:
            from mix_voix import mix_to_wav
            bed = Path(folder) / 'lit.wav'
            mixed = Path(folder) / 'mix-voix.wav'
            run('-i', source, '-map', '0:a:0', '-af', music, '-c:a', 'pcm_s16le', bed)
            son = mix_to_wav(bed, voice, duration, mixed)
            audio_inputs = ['-i', mixed]
            graph = f'[1:a:0]{gain(mixed, FORMAT, -16.7, -1.45)}[a]'
        log = run('-i', master, *audio_inputs, '-filter_complex', graph,
                  '-map', '0:v:0', '-map', '[a]', '-map_metadata', '-1',
                  '-map_chapters', '-1', *metadata, '-c:v', 'copy', '-c:a', 'aac',
                  '-b:a', '160k', '-ar', 48000, '-t', duration, '-movflags', '+faststart', temp).stderr
        require(b'Audio: aac' in log and abs(length_audio(temp) - duration) < .04,
                'AAC ou durée audio hors contrat')
        require(image_hash(master) == image_hash(temp), 'La vidéo doit rester bit pour bit identique')
        i, tp = measure(temp)
        require(-30 <= i <= -12 and tp <= -1, 'Niveau du mix AAC hors contrat')
        temp.replace(output)
    return {**sync, 'id': piste['id'], 'source_sha256': sha(source), 'video_sha256': sha(output),
            'lufs_i': i, 'dbtp': tp, 'voix': bool(voice), 'duree_s': duration,
            **({'attribution': credit} if credit else {}), **({'mix_voix':son} if son else {})}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True, help='Dossier privé des sources officielles FMA et Pixabay')
    parser.add_argument('--plan-son', type=Path, default=PLAN_SON)
    parser.add_argument('--master', type=Path, help='Autre master muet déjà rendu avec le même plan de 30 s')
    parser.add_argument('--voix', type=Path, help='Voix montée sur la même durée (WAV/MP3), facultative')
    parser.add_argument('--piste', help='ID à rejouer ; sinon, un tirage au hasard')
    parser.add_argument('--precedente', help='ID à exclure si nouveau tirage')
    parser.add_argument('--etat-rotation', type=Path, help='Base persistante, hors des fichiers publics')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output', type=Path, help='Nom du spot MP4 exporté')
    group.add_argument('--demo', type=Path, help='Dossier cible de la démo (4 films intégrés + catalogue)')
    args = parser.parse_args()
    case, plan = validate(load(CASE), load(PLAN))
    master = args.master or ROOT / 'media' / case['sortie']['file']
    catalog_config = load(args.plan_son)
    require(catalog_config.get("profile_id")==plan["audio_profile"], "Le catalogue n’est pas le profil sonore du plan T2")
    tracks = selected_tracks(catalog_config, args.sources)
    if args.demo:
        require(not (args.piste or args.precedente or args.master), 'La démo utilise les quatre fonds et le master du cas')
        require(args.voix is None, 'La démo ne contient aucune narration de test.')
        dest = args.demo
        dest.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=dest) as folder:
            staged = Path(folder)
            catalogue, report = [], []
            for t in tracks:
                rel = Path('media') / 'afrobeat' / (t['id'] + '.mp4')
                q = render(master, args.sources / t['fichier'], t, staged / rel, case, plan, args.voix)
                public = {k: t[k] for k in ('id', 'titre', 'auteur', 'source', 'content_id', 'plateforme', 'licence')}
                public['licence_nom'] = LICENCES[t['plateforme']][1]
                public['modifications'] = MODIFICATIONS
                catalogue.append({**public, 'bpm': q['bpm_sortie'], 'video': rel.as_posix(),
                                  'sha256': q['video_sha256']})
                report.append({**q, 'position': len(catalogue), 'source': t['source'], 'licence': t['licence']})
            for t in catalogue:
                rel = Path(t['video'])
                (dest / rel).parent.mkdir(parents=True, exist_ok=True)
                (staged / rel).replace(dest / rel)
            (dest / 'assets').mkdir(exist_ok=True)
            js = ('/* Généré par ingenierie/mixage.py. */\nwindow.VV_COIFFURE_AUDIO_PROFILE = '
                  + json.dumps(catalog_config['profile_id']) + ';\nwindow.VV_AFROBEAT_CATALOGUE = ')
            (dest / 'assets' / 'afrobeat-catalogue.js').write_text(
                js + json.dumps(catalogue, ensure_ascii=False, indent=2).replace('</', '<\\/') + ';\n', encoding='utf-8')
            (dest / 'ingenierie').mkdir(exist_ok=True)
            save(dest / 'ingenierie' / 'recette-sonore.json', {'resultat': 'PASS', 'master_sha256': sha(master), 'pistes': report})
        print(f'Quatre films avec musique : {dest}')
    else:
        protected = {ROOT / 'media' / n for n in [case['sortie']['file'], *(s['media'] for s in case['scenes'])]}
        require(args.output.suffix.lower() == '.mp4' and args.output.resolve() not in protected,
                'Choisir un nouveau fichier MP4 ; les rushs et le master sont conservés')
        def montage(t):
            report = render(master, args.sources / t['fichier'], t, args.output, case, plan, args.voix)
            print(json.dumps({'piste': t['titre'], 'auteur': t['auteur'], **report}, ensure_ascii=False, indent=2))
        if args.piste:
            t = next((x for x in tracks if x['id'] == args.piste), None)
            require(t is not None, 'ID de piste inconnu')
            montage(t)
        else:
            from rotation import next_track
            with next_track(tracks, case['id'], args.etat_rotation, args.precedente) as t:
                montage(t)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, FileNotFoundError) as error:
        raise SystemExit(f'Mixage arrêté : {error}') from None
    except subprocess.CalledProcessError as error:
        raise SystemExit('FFmpeg : ' + error.stderr.decode(errors='replace').strip()[-1400:]) from None
