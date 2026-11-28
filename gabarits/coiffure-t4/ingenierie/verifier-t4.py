#!/usr/bin/env python3
"""Vérifie les contrats et le mappage de tous les exemples d'images ; aucun rendu vidéo."""
import json,re,subprocess,copy
from pathlib import Path
from jsonschema import Draft202012Validator
p=Path(__file__).resolve().parent.parent
read=lambda name:json.loads((p/name).read_text(encoding='utf8'))
for doc,schema in [('contrat.json','contrat.schema.json'),('formulaire/questions.json','formulaire/schema-questions.json'),('capture/guide.json','capture/schema-guide.json'),('ingenierie/contrat-t4.json','ingenierie/schema-contrat-t4.json'),('handoff-t4.json','handoff-t4.schema.json')]:
 s=read(schema);Draft202012Validator.check_schema(s);Draft202012Validator(s).validate(read(doc))
c=read('contrat.json');assert c==read('config.json')['contrat'];g=read('capture/guide.json');q=read('formulaire/questions.json');d=read('ingenierie/contrat-t4.json');h=read('handoff-t4.json')
assert d['champs']==q['questions'];assert d['capture']['scenes']==g['scenes'] and d['capture']['ecrans']==g['screens'];assert c['reprise_locale']==h['recovery']
assert len(q['questions'])==8 and len(g['scenes'])==4 and len(g['screens'])==12
for a,b in zip(g['screens'],h['implementation_handoff']['screens']):assert (b['screen_id'],b['scene_id'],b['state'])==('T4_CAPTURE_'+a['id'],a['scene'],a['etat'])
for field in q['questions']:assert c['fiche'][field['id']]['requis']==field['obligatoire']
assert 'questions.json' in (p/'app.js').read_text() and 'guide.json' in (p/'capture.js').read_text()
# Evaluate the actual JS scene mapping extracted from the engine, and compare each output frame.
w=(p/'render.worker.mjs').read_text();starts=re.search(r'const oldStarts=(\[[^;]+\]),oldLengths=(\[[^;]+\]);',w);assert starts
assert json.loads(starts.group(1))==d['montage']['reference_debuts'];assert json.loads(starts.group(2))==d['montage']['reference_longueurs']
expr=re.search(r'const segments=(ids\.map\(\(id,i\)=>\{[^;]+;return \{[^;]+\}\}\));',w);assert expr, 'expression de séquencement du moteur introuvable'
frame_sets=[[60,60,60,60],[120,240,180,150],[150,330,240,177],[93,126,159,177]]
for frames in frame_sets:
 js='const ids=["S1","S2","S3","S4"],data={frames:'+json.dumps(frames)+'};let total=0;const oldStarts='+starts.group(1)+',oldLengths='+starts.group(2)+';const segments='+expr.group(1)+';console.log(JSON.stringify(segments.map(s=>({a:s.a,b:s.b,oldStart:s.oldStart,oldLength:s.oldLength,rows:Array.from({length:s.b-s.a},(_,i)=>s.refs.map(([id,f])=>[id,f(s.a+i)]))}))))'
 real=json.loads(subprocess.check_output(['node','-e',js],text=True));edge=0
 for i,row in enumerate(real):
  assert row['a']==edge and row['b']==edge+frames[i] and row['oldStart']==d['montage']['reference_debuts'][i] and row['oldLength']==d['montage']['reference_longueurs'][i]
  assert all(v==[[f'S{i+1}',j]] for j,v in enumerate(row['rows']));edge=row['b']
 assert edge==sum(frames)
assert c['voix_client']['facultative']==d['audio']['facultatif'] and c['voix_client']['transcription_automatique'] is False
print('Cinq schémas valides ; fiche, guide, douze états, contrat et 4 configurations de séquencement concordent.')
