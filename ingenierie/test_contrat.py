import copy,json
from pathlib import Path
import pytest
from core import load,validate,CASE,PLAN,ROOT,sha
@pytest.fixture
def pair():return load(CASE),load(PLAN)

def test_baseline(pair):
 a,b=validate(*pair); assert [s['secondes'] for s in a['scenes']]==[6,7,7,7] and b['shots'][-1]['out']==900

@pytest.mark.parametrize('mod', ['fifth','missing','scene_duplicate','scene_reorder','duration','add_audio','overwrite_reference','gap','short_cta','unsafe_route','out_of_bounds','wrong_transition','long_field','stock_sha','not_demo'])
def test_reject_bad_cases(pair,mod):
 c,p=pair
 if mod=='fifth':c['scenes'].append(copy.deepcopy(c['scenes'][3])); c['scenes'][4]['n']=5
 if mod=='missing':c['scenes'].pop()
 if mod=='scene_duplicate':c['scenes'][1]['id']='S1'
 if mod=='scene_reorder':c['scenes'][0],c['scenes'][1]=c['scenes'][1],c['scenes'][0]
 if mod=='duration':c['sortie']['frames']=930
 if mod=='add_audio':p['audio']['enabled']=True
 if mod=='overwrite_reference':p['spec_sources']['write_back']=True
 if mod=='gap':p['shots'][1]['in']+=1
 if mod=='short_cta':p['shots'][-2]['out']=870; p['shots'][-1]['in']=870; p['cuts'][-1]['at']=870
 if mod=='unsafe_route':c['display']['route']='https://example.com'
 if mod=='out_of_bounds':p['shots'][4]['src']=209
 if mod=='wrong_transition':p['cuts'][1]['frames']=17
 if mod=='long_field':c['display']['benefice']='a'*90
 if mod=='stock_sha':c['scenes'][0]['stock']['sha256']='pas-de-hash'
 if mod=='not_demo':c['mode']='production'
 with pytest.raises(ValueError):validate(c,p)

def test_master_link(pair):
 c,_=pair; r=load(ROOT/'ingenierie'/'recette-video.json'); a=load(ROOT/'ingenierie'/'recette-parcours.json'); assert a['cas']==r['cas']==c['id'] and a['resultat']==r['resultat']=='PASS'; assert sha(ROOT/'media'/c['sortie']['file'])==r['film']['sha256']
