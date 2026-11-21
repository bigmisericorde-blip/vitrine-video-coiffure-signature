#!/usr/bin/env python3
"""Prépare le dossier autonome des douze écrans. Ne contacte aucun service."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
T3 = HERE.parent
MASTER_NAME = 'T3-Essai-P2-r3-muet.mp4'
LOCAL = T3/'recherche/essais/T3-Soin-du-visage-Essai.mp4'
SOURCES = ['https://mixkit.co/free-stock-video/a-young-woman-laying-on-a-relaxing-spa-bed-receives-52143/', 'https://mixkit.co/free-stock-video/a-young-beautiful-woman-laying-on-the-spa-bed-receives-52148/', 'https://mixkit.co/free-stock-video/young-woman-getting-a-facial-massage-52157/', 'https://mixkit.co/free-stock-video/a-young-woman-with-her-eyes-shut-receives-a-relaxing-52150/']
MIX_LICENSE = 'https://mixkit.co/license/modal/videoFree/'


def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()


def dump(p,x):
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main(master, ff, out):
    source=json.loads((HERE/'capture.json').read_text(encoding='utf-8'))
    assert sha(master)==source['film']['sha256'] and [s['id'] for s in source['scenes']]==['S1','S2','S3','S4']
    assert not out.exists(),f'Dossier de sortie déjà existant : {out}'
    for name in ('capture/ecrans','formulaire','media','recherche','rapports','outils'):(out/name).mkdir(parents=True,exist_ok=True)
    shutil.copyfile(master,out/'media'/MASTER_NAME)
    shutil.copyfile((HERE/'INTEGRATION.md') if (HERE/'INTEGRATION.md').exists() else T3/'INTEGRATION.md',out/'INTEGRATION.md')
    q=T3/'Fiche-questions-T3.md'
    if not q.exists():q=T3/'formulaire/Fiche-questions-T3.md'
    shutil.copyfile(q,out/'formulaire/Fiche-questions-T3.md')
    shutil.copyfile(HERE/'Ecriture-et-audio.md',out/'recherche/Ecriture-et-audio.md')
    for n in ('fabriquer.py','galerie.html','capture.json','recette.py','sceller.py','Ecriture-et-audio.md'):
        p=HERE/n
        if p.is_file():shutil.copyfile(p,out/'outils'/n)
    def run(args):return subprocess.run([ff,'-hide_banner','-nostdin','-v','error','-threads','2',*map(str,args)],check=True,timeout=75,capture_output=True).stdout
    dump(out/'capture/guide.json',source)
    with tempfile.TemporaryDirectory(prefix='T3-passerelle-',dir=out.parent) as tmp:
        low=Path(tmp)/'montage-demonstration.mp4'
        run(['-i',master,'-map','0:v:0','-an','-vf','scale=360:640:flags=lanczos','-c:v','libx264','-threads','3','-preset','fast','-crf','28','-maxrate','310k','-bufsize','390k','-g','48','-pix_fmt','yuv420p','-colorspace','bt709','-color_trc','bt709','-color_primaries','bt709','-movflags','+faststart',low])
        source['mp4_b64']=base64.b64encode(low.read_bytes()).decode('ascii')
        dump(out/'rapports/Media-integre.json',{'fichier_source':'media/'+MASTER_NAME,'sha256_source':sha(master),'sha256_media_integre':sha(low),'octets_media_integre':low.stat().st_size,'source_preservee':True,'film_deja_monte':True,'piste_audio_absente':True,'fps':24,'duree_s':30})
        for s in source['scenes']:
            a,b=s['extrait_images']; assert 0<=a<b<=720 and a/24<=s['miniature_s']<b/24
            jpg=run(['-ss',s['miniature_s'],'-i',master,'-vf','scale=288:512:flags=lanczos','-an','-frames:v','1','-q:v','4','-f','mjpeg','pipe:1']); assert jpg[:2]==b'\xff\xd8'
            s['poster']='data:image/jpeg;base64,'+base64.b64encode(jpg).decode('ascii')
    h=(HERE/'galerie.html').read_text(encoding='utf-8'); assert h.count('__VV_CONFIG__')==1
    payload=json.dumps(source,separators=(',',':'),ensure_ascii=False).replace('<','\\u003c')
    (out/'index.html').write_text(h.replace('__VV_CONFIG__',payload),encoding='utf-8')
    with (out/'capture/12-ecrans.md').open('w',encoding='utf-8') as f:
        f.write('# T3 — Les 12 écrans, un par un\n\n[Galerie](../index.html) · [Planche 12 écrans](planche-12-ecrans.jpg) · [Fiche de questions](../formulaire/Fiche-questions-T3.md)\n\n')
        f.write('Ouvrir la vue pour la tester ou le numéro pour voir sa capture. Le chrono et la relecture utilisent le **même extrait du film monté**, sans voix ni musique. La caméra n’est pas allumée.\n\n| Nº | Prise | Vue | Consigne ou transition | Fichier |\n|:--:|---|---|---|---|\n')
        for i,s in enumerate(source['scenes']):
            for j,(suffix,view) in enumerate((('A_GUIDE','Guide'),('B_RECORDING','Chrono'),('C_REVIEW','Relecture'))):
                n=f'{i*3+j+1:02d}'; next_a=f'{i*3+1:02d}'; next_view=f'{i*3+3:02d}'; move='Prochain guide' if i<3 else 'Film d’exemple si les quatre prises sont gardées'
                t=(f"{s['duree_filmer_s']} s proposés à filmer. {' '.join(s['consignes'])}",f'Fin → {next_view}. Annuler → {next_a}, sans garder de prise.',f"{s['question']} Refaire → {next_a}. Garder → {move}.")[j]
                f.write(f"| [{n}](../index.html#ecran-{n}) | {s['titre']} | {s['id']}_{suffix} · {view} | {t} | [Capture](ecrans/{n}.jpg) |\n")
        f.write('\n## Repères du film — exemple, pas durées imposées de tournage\n\n| Prise | Images dans le film (fin exclue, 24 i/s) | Extrait lu |\n|---|---|---|\n')
        for s in source['scenes']:
            a,b=s['extrait_images']; f.write(f"| {s['id']} | {a}–{b} | {a/24:.3f}–{b/24:.3f} s |\n")
        f.write('\nL’identité des acceptations vit seulement dans la page : aucune collecte, capture native, donnée saisie ou création de vidéo personnalisée. Le dernier bouton lit le film étalon.\n')
    rights=f'''# Sources et périmètre — T3

- **Image livrée :** montage d’essai P2-r3 de 30 s. Quatre rushs ont été travaillés ensemble (recadrages, titres, fenêtres, panneaux, changement de vitesse et diptyque). Pour le lecteur, un réencodage léger du même montage est embarqué et lu par fenêtres ; pas de rush stock redistribué seul. `media/{MASTER_NAME}` est l’export muet original, intact.
- **Droits des images :** [Mixkit Stock Video Free License]({MIX_LICENSE}) · [conditions](https://mixkit.co/terms/). Usage dans le montage et démonstration du parcours uniquement ; ne pas traiter les plans comme une banque d’images. Crédit : Mixkit. Aucune image ni bande sonore de la publicité de référence n’est fournie. Les personnes ne sont pas des clientes ni des conseillères du projet.
- **Crédits des prises incorporées :** {', '.join('['+str(n)+']('+u+')' for n,u in zip([52143,52148,52157,52150],SOURCES))}.
- **Référence d’inspiration :** [It’s Glow Time — Hand & Stone / iSpot](https://www.ispot.tv/ad/TakD/hand-and-stone-brightening-facial-enhancement-its-glow-time). Lien documentaire ; aucune copie.
- **Audio :** comparatif privé sous-titré déjà revu, pas de piste de production approuvée dans ce lot. Aucun original musical, prise de voix, mix ou lien privé de remise n’est dans le dossier. Ne pas déduire de la revue une autorisation de redistribution ou d’usage commercial. La mention commerciale/TV de raspberrymusic reste à clarifier avant diffusion de la variante concernée.
- **Données :** la fiche montre des exemples, pas une offre réelle. Pas de coordonnées, aucun élément R04/T1/T2, aucune archive client. Les polices d’interface sont celles du système ; aucun fichier de police de production n’est inclus.

Montage : situer le soin → montrer l’approche → isoler le geste à vitesse réelle → fermer sur le diptyque puis sur le carton. Les cinq effets de l’essai demeurent dans le MP4. L’outil sur la joue est visible aux images 274 à 343, sans promesse de résultat. Le carton « Réserver ce soin » de 24,50 à 30 s ne mène à aucun contact.
'''
    (out/'recherche/Droits-et-perimetre.md').write_text(rights,encoding='utf-8')
    (out/'README.md').write_text('''# Vitrine Vidéo · T3 — Apporter une preuve

**Revue des douze écrans · r1.** Ouvrir [la galerie autonome](index.html), puis un des 12 écrans ou le parcours complet. Exemple de soin du visage ; vocabulaire simple et questions générales applicables à d’autres métiers.

- [12 écrans individuels et navigation](capture/12-ecrans.md) · [Planche des 12](capture/planche-12-ecrans.jpg) · [Questions proposées](formulaire/Fiche-questions-T3.md).
- [Film muet P2-r3](media/T3-Essai-P2-r3-muet.mp4) · [Source et droits](recherche/Droits-et-perimetre.md).
- [Rapport de recette](rapports/Controle-12-ecrans.json) · [Intégration](INTEGRATION.md) · [Manifeste](manifest.json).

Le film et son écriture ont été validés comme essai. Le parcours et les durées de prise restent **à relire**. **Ni caméra réelle, ni nouveau montage calculé à partir des réponses, ni intégration d’application.** Aucun audio privé ou pack de production. T3 est ici un nom éditorial et non un identifiant catalogue affecté.

## Régénérer en local

Avec Python 3.11+, FFmpeg, Playwright + Chromium et Pillow :

```sh
python3 outils/fabriquer.py --master media/T3-Essai-P2-r3-muet.mp4 --sortie ../t3-revue-reconstruite
python3 outils/recette.py ../t3-revue-reconstruite
python3 outils/sceller.py ../t3-revue-reconstruite
(cd ../t3-revue-reconstruite && sha256sum -c SHA256SUMS)
```

La galerie n’utilise ni CDN ni requêtes de média externes. Le nom de dossier n’annonce pas une version de production.
''',encoding='utf-8')
    dump(out/'etat.json',{'revision':'revue-parcours-r1','nom':'T3 — Apporter une preuve','secteur':'Coiffure et beauté','catalog_id':None,'phase_no_cible_revue':6,'statut':'proposition : douze écrans en attente de relecture','accord_essai_P2_r3_prive':True,'accord_P3':None,'accord_P4':None,'musique_production_approuvee':False,'prochaine_action':'Visionner les 12 écrans et faire valider leur navigation et leurs consignes.'})
    (out/'journal-validations.md').write_text('''# Journal de revue T3

| Objet | État | Périmètre |
|---|---|---|
| Film de conception P2-r3 et écriture | Essai approuvé | Composition, cinq effets et texte ; aucun tarif ou contact de production. |
| Comparatif avec sous-titres | Essai privé approuvé | Les médias audio et les liens de partage privés ne sont pas dans le dossier. |
| 12 écrans et navigation | Proposés à la revue | Simulation locale sur le film déjà monté ; pas une preuve d’enregistrement réel. |
| Questions | Proposées à la revue | Une question courte par sujet. Exemples distincts des vraies offres. |
| Production, musique, voix, intégration | Non approuvées dans cette revue | Aucun moteur ni paquet final annoncé. |
''',encoding='utf-8')
    print('Dossier autonome préparé :',out,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--master',type=Path,default=LOCAL if LOCAL.is_file() else T3/'media'/MASTER_NAME); p.add_argument('--ffmpeg',default='ffmpeg'); p.add_argument('--sortie',type=Path,required=True); a=p.parse_args(); main(a.master.resolve(),a.ffmpeg,a.sortie.resolve())
