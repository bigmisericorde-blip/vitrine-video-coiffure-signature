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
