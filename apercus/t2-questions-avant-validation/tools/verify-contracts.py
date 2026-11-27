#!/usr/bin/env python3
"""Vérifie les schémas et les exemples sans résoudre de référence réseau."""
from copy import deepcopy
import json
from pathlib import Path
from jsonschema import Draft202012Validator

R=Path(__file__).resolve().parents[1]
load=lambda path:json.loads((R/path).read_text())
fixtures={'template':['config/template.json'],'render-job':['fixtures/contracts/job-3-prises.json','fixtures/contracts/job-4-prises.json'],'render-result':['fixtures/contracts/resultat-exemple.json'],'render-error':['fixtures/contracts/erreur-exemple.json']}
validators={}
for k,paths in fixtures.items():
    schema=load(f'schemas/{k}.schema.json');Draft202012Validator.check_schema(schema);v=Draft202012Validator(schema);validators[k]=v
    for f in paths:v.validate(load(f))
j=load(fixtures['render-job'][0]);bad=deepcopy(j);bad['answers']['contact']='+2290100000000';assert not validators['render-job'].is_valid(bad)
bad=deepcopy(j);bad['slots']=['S1','S2','S3','S4'];assert not validators['render-job'].is_valid(bad)
bad=deepcopy(j);bad['music']['track_id']='fma-0';assert not validators['render-job'].is_valid(bad)
r=load(fixtures['render-result'][0]);r['added_voice_off']=True;validators['render-result'].validate(r)
r['added_voice_off']='oui';assert not validators['render-result'].is_valid(r)
j=load(fixtures['render-job'][0]);j['voice']=True;validators['render-job'].validate(j)
j['voice']=False;assert not validators['render-job'].is_valid(j)
print(json.dumps({'schemas':len(validators),'valid_fixtures':sum(map(len,fixtures.values())),'negative_cases':5},indent=2))

# Schémas de la fiche et des 12 états, ajoutés à la révision T2.
for schema_name, document in [('questions','formulaire/questions.json'),('guide','capture/guide.json')]:
    Draft202012Validator(load('schemas/'+schema_name+'.schema.json')).validate(load(document))
q,g,t,plan=map(load,['formulaire/questions.json','capture/guide.json','config/template.json','ingenierie/plan.json'])
assert [x['id'] for x in q['fields']]==['salon','service','ville','contact','prix']
assert [x['required'] for x in q['fields']]==[True,True,False,False,False]
assert [x['secondes'] for x in g['scenes']]==[6,7,7,7]
assert list(plan['scenes'])==[s['id'] for s in g['scenes']]
assert all(plan['scenes'][s['id']]==s['secondes']*t['media']['fps'] for s in g['scenes'])
assert len(g['screens'])==12 and q['flow_contract']['plan']==t['paths']['plan']
for i,x in enumerate(g['screens']):
    assert x['order']==i+1 and x['slot']==f'S{i//3+1}' and x['state']=='ABC'[i%3]
    assert x['next_screen']==(g['screens'][i+1]['id'] if i<11 else 'COIFFURE-T2.VOICE_CHOICE')
    assert x['retake_screen']==(g['screens'][i-2]['id'] if i%3==2 else None)
print('Questions, scènes, 12 transitions et plan T2 : conformes')
