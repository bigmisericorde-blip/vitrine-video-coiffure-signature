"""Empreintes de livraison T2. Ne télécharge rien et ne modifie aucun média."""
from pathlib import Path
import argparse
from core import CASE, HERE, PLAN, ROOT, load, save, sha, validate

MANIFEST=HERE/'manifest-t2.json'


def build():
    case,plan=validate(load(CASE),load(PLAN))
    catalog=load(HERE/'afrobeat.json');audio=load(HERE/'recette-sonore.json');rushs=load(HERE/'manifest-rushs.json')
    if catalog['profile_id']!=plan['audio_profile'] or audio['resultat']!='PASS':
        raise ValueError('Profil audio non conforme')
    protected={f'media/{row["fichier"]}':row['sha256'] for row in rushs['prises']}
    protected['media/'+case['sortie']['file']]=audio['master_sha256']
    protected.update({f'media/afrobeat/{row["id"]}.mp4':row['video_sha256'] for row in audio['pistes']})
    for k,v in protected.items():
        if sha(ROOT/k)!=v:raise ValueError('Empreinte inattendue : '+k)
    names=[
        '.nojekyll','README.md','CREDITS.md','index.html','ecrans.html','simulation.html','film.html','reservation.html','atelier.html','cas-demo.js',
        'requirements.txt','requirements-atelier.txt',
        'ingenierie/plan.json','ingenierie/cas-test.json','ingenierie/afrobeat.json',
        'ingenierie/manifest-rushs.json','ingenierie/recette-sonore.json','ingenierie/recette-video.json',
        'ingenierie/simulation-t2.html','ingenierie/prises-web.js','ingenierie/build_ecrans.py','ingenierie/build_prises.py',
        'ingenierie/serve.py','ingenierie/serve_atelier.py','ingenierie/core.py','ingenierie/rendu.py',
        'ingenierie/mixage.py','ingenierie/mix_voix.py','ingenierie/rotation.py','ingenierie/postproduction.py','ingenierie/voix_texte.py',
        'ingenierie/fixtures/fiche-t2-recette.json',
        'final.html','ingenierie/qa_film_final.py','livrables/09-film-final-t2.md','livrables/t2-final/recette-film.json',
        'media/t2-signature-coiffure-narree.mp4','media/t1-coiffure-questions-corrigees.mp4','media/t1-coiffure-progression-validee.mp4','media/t2-signature-voix.vtt','livrables/10-questions-beaute.md',
        'livrables/07-bandes-son-afrobeat.md',
    ]
    files={ROOT/n for n in (*names,*protected)}
    files.update(p for p in (ROOT/'assets').rglob('*') if p.is_file())
    files.update(p for p in (ROOT/'livrables/12-ecrans').glob('*.webp') if p.is_file())
    files.update((ROOT/'livrables/t2-final').glob('*.webp'))
    return {'schema':'vv.coiffure.livraison/1.0','plan_canonique':PLAN.relative_to(ROOT).as_posix(),
            'artifacts':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    result=build()
    if a.check:
        if result!=load(MANIFEST):raise SystemExit('Manifest T2 à régénérer ou fichiers altérés.')
    else:save(MANIFEST,result)
    print(f'PASS : {len(result["artifacts"])} empreintes de livraison T2.')


if __name__=='__main__': main()
