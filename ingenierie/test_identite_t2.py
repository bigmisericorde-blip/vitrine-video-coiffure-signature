import pytest

from build_manifest_t2 import build, MANIFEST
from core import CASE, HERE, PLAN, ROOT, load, sha, validate


def test_une_identite_et_un_catalogue_separe():
    case,plan=validate(load(CASE),load(PLAN));catalogue=load(HERE/'afrobeat.json')
    assert (plan['template_id'],plan['version'],plan['audio_profile'])==('T2','1.0.0',catalogue['profile_id'])
    assert catalogue['schema']=='vv.coiffure.afrobeat/1.2'
    assert [x['id'] for x in catalogue['pistes']]==['fma-279236','fvv-ghj3du94kp45fclg9a9ofcqb','569473','fma-265362']
    assert '573944' not in (t['id'] for t in catalogue['pistes'])
    assert not {'pistes','selection_finale','ota','download','cloudflare'} & set(plan)
    assert [s['secondes'] for s in case['scenes']]==[6,7,7,7]


@pytest.mark.parametrize('field,bad',[('template_id','T1'),('version','1.2'),('audio_profile','fma-279236.mp4')])
def test_refus_des_champs_invalides(field,bad):
    case,plan=load(CASE),load(PLAN)
    del plan[field]
    with pytest.raises(ValueError):validate(case,plan)
    plan[field]=bad
    with pytest.raises(ValueError):validate(case,plan)


def test_chargeur_json_refuse_un_doublon(tmp_path):
    p=tmp_path/'double.json';p.write_text('{"version":"1.0.0","version":"1.2.0"}')
    with pytest.raises(ValueError,match='double'):load(p)


def test_silencieux_et_calibrations_identiques():
    r=load(HERE/'recette-identite-t2.json')
    m=ROOT/'media'/load(CASE)['sortie']['file']
    assert r['avant']['sha256']==r['apres']['sha256']==sha(m)
    assert r['plans_egaux_hors_metadonnees'] is True
    assert r['avant']['images']==r['apres']['images']==900
    assert r['avant']['audio']==r['apres']['audio']==False
    assert all(sha(ROOT/n)==digest for n,digest in r['media_intacts'].items())


def test_generation_et_manifeste():
    provenance=load(HERE/'provenance-ecrans.json')
    output=ROOT/provenance['output'];source=ROOT/provenance['t2_markup']
    assert output.read_bytes()==source.read_bytes()
    assert sha(output)==provenance['sha256_output']
    assert build()==load(MANIFEST)
