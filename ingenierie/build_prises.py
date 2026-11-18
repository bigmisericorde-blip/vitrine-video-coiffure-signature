#!/usr/bin/env python3
"""Télécharge quatre rushs publics, vérifie leurs SHA, produit quatre vraies prises."""
from __future__ import annotations
import argparse, subprocess, urllib.request, os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from core import ROOT, HERE, CASE, PLAN, load, save, sha, validate, ffmpeg, compile_ui
p=argparse.ArgumentParser();p.add_argument('--stock',type=Path,default=Path(os.environ.get('VV_STOCK_CACHE',Path.home()/'.cache'/'vv-coiffure-stock')));p.add_argument('--ui-only',action='store_true');a=p.parse_args()
case,plan=validate(load(CASE),load(PLAN)); compile_ui(case,plan)
if a.ui_only:raise SystemExit(0)
a.stock.mkdir(parents=True,exist_ok=True);(ROOT/'media').mkdir(exist_ok=True)
def one(s):
 r=s['stock']; original=a.stock/f'{r["id"]}.mp4'
 if not original.exists():
  pending=original.with_suffix('.part')
  with urllib.request.urlopen(r['cdn'],timeout=22) as f, pending.open('wb') as o:
   while data:=f.read(1<<20):o.write(data)
  pending.rename(original)
 if sha(original)!=r['sha256']:raise ValueError(f'Empreinte stock incorrecte : {original}')
 # L’original est 16:9. La fenêtre de démo est le cadrage portrait transporté par la fiche T1.
 n=s['secondes']*30; path=ROOT/'media'/s['media']; tmp=path.with_suffix('.tmp.mp4'); left=r['crop_x']//2*2
 subprocess.run([ffmpeg(),'-hide_banner','-v','error','-nostdin','-y','-threads','2','-ss',f'{r["in_s"]:.3f}','-i',str(original),'-map','0:v:0','-an','-filter_threads','1','-vf',f'crop=606:1080:{left}:0,scale=720:1280:flags=lanczos,setsar=1,fps=30','-frames:v',str(n),'-c:v','libx264','-threads','2','-preset','medium','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(tmp)],check=True)
 tmp.replace(path); print(f'{s["id"]}: {s["secondes"]} s ; stock {r["id"]} ; {path.stat().st_size:,} octets',flush=True)
 return {'id':s['id'],'duree':s['secondes'],'sha256':sha(path),'fichier':s['media'],'source':r}
with ThreadPoolExecutor(4) as t: records=list(t.map(one,case['scenes']))
save(HERE/'manifest-rushs.json',{'fixture':case['id'],'licence':'https://www.pexels.com/license/','prises':records})
