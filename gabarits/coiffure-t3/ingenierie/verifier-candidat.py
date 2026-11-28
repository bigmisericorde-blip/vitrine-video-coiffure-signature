from pathlib import Path
import json,jsonschema,subprocess
P=Path(__file__).resolve().parent.parent
load=lambda name:json.loads((P/name).read_text(encoding='utf-8'))
c=load('config.json')['contrat'];assert c==load('contrat.json');q=load('formulaire/questions.json');plan=load('plan-t3-candidat.json');schema=load('ingenierie/schema-plan-variable.json');jsonschema.Draft202012Validator.check_schema(schema);jsonschema.validate(plan,schema)
doc=load('ingenierie/contrat-t3.json');jsonschema.validate(doc,load('ingenierie/schema-contrat-t3.json'));assert load('ingenierie/plan.json')==plan
assert c['template_id']==q['template_id']==plan['template_id']==doc['template_id']=='COIFFURE-T3'
assert [x['id'] for x in q['questions']]==['nom','service','outil','lieu','cible','prix']; assert len({x['id'] for x in q['questions']})==6
for x in q['questions']:
 f=c['fiche'][x['id']];assert isinstance(x['libelle'],str) and x['libelle'] and f['requis']==x['obligatoire'] and isinstance(f['max'],int) and f['max']>0
assert c['media']['fps']==plan['media']['fps']==30 and c['media']['largeur']==plan['media']['largeur']==720 and c['media']['hauteur']==plan['media']['hauteur']==1280
assert c['media']['secondes_max']==30 and c['media']['images_max_avec_audio']==plan['media']['images_max_avec_audio']==899
assert list(c['prises'])==[x['id'] for x in plan['scenes']]==['S1','S2','S3','S4']
for p in c['prises'].values():
 assert p['secondes_min']==2 and p['secondes']>=p['secondes_min'] and p['titre'] and p['guide'] and p['question']
 g=p['capture'];assert g['titre'] and g['consigne'] and all(isinstance(s,str) and s for s in g['a_filmer']+g['a_eviter'])
fields={x['id'] for x in q['questions']};shown={v for s in plan['scenes'] for v in s['reponses_affichees']};assert fields==shown
assert plan['soustitres']['transcription_automatique_integree'] is False and plan['audio']['detection_fin_phrase'] is False
for f in ['app.js','capture.js','verifier-prise.mjs','audio-mix-candidat.mjs','plan-durees-candidat.mjs','render.worker.mjs']:subprocess.run(['node','--check',str(P/f)],check=True)
print('Contrat candidat : questions, champs et obligations, 4 scènes, réponses, guide, durées, limites et syntaxe vérifiés. Transcription automatique absente.')
