"""Rotation et mixage validés sur des signaux déterministes, jamais intégrés aux fonds."""
from concurrent.futures import ThreadPoolExecutor
import threading
import time

import numpy as np
import pytest

from mix_voix import SR, MediaError, activity, decode, envelope, mix_to_wav, wav
from postproduction import catalogue, finalize
from rotation import next_track


def test_quatre_fonds_valides():
    tracks, _, _ = catalogue()
    assert [t['id'] for t in tracks] == ['fma-279236','fma-279237','fma-279239','fma-265362']
    assert all(t['media'].is_file() for t in tracks)


def test_rotation_tour_et_absence_de_repetition(tmp_path):
    songs=[{'id':str(n)} for n in range(4)]
    state=tmp_path/'test.sqlite'
    seen=[]
    for _ in range(12):
        with next_track(songs,'1',state,choose=lambda x:x[0]) as s: seen.append(s['id'])
    assert all(a!=b for a,b in zip(seen,seen[1:]))
    assert all(len(set(seen[j:j+4]))==4 for j in (0,4,8))
    with pytest.raises(RuntimeError), next_track(songs,'2',state,choose=lambda x:x[0]):
        raise RuntimeError('échec de montage')
    with next_track(songs,'2',state,choose=lambda x:x[0]) as s: assert s['id']=='0'


def test_rotation_concurrente(tmp_path):
    songs=[{'id':str(n)} for n in range(4)]
    events=[];gate=threading.Barrier(3)
    def work():
        gate.wait()
        with next_track(songs,'1',tmp_path/'parallel.sqlite',choose=lambda x:x[0]) as t:
            events.append(t['id']);time.sleep(.025)
    with ThreadPoolExecutor(3) as pool: list(pool.map(lambda _:work(),range(3)))
    assert len(set(events))==3


def make_tones(tmp_path):
    n=SR*9; t=np.arange(n,dtype=np.float32)/SR
    bed=np.sin(2*np.pi*120*t)*.15
    voice=np.sin(2*np.pi*1370*t)*.13
    voice[(t<1)|(t>=2.3)&(t<3.5)|(t>=4.9)]=0
    b,v=tmp_path/'bed.wav',tmp_path/'voice.wav'
    wav(b,np.repeat(bed[:,None],2,axis=1)); wav(v,voice[:,None]);return b,v,voice


def test_ducking_et_debit(tmp_path):
    b,v,dry=make_tones(tmp_path); target=tmp_path/'mix.wav'
    r=mix_to_wav(b,v,9,target,fixed=True)
    assert r['debit_modifie'] is False and r['position_s']==0 and len(r['fenetres_voix_s'])==2
    real=decode(target,'wav',channels=1,limit=9)[:,0];assert len(real)==9*SR
    def amplitude(start,sz=.4,freq=120):
        x=real[round(start*SR):round((start+sz)*SR)];return 2*abs(x@np.exp(-2j*np.pi*freq*np.arange(len(x))/SR))/len(x)
    db=lambda a,b:20*np.log10(a/b)
    assert -13.2<db(amplitude(1.6),amplitude(.15))<-12.7
    assert -13.2<db(amplitude(4.1),amplitude(5.5))<-12.7
    assert abs(db(amplitude(2.84),amplitude(.15)))<.2
    assert amplitude(1.6,freq=1370)>.07
    assert r['fenetres_voix_s'][0][0]==pytest.approx(.95,abs=.015)
    assert r['fenetres_voix_s'][1][0]==pytest.approx(3.45,abs=.015)


def test_pas_de_coupure_ou_acceleration(tmp_path):
    b,v,_=make_tones(tmp_path)
    with pytest.raises(MediaError,match='n’accélère pas'):
        mix_to_wav(b,v,3,tmp_path/'trop-court.wav')
    with pytest.raises(MediaError,match='Aucune voix audible'):
        s=tmp_path/'silence.wav';wav(s,np.zeros((SR*2,1),dtype=np.float32)); mix_to_wav(b,s,9,tmp_path/'silence-mix.wav')
