#!/usr/bin/env python3
"""Assembler et vérifier le lot de revue à partir d’une liste fermée de fichiers."""
from argparse import ArgumentParser
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.commun import ROOT, TRACKS, TAKES, exige, ecrire, lire, loi, sha
from engine.musiques import verifier as verifier_audio

CODE = ('INTEGRATION.md','CREDITS.md','contrat.json','sources-musicales.json','requirements.txt','t3.py','service.py',
        'engine/commun.py','engine/images.py','engine/musiques.py','web/index.html','web/app.css','web/app.js',
        'exemple/fiche.json','outils/creer_exemple.py','outils/approvisionner.py','outils/recette.py','outils/recette_web.py','outils/lot.py')
AUDIO = ('audio/catalogue.json',*(f'audio/{t}.flac' for t in TRACKS))
FONTS = ('polices/DejaVuSans.ttf','polices/DejaVuSerif.ttf','polices/LICENCE-DejaVu.txt')
EX = tuple(f'exemple/{p}.mp4' for p in TAKES)
QA = ('conformite/Controle-moteur-T3.json','conformite/Controle-Parcours-Web.json','conformite/Controle-Apercu-Web.json')
FILES=tuple(sorted((*CODE,*AUDIO,*FONTS,*EX,*QA)))


def sums(d):
    return ''.join(f'{sha(d/k)}  {k}\n' for k in (*FILES,'manifest.json'))


def verifier(d):
    m=lire(d/'manifest.json');contrat=lire(d/'contrat.json'); courant=loi()
    exige(contrat==courant,'LOT','Le contrat du lot ne correspond pas au moteur de revue.')
    exige(m['schema']==1 and m['revision']==contrat['revision'] and m['audio_profile']==contrat['audio_profile']
           and m['template_id']==contrat['template_id'] and m['version']==contrat['version'], 'LOT','Identité ou profil du manifeste incompatible.')
    exige(m.get('statut')=='candidat_de_revue' and m.get('publication_autorisee') is False,
           'LOT','Ce lot est réservé à la revue et non autorisé en production.')
    exige(tuple(sorted(m['fichiers']))==FILES,'LOT','Liste des ressources incomplète.')
    for k,v in m['fichiers'].items():
        p=d/k
        exige(p.is_file() and not p.is_symlink() and p.stat().st_size==v['octets'] and sha(p)==v['sha256'],'LOT',f'Fichier absent ou incohérent : {k}')
    exige((d/'SHA256SUMS').read_text()==sums(d),'LOT','Le registre des empreintes ne concorde pas.')
    verifier_audio(d/'audio');ok=lire(d/QA[0]);web=lire(d/QA[1]);demo=lire(d/QA[2]);
    exige(ok['statut']==web['statut']==demo['statut']=='PASS' and list(ok['exports'])==list(TRACKS)
           and not ok['master_de_revue_utilise'] and ok['identite_h264_et_pts_dts']
           and web['import_quatre_prises'] and web['meme_fichier_lecture_telechargement'] and demo['exemple_demo'],'LOT','Contrôles de recette absents ou incomplets.')
    return m


def fabriquer(d,zip_path,source,qa,main_sha,revue_sha):
    exige(not d.exists() and not zip_path.exists(),'LOT','Utilise des chemins de sortie neufs.')
    exige(all(re.fullmatch(r'[0-9a-f]{40}',i) for i in (main_sha,revue_sha)),'LOT','Révisions de base et de revue requises.')
    d.parent.mkdir(parents=True,exist_ok=True);zip_path.parent.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(dir=d.parent,prefix='lot-t3-') as tmp:
        out=Path(tmp)/'lot';out.mkdir()
        chemins=dict([(k,ROOT/k) for k in CODE]+[(k,source/k) for k in (*AUDIO,*FONTS,*EX)]+list(zip(QA,qa)))
        for k,p in chemins.items():
            exige(p.is_file() and not p.is_symlink(),'LOT',f'Pièce de revue non disponible : {k}')
            t=out/k;t.parent.mkdir(parents=True,exist_ok=True);copyfile(p,t)
        role=lambda k: 'extrait musical ou catalogue' if k in AUDIO else 'police ou licence' if k in FONTS else 'mire synthétique' if k in EX else 'rapport de recette' if k in QA else 'documentation, contrat ou moteur'
        ecrire(out/'manifest.json',{'schema':1,'revision':loi()['revision'],'statut':'candidat_de_revue','template_id':loi()['template_id'],'version':loi()['version'],
              'audio_profile':loi()['audio_profile'],'compatibilite':'Atelier Python/FFmpeg local sur Linux (recette). Pas Android/OTA.',
              'base_git':main_sha,'revue_r2_reference':revue_sha,'lecture_r2_supplantee':False,'publication_autorisee':False,
              'mires':'Quatre prises synthétiques originales. Pas de prise ou de dérivé Mixkit.',
              'fichiers':{k:{'octets':(out/k).stat().st_size,'sha256':sha(out/k),'role':role(k)} for k in FILES}})
        (out/'SHA256SUMS').write_text(sums(out),encoding='ascii');verifier(out)
        # L’archive ne contient ni fichier caché ni contenu hors de la liste scellée.
        with ZipFile(zip_path,'x',compression=ZIP_DEFLATED,compresslevel=6) as z:
            for k in (*FILES,'manifest.json','SHA256SUMS'):
                i=ZipInfo('T3-Moteur-Audio-r1/'+k);i.compress_type=ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,(out/k).read_bytes())
        out.rename(d)


def main():
    c=ArgumentParser(description=__doc__);s=c.add_subparsers(dest='action',required=True);v=s.add_parser('verifier');v.add_argument('dossier',type=Path)
    f=s.add_parser('assembler');
    for k in ('dossier','zip','ressources','rapport','rapport-import','rapport-demo'):f.add_argument('--'+k,type=Path,required=True)
    f.add_argument('--base',required=True);f.add_argument('--r2',required=True);a=c.parse_args()
    if a.action=='assembler':fabriquer(a.dossier,a.zip,a.ressources,(a.rapport,a.rapport_import,a.rapport_demo),a.base,a.r2)
    m=verifier(a.dossier);print(f"{m['revision']} : {len(FILES)} pièces + manifeste et registre SHA-256.")
    if a.action=='assembler':print(f'ZIP : {a.zip.stat().st_size} octets, SHA-256 {sha(a.zip)}')


if __name__=='__main__':main()
