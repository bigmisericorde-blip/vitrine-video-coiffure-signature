"""Paquet offline vérifié ; à l’exécution aucun accès aux originaux ou au réseau."""
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from .commun import ROOT, TRACKS, SECS, SR, sha, lire, ecrire, exige, loi

SAMPLES = SR*SECS
SOURCES = ROOT/'sources-musicales.json'
CHANGE = 'Extrait de 30 s, niveau ajusté et fondus.'


def credit(t, film=False):
    c = f"Musique : {t['titre']} — {t['artiste']} · Source : {t['fiche']} · Licence : {t['licence']} · {CHANGE}"
    if film:
        c += ' Synchronisée au film.'
    return c + (' '+t['notice_original'] if t.get('notice_original') else '')


def verifier(root):
    src = lire(SOURCES)
    exige((root/'catalogue.json').is_file(), 'PACK', 'Pack musical manquant. Aucun export sans la piste choisie.')
    cat = lire(root/'catalogue.json')
    exige(cat.get('schema')==1 and cat.get('audio_profile')==loi()['audio_profile']==src['profil']
           and cat.get('sources_sha256')==sha(SOURCES), 'PACK','Profil ou provenance du pack incorrect.')
    titres = cat.get('titres', {})
    exige(tuple(titres)==TRACKS, 'PACK','Les quatre pistes exactes sont requises.')
    for i in TRACKS:
        d = titres[i]; t=src['titres'][i]; p=root/(i+'.flac')
        exige(d.get('asset')==p.name and d.get('credit')==credit(t, True)
               and all(d.get(k)==v for k,v in t.items()) and p.is_file() and not p.is_symlink()
               and 0<p.stat().st_size<=6*1024**2 and p.stat().st_size==d.get('octets') and sha(p)==d.get('sha256'),
               'PACK', f'Ressource {i} manquante ou altérée. Aucune substitution.')
    return cat


def couper(outils, originaux, dest):
    src=lire(SOURCES); exige(not dest.exists(), 'PACK','Indique un dossier neuf pour la préparation du pack.')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(prefix='pack-t3-',dir=dest.parent) as path:
        tmp=Path(path); root=(tmp/'lot');root.mkdir(); rows={}
        for i in TRACKS:
            t=src['titres'][i]; f=originaux/(i+'.mp3'); p=root/(i+'.flac'); b=tmp/(i+'.wav')
            exige(f.is_file() and f.stat().st_size==t['octets_original'] and sha(f)==t['sha256_original'], 'SOURCE',f'Original exact {i} introuvable ou altéré.')
            start=int(Decimal(t['depart_s'])*SR)
            outils.ffmpeg(['-protocol_whitelist','file,pipe','-f','mp3','-i',f,'-map','0:a:0','-map_metadata','-1',
                     '-af',f'aformat=sample_rates={SR}:channel_layouts=stereo,atrim=start_sample={start}:end_sample={start+SAMPLES},asetpts=N/SR/TB','-c:a','pcm_f32le',b])
            a=outils.niveaux(b,'wav');gain=round(min(-18.6-a['lufs_i'],-4.5-a['dbtp']),2)
            outils.ffmpeg(['-protocol_whitelist','file,pipe','-f','wav','-i',b,'-map','0:a:0','-map_metadata','-1',
              '-af',f'volume={gain}dB,afade=t=in:st=0:d=0.07:curve=hsin,afade=t=out:st=28.88:d=1.12:curve=hsin','-ar',SR,'-ac',2,'-sample_fmt','s16',
              '-c:a','flac','-metadata',f"title={t['titre']}",'-metadata',f"artist={t['artiste']}",'-metadata',f'comment={credit(t)}',p])
            z=outils.sonde(p,fmt='flac')['streams'][0]; m=outils.niveaux(p,'flac')
            exige(int(z['duration_ts'])==SAMPLES and z['sample_rate']=='48000' and z['channels']==2 and m['dbtp']<=-3.8,
                  'PACK', f'Durée ou niveau hors contrat pour {i}.')
            rows[i]=t|{'asset':p.name,'sha256':sha(p),'octets':p.stat().st_size,'gain_db':gain,'mesures_pcm':m,'credit':credit(t,True)}
        ecrire(root/'catalogue.json',{'schema':1,'audio_profile':src['profil'],'sources_sha256':sha(SOURCES),'titres':rows})
        verifier(root);root.rename(dest)


def joindre(outils, image, image_sig, root, cat, choix, out):
    d=cat['titres'][choix]; f=root/d['asset']; exige(sha(f)==d['sha256'],'PACK','Le fond choisi a changé avant le mix.')
    reduction=0
    with TemporaryDirectory(prefix='mix-t3-',dir=out.parent) as td:
        temp=Path(td)/'film.mp4'
        for _ in range(3):
            outils.ffmpeg(['-y','-protocol_whitelist','file,pipe','-f','mov','-i',image,'-protocol_whitelist','file,pipe','-f','flac','-i',f,
                  '-map','0:v:0','-map','1:a:0','-map_metadata','-1','-map_chapters','-1','-c:v','copy','-af',f'volume={reduction:.2f}dB',
                  '-c:a','aac','-profile:a','aac_low','-b:a','160k','-ar',SR,'-ac',2,'-t',SECS,
                  '-metadata',f"comment={d['credit']}",'-metadata',f"artist={d['artiste']}",'-movflags','+faststart',temp])
            m=outils.niveaux(temp,'mov')
            if m['dbtp']<=-2: break
            reduction=round(reduction-3-m['dbtp'],2)
        exige(-24<=m['lufs_i']<=-16 and m['dbtp']<=-2, 'AUDIO', 'Le niveau du MP4 décodé est hors tolérance.')
        probe=outils.sonde(temp); a=[v for v in probe['streams'] if v['codec_type']=='audio']
        exige(len(a)==1 and (a[0]['codec_name'],a[0]['profile'],a[0]['sample_rate'],a[0]['channels'],a[0]['duration'])==('aac','LC','48000',2,'30.000000'), 'SORTIE','Flux AAC non conforme.')
        exige(probe['format']['tags'].get('comment')==d['credit'] and outils.signature(temp,muet=False)==image_sig,
               'SORTIE','Crédit, flux image ou chronologie modifiés.')
        outils.ffmpeg(['-protocol_whitelist','file,pipe','-f','mov','-i',temp,'-map','0:v:0','-map','0:a:0','-f','null','-'])
        temp.replace(out)
    return {'piste':choix,'titre':d['titre'],'artiste':d['artiste'],'licence':d['licence'],'fiche':d['fiche'],
            'audio_sha256':d['sha256'],'credit':d['credit'],'format':'AAC-LC','hz':SR,'canaux':2,'reduction_export_db':reduction,**m}
