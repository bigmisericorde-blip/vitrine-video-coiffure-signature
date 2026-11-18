#!/usr/bin/env python3
"""Recette vérifiable : horloge de sortie, intégrité/liaison sources, CTA stable."""
from __future__ import annotations
import argparse,csv,io,re,subprocess
import numpy as np
from core import ROOT,HERE,CASE,PLAN,load,save,validate,require,ffmpeg,sha

def run(*arg):return subprocess.run([ffmpeg(),'-hide_banner','-nostdin',*map(str,arg)],capture_output=True,check=True)
case,plan=validate(load(CASE),load(PLAN));checks=[]
def ok(name,info):checks.append({'controle':name,'ok':True,'preuve':info});print('✓',name,info,flush=True)

def inspect(path,frames):
 meta=subprocess.run([ffmpeg(),'-hide_banner','-i',str(path)],capture_output=True,text=True).stderr
 require('Audio:' not in meta and meta.count(' Video:')==1,'Pistes supplémentaires ou vidéo absente')
 require(re.search(r'Video: h264[^\n]*720x1280[^\n]*30 fps',meta),'Format différent de H.264 720x1280/30')
 r=run('-v','error','-xerror','-i',path,'-map','0:v:0','-f','framemd5','-')
 out=r.stdout.decode();ts=[l.split(',') for l in out.splitlines() if l.strip() and not l.startswith('#')]
 require('#tb 0: 1/30' in out and len(ts)==frames,'Comptage ou base temps incorrects')
 require(all(int(x[1])==i and int(x[2])==i and int(x[3])==1 for i,x in enumerate(ts)),'PTS discontinus')
 return {'images':len(ts),'fps':30,'secondes':len(ts)/30,'audio_streams':0,'sha256':sha(path),'bytes':path.stat().st_size,'images_decodees_uniques':len(set(x[-1] for x in ts))}

m=load(HERE/'manifest-rushs.json');require(m['fixture']==case['id'],'Source test différente')
reports={}
for a,b in zip(case['scenes'],m['prises'],strict=True):
 p=ROOT/'media'/a['media']; require(a['media']==b['fichier'] and sha(p)==b['sha256'] and a['id']==b['id'] and a['stock']['sha256']==b['source']['sha256'],'Mauvais lien fichier/écran/manifest')
 reports[a['id']]=inspect(p,a['secondes']*30)
ok('Quatre prises liées et décodées',{k:v['images'] for k,v in reports.items()})
out=ROOT/'media'/case['sortie']['file'];r=inspect(out,900);ok('Master H.264 / 720 × 1280 / 900 images / sans son',r)
ui=(ROOT/'cas-demo.js').read_text(); provenance=load(HERE/'provenance-ecrans.json')
require(provenance['sha256_output']==sha(ROOT/'simulation.html'),'Provenance de la maquette non vérifiée')
require(case['id'] in ui and case['sortie']['file'] in ui and case['display']['cta'] in ui and case['display']['route'] in ui,'Cas d’écran non compilé')
ok('Contrat T1 préservé et cas commun aux écrans',provenance['base_commit'][:7])

def frame(k):return np.frombuffer(run('-v','error','-ss',f'{k/30:.6f}','-i',out,'-map','0:v:0','-frames:v',1,'-pix_fmt','rgb24','-f','rawvideo','-').stdout,np.uint8).reshape(1280,720,3)
from functools import lru_cache
frame=lru_cache(maxsize=22)(frame)
def mad(a,b):return np.abs(a.astype(np.int16)-b.astype(np.int16)).mean()
def green(a):return float(((a[:,:,1].astype(int)-a[:,:,0]>45) & (a[:,:,1].astype(int)-a[:,:,2]>20)).mean())
irises=[c for c in plan['cuts'] if c['id']=='iris_vert']; ix=[]
for c in irises:
 start=c['at']-c['frames']//2
 ix.append(max(green(frame(k)) for k in range(start,start+c['frames'])))
i1,i2=ix;require(i1>.45 and i2>.45,'Iris non visibles dans le MP4')
scale=plan['cuts'][2]['at']; tool=next(c['at'] for c in plan['cuts'] if c['id']=='match_outil'); ui=next(c for c in plan['cuts'] if c['id']=='ui_push')
s1,s2,s3=mad(frame(scale-1),frame(scale)),mad(frame(tool-1),frame(tool)),mad(frame(ui['at']-1),frame(ui['at']+ui['frames']+5))
require(s1>5 and s2>15 and s3>14,'Rupture insuffisante')
ok('Raccords pixels : 2 iris, changement d’échelle, outil et réservation',{'vert_iris1':round(i1,3),'vert_iris2':round(i2,3),'écart_cut':round(float(s1),2),'écart_outil':round(float(s2),2),'écart_ui':round(float(s3),2)})
lock=plan['shots'][-1]; x,y=lock['in'],lock['out']; steps=[x,x+(y-x)//6,x+(y-x)*2//3,y-1]
cta=[frame(k)[643:1092,40:682] for k in steps];stop=max(mad(cta[0],b) for b in cta[1:]);mov=mad(frame(x)[:600],frame(y-1)[:600]);require(stop<1.5 and mov>4,'Carton instable ou photo figée')
ok(f'CTA fixe {(y-x)/r["fps"]:.2f} s / plan haut vivant',{'drift_carton_px':round(float(stop),3),'écart_vidéo_px':round(float(mov),3)})

def wc(a,b):
 def y(c):
  q=[int(c[i:i+2],16)/255 for i in (1,3,5)];return sum(w*(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4) for w,x in zip((.2126,.7152,.0722),q))
 x,z=sorted([y(a),y(b)]);return (z+.05)/(x+.05)
p=plan['design']['palette'];pairs={'CTA texte/pin':wc(p['white'],p['pine']),'CTA texte secondaire/pin':wc(p['mint'],p['pine']),'Action fond menthe':wc(p['deep'],p['light']),'Prix zone verte (grand corps)':wc(p['white'],p['green'])};require(pairs['CTA texte/pin']>=4.5 and pairs['CTA texte secondaire/pin']>=4.5 and pairs['Action fond menthe']>=4.5 and pairs['Prix zone verte (grand corps)']>=3,'Contraste insuffisant')
ok('Contrastes des surfaces texte', {k:round(v,2) for k,v in pairs.items()})
save(HERE/'recette-video.json',{'cas':case['id'],'resultat':'PASS','plan_sha256':sha(PLAN),'cas_sha256':sha(CASE),'film':r,'prises':reports,'controles':checks})
