#!/usr/bin/env python3
"""Contrôle les pièces du lot, hache la livraison et, si demandé, vérifie une archive locale."""
import argparse
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile


def sha(data):return hashlib.sha256(data).hexdigest()


def package(root, archive=None):
    def read(p):return root.joinpath(p).read_bytes()
    def load(p):return json.loads(read(p))
    report=load('rapports/Controle-12-ecrans.json'); media=load('rapports/Media-integre.json'); cfg=load('capture/guide.json')
    assert report['navigation_complete'] and report['iframe_allow_scripts_sans_reseau'] and len(report['vues'])==12 and len(report['lecture_4_extraits'])==4
    assert not report['camera_physique_testee'] and not report['erreurs_js']
    assert sha(read(media['fichier_source']))==media['sha256_source']==cfg['film']['sha256']
    embedded=json.loads(read('index.html').decode('utf-8').split('<script type="application/json" id="vv-data">',1)[1].split('</script>',1)[0]); assert sha(base64.b64decode(embedded['mp4_b64'],validate=True))==media['sha256_media_integre']
    for p in report['vues']:
        assert read(p['capture']).startswith(b'\xff\xd8')
    assert read('capture/planche-12-ecrans.jpg').startswith(b'\xff\xd8')
    need={'README.md','INTEGRATION.md','index.html','etat.json','journal-validations.md','capture/12-ecrans.md','capture/guide.json','capture/planche-12-ecrans.jpg','formulaire/Fiche-questions-T3.md','recherche/Droits-et-perimetre.md','recherche/Ecriture-et-audio.md','rapports/Controle-12-ecrans.json','rapports/Media-integre.json','media/T3-Essai-P2-r3-muet.mp4'}|{f'outils/{p}' for p in ['fabriquer.py','galerie.html','capture.json','recette.py','sceller.py','Ecriture-et-audio.md']}|{f'capture/ecrans/{i:02d}.jpg' for i in range(1,13)}
    files={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}-{'manifest.json','SHA256SUMS'}
    assert files==need,{'manquants':sorted(need-files),'inattendus':sorted(files-need)}
    for n in sorted(files):
        rel=PurePosixPath(n); assert not any(p.startswith('.') for p in rel.parts) and not (root/n).is_symlink()
        if rel.suffix=='.md':
            t=read(n).decode('utf-8'); assert not re.search(r'send\.vis\.ee|e2b\.app|/home/user/|github_pat_|gh[pousr]_[A-Za-z0-9]{20,}',t,re.I)
            for u in re.findall(r'\]\(([^\s\)]+)\)',t):
                if '://' in u or u.startswith('#'):continue
                p=((root/n).parent/u.split('#',1)[0]).resolve(); assert p.is_relative_to(root) and (p.is_file() or p==root/'manifest.json'),(n,u)
    arr=[{'chemin':n,'octets':(root/n).stat().st_size,'sha256':sha(read(n))} for n in sorted(files)]
    (root/'manifest.json').write_text(json.dumps({'format':'vitrine-video-revue-parcours-1','revision':'revue-parcours-r1','catalog_id':None,'phase':'12 écrans à valider','images_film':'montage P2-r3 et copie navigateur, non des rushs','catalogue_audio_inclus':False,'comptes_et_cles_inclus':False,'fichiers':arr},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    entries=sorted(need|{'manifest.json'}); sums=''.join(f'{sha(read(n))}  {n}\n' for n in entries); (root/'SHA256SUMS').write_text(sums,encoding='ascii'); entries+=['SHA256SUMS']
    if archive:
        assert archive.parent!=root and not archive.is_relative_to(root)
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for n in entries:
                f=zipfile.ZipInfo('t3-preuve/'+n,date_time=(2025,1,1,0,0,0));f.external_attr=0o100644 << 16; z.writestr(f,read(n),compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
        with zipfile.ZipFile(archive,'r') as z:
            assert not z.testzip() and sorted(z.namelist())==sorted('t3-preuve/'+n for n in entries)
            assert all(sha(z.read('t3-preuve/'+n))==sha(read(n)) for n in entries)
        print(f'Archive de revue : {archive.name}, {len(entries)} pièces, {archive.stat().st_size} octets. SHA-256 {sha(archive.read_bytes())}')
    print(f'{len(entries)} fichiers vérifiés, aucun fichier hors liste. Manifeste SHA-256 : {sha(read("manifest.json"))}')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('dossier',type=Path); ap.add_argument('--zip',type=Path); args=ap.parse_args(); package(args.dossier.resolve(),args.zip.resolve() if args.zip else None)
