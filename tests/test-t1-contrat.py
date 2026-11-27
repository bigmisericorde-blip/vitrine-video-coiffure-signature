#!/usr/bin/env python3
"""Validation locale du contrat T1 beauté et du plan historique de montage."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator

root = Path(__file__).resolve().parents[1]
read = lambda p: json.loads((root / p).read_text(encoding='utf-8'))
c = read('config/t1-beaute.json')
plan = read(c['renderer']['plan_path'])
Draft202012Validator(read('schemas/t1-beaute.schema.json')).validate(c)
answers = Draft202012Validator(read('schemas/t1-reponses.schema.json'))
answers.validate({'salon':'Salon','service':'Manucure'})
assert not answers.is_valid({'salon':'','service':'Manucure'})
assert not answers.is_valid({'salon':'Salon'})
assert c['renderer']['plan_schema'] == plan['schema']
assert c['renderer']['frames'] == c['renderer']['fps'] * c['renderer']['duration_s'] == 900
assert [s['id'] for s in c['capture']['scenes']] == ['S1','S2','S3','S4']
assert [s['secondes'] for s in c['capture']['scenes']] == [6,7,7,7]
assert len(c['capture']['screens']) == 12
cursor = 0
for i, shot in enumerate(plan['shots']):
    assert shot['in'] == cursor and shot['out'] > cursor
    scene = next(s for s in c['capture']['scenes'] if s['id'] == shot['scene'])
    # sourceFrame dans le moteur utilise floor(src + (frame-in)*speed).
    last_src = int(shot['src'] + (shot['out'] - 1 - shot['in']) * shot['speed'])
    assert last_src < scene['secondes'] * c['renderer']['fps'], shot['id']
    if i:
        assert plan['cuts'][i-1]['at'] == shot['in']
    cursor = shot['out']
assert cursor == c['renderer']['frames'] and len(plan['shots']) == 12 and len(plan['cuts']) == 11
print('OK : schémas, réponses, quatre prises, douze écrans et plan 900 images')
