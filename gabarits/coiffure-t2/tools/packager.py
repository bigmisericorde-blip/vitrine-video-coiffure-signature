#!/usr/bin/env python3
"""Construit et vérifie un paquet isolé. Liste fermée : ni Git, ni archives, ni médias privés."""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import zipfile

ROOT=Path(__file__).resolve().parents[1]
CORE='''README.md INTEGRATION.md CREDITS.md index.html simulation.html ecrans.html
config/template.json capture/guide.json ingenierie/plan.json
formulaire/questions.json formulaire/habillage.json formulaire/habillage-onglerie.json formulaire/exemples.json
schemas/template.schema.json schemas/render-job.schema.json schemas/render-result.schema.json schemas/render-error.schema.json
fixtures/contracts/job-3-prises.json fixtures/contracts/job-4-prises.json fixtures/contracts/resultat-exemple.json fixtures/contracts/erreur-exemple.json
assets/web.css assets/simulation-t2.css assets/result.css assets/capture.mjs assets/media.mjs assets/motion.mjs assets/motion-onglerie.mjs assets/cassures.mjs assets/montage-onglerie.mjs assets/render.worker.mjs
assets/fiche-production.mjs assets/ecrans-production.mjs
assets/engine/metiers.js assets/engine/contract.mjs assets/engine/fiche.mjs assets/engine/music.mjs assets/engine/resources.mjs assets/engine/rotation.mjs
assets/texte/DancingScript-Variable.ttf assets/texte/OFL-DancingScript.txt assets/texte/police.json assets/texte/lettrage.mjs assets/texte/modele-visuel.mjs
assets/Manrope.ttf assets/IBMPlexMono-Medium.ttf assets/Montserrat-Variable.ttf assets/PlusJakartaSans-Variable.ttf
assets/OFL.txt assets/OFL-Plex.txt assets/OFL-Montserrat.txt assets/OFL-PlusJakartaSans.txt
assets/vendor/mediabunny-1.66.1.min.mjs assets/vendor/mediabunny-LICENSE.txt assets/vendor/SOURCES.md
audio/music/catalogue.json audio/music/CREDITS.md docs/12-ecrans.md
tools/preview.py tools/mires.py tools/qa-production.py tools/recette-profils.py tools/qa-requirements.txt tools/test-production.mjs tools/verify-contracts.py tools/packager.py'''.split()
CORE+= ['schemas/questions.schema.json','schemas/guide.schema.json']
CORE+= ['reference/onglerie.mp4','assets/vendor/mediabunny-aac-encoder.min.mjs','assets/vendor/aac-encoder-LICENSE.txt','assets/vendor/ffmpeg-LGPL-2.1.txt','assets/vendor/ffmpeg-LICENSE.md','assets/vendor/aac-source/README.md'] + [f'assets/vendor/aac-source/src/{n}' for n in ['bridge.c','encode.worker.ts','encoder.ts','index.ts','shared.ts']]
CORE+= [f'reference/ecran-{i}.jpg' for i in range(1,5)]
CORE+= [f'fixtures/media/S{i}.mp4' for i in range(1,5)]+[f'audio/music/fonds/{c}.m4a' for c in 'ABCD']
EVIDENCE=['conformance/Recette-six-questions.json','conformance/Recette-integrale.json','conformance/Tests-contrats-rotation.json','conformance/Tests-schemas.json','conformance/Recette-profils.json','conformance/Retest-sources-audio.json','conformance/Comparaison-onglerie.json','conformance/Validation-utilisateur.json']+[f'conformance/12-ecrans/{i:02}.webp' for i in range(1,13)]
FILES=sorted(CORE+EVIDENCE)
assert len(FILES)==len(set(FILES))
MAX_BYTES=64*1024*1024

def sha(data):return hashlib.sha256(data).hexdigest()
def js(data):return (json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def parse(payload,path):return json.loads(payload[path])

def need(ok,why):
    if not ok:raise ValueError(why)

def role(path):
    if path.startswith('conformance/'):return 'preuve_locale'
    if path.startswith('reference/'):return 'film_exemple_fictif'
    if path.startswith('fixtures/media/'):return 'mire_graphique_sans_audio'
    if path.startswith('audio/music/fonds/'):return 'fond_musical_cc_by_4'
    if path.startswith('assets/') and path.endswith('.ttf'):return 'police_locale'
    if path.startswith(('tools/','schemas/','fixtures/contracts/')):return 'contrat_ou_outil'
    return 'source_ressource_ou_documentation'

def evidence_check(payload):
    t=parse(payload,'config/template.json');qa=parse(payload,'conformance/Recette-integrale.json');rot=parse(payload,'conformance/Tests-contrats-rotation.json');schem=parse(payload,'conformance/Tests-schemas.json')
    need(t['template_id']=='COIFFURE-T2' and not t['audio']['added_voice_off'] and not t['audio']['source_audio_in_output'],'Périmètre audio invalide')
    need(set(t['paths'].values())<=set(FILES),'Ressource canonique hors paquet')
    need(qa['revision']==t['version'] and qa['external_requests']==0 and qa['posts']==0 and qa['errors']==0 and qa['screens']==12 and qa['audio_failure_retry_same_job'] and qa['source_audio_reviewed_not_exported'],'Recette intégrale locale manquante')
    prof=parse(payload,'conformance/Recette-profils.json');audio=parse(payload,'conformance/Retest-sources-audio.json')
    need(len(prof['profils'])==8 and all(x['guides_confirmes']==4 for x in prof['profils']) and prof['ecrans_manucure']==12 and prof['export_sur_mires']['decoded_completely'] and not prof['validation_visuelle_humaine'],'Recette des profils manquante')
    need(len(audio)==4 and {x['id'] for x in audio}==set('ABCD') and all(x.get('identical') and x.get('decoded') and x.get('http')==200 for x in audio),'Retest des sources audio manquant')
    comp=parse(payload,'conformance/Comparaison-onglerie.json')
    need(comp['statut']=='PASS' and comp['images_comparees']==900 and comp['ssim_moyen']>=.99 and comp['ssim_image_minimum']>=.98 and comp['donnees_audio_identiques'] and all(x['identique'] for x in comp['composants_identiques']),'Comparaison Onglerie manquante')
    validation=parse(payload,'conformance/Validation-utilisateur.json')
    need(validation['rendu_general_valide'] and validation['finitions_separees'] and validation['sans_voix_pour_instant'],'Validation utilisateur manquante')
    a,b=qa['four_imports'],qa['three_imports']
    need(a['variant']!=b['variant'] and a['music_only_aac_bit_identical'] and b['music_only_aac_bit_identical'] and a['decoded_completely'] and b['decoded_completely'],'MP4 d’intégration non vérifiés')
    need(rot['form_combinations']==16 and rot['rotation_successes']==10000 and rot['rotation_repeats']==0 and schem['schemas']==4,'Schémas ou rotation non vérifiés')
    need(sha(payload[t['paths']['plan']])==t['base']['plan_sha256'],'Le plan R04 a changé')
    habillage=parse(payload,t['paths']['habillage']); need('speech_refs' not in habillage and all('narration' not in v for v in habillage['variants'].values()),'L’habillage embarque un script de test')
    for track in parse(payload,t['paths']['catalogue'])['tracks']:
        p='audio/music/'+track['path'];need(p in payload and sha(payload[p])==track['sha256'],'Fond du catalogue absent ou modifié')
    return t

def manifest(payload):
    t=evidence_check(payload)
    rows=[{'path':p,'bytes':len(payload[p]),'sha256':sha(payload[p]),'role':role(p)} for p in FILES]
    index=('\n'.join(f'{x["path"]}\t{x["sha256"]}' for x in rows if x['path'] in CORE)+'\n').encode()
    return {'schema':'vv.coiffure.integration-bundle/1','template_id':t['template_id'],'version':t['version'],'status':'release_candidate','execution_profile':t['execution_profile'],'audio_profile':t['audio_profile'],'music_catalogue_version':t['audio']['catalogue_version'],'approved_visual_reference_sha256':t['base']['approved_master_sha256'],'source_tree_sha256':sha(index),'submitted_commit':None,'source_directory_proposal':'gabarits/coiffure-t2/','ota_deployed':False,'added_voice_off':False,'optional_voice_off':True,'third_party_demo_footage_included':True,'mode_demo':'mires graphiques pour le test, référence onglerie séparée','local_only_limits':['Pas de preuve de CI distante ou de recette sur appareil physique.','Référence onglerie fictive : droits de tiers à vérifier pour tout autre usage.'], 'files':rows}

def source():
    d={}
    for p in FILES:
        f=ROOT/p;need(f.is_file() and not f.is_symlink(),f'Manque ou lien symbolique : {p}');d[p]=f.read_bytes()
    need(sum(map(len,d.values()))<MAX_BYTES,'Le paquet dépasse le budget')
    return d

def check(payload):
    need(set(payload)==set(FILES)|{'manifest.json'},'Arborescence inattendue ou fichier manquant')
    m=parse(payload,'manifest.json');data={k:payload[k] for k in FILES}
    need(m==manifest(data),'Manifeste non conforme ou empreintes différentes')
    return m

def verify_zip(path):
    with zipfile.ZipFile(path) as z:
        info=z.infolist();names=[x.filename for x in info];expected=set(FILES)|{'manifest.json'}
        need(len(names)==len(expected) and set(names)==expected,'Fichiers supplémentaires, dupliqués ou manquants dans le ZIP')
        need(sum(x.file_size for x in info)<MAX_BYTES,'Taille décompressée excessive')
        need(all(stat.S_IFMT(x.external_attr>>16) in (0,stat.S_IFREG) and not x.is_dir() for x in info),'Type de fichier ZIP inattendu')
        payload={x.filename:z.read(x) for x in info}
    m=check(payload)
    return m,payload

def unpack(dest,payload):
    need(not dest.is_symlink() and (not dest.exists() or dest.is_dir() and not list(dest.iterdir())),'Choisir un dossier de destination neuf ou vide')
    dest.mkdir(parents=True,exist_ok=True)
    for name,data in payload.items():
        p=dest/name;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)

def build(path):
    need(path.suffix=='.zip','Le chemin de sortie doit finir en .zip')
    data=source();data['manifest.json']=js(manifest(data));path.parent.mkdir(parents=True,exist_ok=True)
    working=path.with_suffix('.writing.zip')
    with zipfile.ZipFile(working,'w') as z:
        for name,raw in sorted(data.items()):
            item=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));item.create_system=3;item.external_attr=0o100644<<16
            z.writestr(item,raw,compress_type=zipfile.ZIP_DEFLATED,compresslevel=7)
    m,_=verify_zip(working);working.replace(path)
    h=sha(path.read_bytes());Path(str(path)+'.sha256').write_text(f'{h}  {path.name}\n',encoding='utf-8')
    return {**summary(m),'archive':path.name,'archive_sha256':h,'archive_bytes':path.stat().st_size}

def verify_dir(d):
    need(d.is_dir() and not d.is_symlink(),'Dossier introuvable ou symbolique')
    items=[p for p in d.rglob('*') if p.is_file() or p.is_symlink()];total=sum(x.stat().st_size for x in items if not x.is_symlink())
    need(total<MAX_BYTES and all(not x.is_symlink() for x in items),'Taille excessive ou lien symbolique dans le dossier')
    return check({x.relative_to(d).as_posix():x.read_bytes() for x in items})

def summary(m):return {'template_id':m['template_id'],'version':m['version'],'checked_files':len(m['files']),'source_tree_sha256':m['source_tree_sha256'],'approved_visual_reference_sha256':m['approved_visual_reference_sha256']}

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
    q=sub.add_parser('build');q.add_argument('archive',type=Path)
    q=sub.add_parser('verify');q.add_argument('archive',type=Path);q.add_argument('--extract',type=Path)
    q=sub.add_parser('verify-dir');q.add_argument('directory',type=Path)
    a=p.parse_args()
    try:
        if a.action=='build':s=build(a.archive)
        elif a.action=='verify':
            m,d=verify_zip(a.archive);s=summary(m)
            if a.extract:unpack(a.extract,d);s['extracted']=True
        else:s=summary(verify_dir(a.directory))
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as e:
        p.exit(1,f'Paquet refusé : {e}\n')
    print(json.dumps(s,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
