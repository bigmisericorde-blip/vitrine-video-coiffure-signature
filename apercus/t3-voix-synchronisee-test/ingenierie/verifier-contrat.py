#!/usr/bin/env python3
"""Vérifie la cohérence du contrat descriptif T3 avec le code local ; ne rend pas la vidéo."""
from pathlib import Path
import json, math, re, subprocess
import jsonschema
P=Path(__file__).resolve().parent.parent
read=lambda p:json.loads((P/p).read_text(encoding='utf8'))
d=read('ingenierie/contrat-t3.json'); schema=read('ingenierie/schema-contrat-t3.json'); jsonschema.Draft202012Validator.check_schema(schema);jsonschema.validate(d,schema)
c=read('config.json')['contrat'];assert c==read('contrat.json'),'config et contrat diffèrent'
qs=read('formulaire/questions.json')['questions'];fields=d['champs'];assert [f['id'] for f in fields]==[f['id'] for f in qs]
for f,q in zip(fields,qs):
 k=f['id'];assert f['libelle']==q['libelle'] and f['obligatoire']==q['obligatoire']==c['fiche'][k]['requis'];assert f['maximum_caracteres']==c['fiche'][k]['max'] and f['usage']==c['fiche'][k]['usage']
assert d['capture']['nombre_scenes']==4 and d['capture']['nombre_etats_stables']==12
for s in d['capture']['scenes']:
 x=c['prises'][s['id']];assert (s['titre'],s['minimum_s'],s['guide'],s['question_relecture'])==(x['titre'],x['secondes'],x['guide'],x['question']);assert len(s['etats'])==3
w=(P/'render.worker.mjs').read_text();assert not re.search(r'\b(?:fillText|strokeText)\s*\(',w),'texte dessiné par le moteur'
assert 'captation_audio_des_prises_utilisee' in c['voix_client'] and c['voix_client']['captation_audio_des_prises_utilisee']==d['audio']['prise_en_compte_du_son_des_scenes']==True
# Exécute uniquement la déclaration des segments extraits du moteur existant,
# afin de comparer toutes les images à la formule documentée.
definition=re.search(r'const segments=(\[[\s\S]*?\]);',w).group(1)
js="const clamp=x=>Math.max(0,Math.min(1,x));const segments="+definition+";console.log(JSON.stringify(segments.map(s=>({a:s.a,b:s.b,frames:Array.from({length:s.b-s.a},(_,i)=>s.refs.map(([id,fn])=>[id,fn(s.a+i)]))}))));"
real=json.loads(subprocess.check_output(['node','-e',js],text=True));doc=d['montage']['segments'];assert len(real)==len(doc)==d['montage']['nombre_segments'];edge=0
for actual,seg in zip(real,doc):
 a,b=seg['debut'],seg['fin_exclue'];assert a==edge and (a,b)==(actual['a'],actual['b']) and b>a
 for index,rows in enumerate(actual['frames']):
  frame=a+index;want=[]
  for ref in seg['sources']:
   value=ref['offset_images']+(frame-a)*ref['progression_images_par_image'];r=ref.get('supplement_arrondi')
   if r:
    t=min(1,max(0,(frame-r['de_image_sortie'])/r['duree_images']));value+=math.floor(r['maximum']*t**r['puissance']+.5)
   assert 0<=value<c['prises'][ref['source']]['secondes']*30,(frame,ref,value)
   want.append([ref['source'],value])
  assert want==rows,(frame,want,rows)
 edge=b
assert edge==d['sortie']['images']==900
# Vérifier indépendamment les 900 images de la variante synchronisée.
voice_def=re.search(r'const segmentsVoix=(\[[\s\S]*?\]);',w).group(1)
js2="const segments="+voice_def+";console.log(JSON.stringify(segments.map(s=>({a:s.a,b:s.b,frames:Array.from({length:s.b-s.a},(_,i)=>s.refs.map(([id,fn])=>[id,fn(s.a+i)]))}))));"
real_voice=json.loads(subprocess.check_output(['node','-e',js2],text=True));doc_voice=d['montage']['variante_voix_prises']['segments'];assert len(real_voice)==len(doc_voice)==4;edge=0
for actual,seg in zip(real_voice,doc_voice):
 a,b=seg['debut'],seg['fin_exclue'];assert a==edge and (a,b)==(actual['a'],actual['b']);assert seg['source_debut']==0 and seg['source_fin_exclue']==b-a and seg['vitesse']==1
 for j,rows in enumerate(actual['frames']):assert rows==[[seg['source'],j]],(a+j,rows)
 edge=b
assert edge==900 and [s['fin_exclue']-s['debut'] for s in doc_voice]==[180,240,240,240]
assert c['voix_client']['son_des_prises']['duree_conservee_par_scene_s']==d['audio']['mode_voix_des_prises']['duree_conservee_par_scene_s']==[6,8,8,8]
assert d['sortie']['fps']==c['media']['fps']==30 and d['sortie']['largeur_px']==c['media']['largeur']==720 and d['sortie']['hauteur_px']==c['media']['hauteur']==1280
print('Schéma valide ; fiche, 4 scènes, 12 états et les 900 images de chaque variante vérifiés ; texte moteur absent.')
