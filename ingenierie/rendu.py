#!/usr/bin/env python3
"""Rendu original 9:16, piloté à l'image. 4 vidéos sources ; aucune piste audio."""
from __future__ import annotations
from functools import lru_cache
import argparse, os, math, subprocess
from pathlib import Path
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont,ImageColor
from core import ROOT, CASE, PLAN, ffmpeg, load, validate, sha, save
cv2.setNumThreads(1)
W,H,FPS=720,1280,30
S=(W,H)
C,P=validate(load(CASE),load(PLAN));D=C['display'];M=C['copy']; PA=P['design']['palette'];AS=ROOT/'assets'
INK,DEEP,PINE,GREEN,NEON,MINT,WHITE=tuple(PA[k] for k in ('deep','dark','pine','green','light','mint','white'))
PRICE=f'{D["prix"]:,}'.replace(',','\u202f')
TITLEFONT=P['design']['fonts']['title']; NUMFONT=P['design']['fonts']['data']
SHOTS=P['shots'];CUTS=P['cuts'];START=[p['in'] for p in SHOTS]
BY_STAGE={p['stage']:p for p in SHOTS}
AT={x['at']:x for x in CUTS}; DESIGN=P['design']; FX=DESIGN['motion']
B0,B1=(BY_STAGE[DESIGN[k]]['in'] for k in ('badge_from_stage','badge_to_stage'))

def clamp(t): return min(1.,max(0.,float(t)))
def smooth(t):t=clamp(t);return t*t*(3-2*t)
def ease(t):return 1-(1-clamp(t))**3

def lerp(a,b,t):return a+(b-a)*t

def tuplec(c):return ImageColor.getrgb(c) if isinstance(c,str) else c

@lru_cache(maxsize=200)
def font(px=24, w=650, mono=False):
 f=ImageFont.truetype(str(AS/(NUMFONT if mono else TITLEFONT)),round(px));
 if not mono:f.set_variation_by_axes([w])
 return f

def text(d,x,y,s,n=28,color=WHITE,weight=650,mono=False,track=0,maxa=None,align='left'):
 f=font(n,weight,mono)
 if maxa:
  while n>16 and f.getlength(s)+max(0,len(s)-1)*track>maxa:
   n-=1;f=font(n,weight,mono)
 if align=='right':x-=f.getlength(s)+max(0,len(s)-1)*track
 if align=='center':x-=(f.getlength(s)+max(0,len(s)-1)*track)*.5
 if track:
  for q in s:
   d.text((round(x),round(y)),q,font=f,fill=color,anchor='lt'); x+=f.getlength(q)+track
 else:d.text((round(x),round(y)),s,font=f,fill=color,anchor='lt')
 return n

def patch(canvas,obj,xy):
 # PIL crops automatically at the canvas boundary.
 canvas.paste(obj,tuple(map(int,xy)),obj if obj.mode=='RGBA' else None)

def rr(d,box,r,fill,ol=None,width=1): d.rounded_rectangle(tuple(int(x) for x in box),r,fill=fill,outline=ol,width=width)

def arrow(d,x,y,l=18,c=INK,sz=3):
 d.line((x-l,y,x+l,y),fill=c,width=sz); d.line((x+l-9,y-8,x+l,y,x+l-9,y+8),fill=c,width=sz,joint='curve')

def vmark(d,x,y,s=1,c=WHITE):
 d.line([(int(x+4*s),int(y+10*s)),(int(x+14*s),int(y+33*s)),(int(x+29*s),int(y+4*s))],fill=c,width=max(3,int(5*s)),joint='curve');
 d.ellipse((int(x+29*s),int(y+2*s),int(x+34*s),int(y+7*s)),fill=NEON)

def background(w,h,style='studio'):
 y,x=np.mgrid[0:h,0:w].astype(np.float32); x/=w;y/=h; a=np.array(tuplec(INK),dtype=np.float32);b=np.array(tuplec(PINE),dtype=np.float32);c=np.array(tuplec(GREEN),dtype=np.float32)
 ell=np.exp(-(((x-.88)*1.35)**2+((y-.26)*2.2)**2)*2.2)*.77; k=np.clip(.10+ell,0,1)[:,:,None]
 z=a[None,None,:]*(1-k)+b[None,None,:]*k; light=((1-.85*x)*np.exp(-((y-1.0)*4)**2)*.28)[:,:,None];z=z*(1-light)+c*light
 if style=='studio':
  # Fine engraved strips, quiet behind the card. Deterministic texture.
  z+=((np.abs((x*w+y*h*.55)%58-1)<.95)*2.4+np.random.default_rng(20).normal(0,.64,(h,w)))[:,:,None]
 return Image.fromarray(np.clip(z,0,255).astype(np.uint8),'RGB')

STUDIO=background(W,H)

def scrim(bottom=.76,top=.32,shade=INK,bs=.43,ts=.22):
 y=np.arange(H,dtype=np.float32)/H;v=(bottom*np.clip((y-bs)/(1-bs),0,1)**1.45 + top*np.clip((ts-y)/ts,0,1)**1.22)*255
 p=Image.new('RGBA',S,tuplec(shade)+(255,));p.putalpha(Image.fromarray(np.tile(np.minimum(v,255).astype(np.uint8)[:,None],(1,W))));return p
SCRIM=scrim(.95,.61,bs=.36); TOP=scrim(1.15,.69,bs=.28,ts=.27); END=scrim(.93,.69,bs=.2)

@lru_cache(maxsize=16)
def grademap(scene):
 # Slightly cyan shadows and restrained saturation without recoloring hair or skin.
 x=np.arange(256,dtype=np.float32);sh=(1-x/255)**1.75
 b=np.clip(x*.995+sh*9,0,255); g=np.clip(x*.991+sh*7,0,255); r=np.clip(x*.994+sh*2,0,255)
 return np.stack((b,g,r),1).astype(np.uint8).reshape(256,1,3)

class Source:
 def __init__(self,s):
  self.src=cv2.VideoCapture(str(ROOT/'media'/s['media']));self.pos=-1;self.bgr=None
  if not self.src.isOpened():raise RuntimeError(s['media'])
  if int(self.src.get(cv2.CAP_PROP_FRAME_COUNT))!=s['secondes']*FPS:raise RuntimeError(f'{s["id"]} : longueur hors contrat')
 def get(self,k):
  if k==self.pos and self.bgr is not None:return self.bgr
  if k!=self.pos+1:self.src.set(cv2.CAP_PROP_POS_FRAMES,k)
  ok,im=self.src.read()
  if not ok:raise RuntimeError(f'Lecture impossible image {k}')
  self.pos=k;self.bgr=im;return im

SRC={s['id']:Source(s) for s in C['scenes']}

def rush(shot,f):
 i=max(0,min(shot['out']-shot['in']-1,f-shot['in']));p=smooth(i/max(1,shot['out']-shot['in']-1));k=shot['src']+int(i*shot['speed']); fr=SRC[shot['scene']].get(k)
 z=lerp(*shot['zoom'],p);cx,cy=shot['anchor'];cw,ch=round(W/z),round(H/z)
 # anchor describes a position in the available overscan, not an additive translation.
 x=round((W-cw)*cx);y=round((H-ch)*cy);fr=fr[y:y+ch,x:x+cw]
 if (cw,ch)!=S:fr=cv2.resize(fr,S,interpolation=cv2.INTER_LINEAR)
 return Image.fromarray(cv2.cvtColor(cv2.LUT(fr,grademap(shot['scene'])),cv2.COLOR_BGR2RGB),'RGB')

@lru_cache(maxsize=180)
def rounded_mask(w,h,r):
 im=Image.new('L',(w,h));rr(ImageDraw.Draw(im),(0,0,w-1,h-1),r,255);return im

def cover(img,w,h,focus=(.5,.45)):
 a,b=img.size; v=w/h
 if a/b>v:
  nw=b*v;x=min(a-nw,max(0,focus[0]*a-nw/2));box=(x,0,x+nw,b)
 else:
  nh=a/v;y=min(b-nh,max(0,focus[1]*b-nh/2));box=(0,y,a,y+nh)
 return img.resize((w,h),Image.Resampling.BILINEAR,box=box)

def vwin(dst,img,rect,r=25,focus=(.5,.38),border=True):
 x,y,w,h=map(int,rect);a=cover(img,w,h,focus);dst.paste(a,(x,y),rounded_mask(w,h,r) if r else None)
 if border:rr(ImageDraw.Draw(dst),(x,y,x+w-1,y+h-1),r,None,tuplec(MINT),1)

@lru_cache(maxsize=1)
def heads():
 im=Image.new('RGBA',S);d=ImageDraw.Draw(im)
 rr(d,(44,96,103,155),13,tuplec(INK)+(240,),tuplec(NEON)+(200,),2);vmark(d,55,106,1.17)
 text(d,117,99,D['salon'],30,WHITE,800,maxa=280)
 text(d,118,136,'DÉMONSTRATION',17,MINT,mono=True,track=2)
 return im

@lru_cache(maxsize=1)
def badge():
 im=Image.new('RGBA',(228,105)); d=ImageDraw.Draw(im)
 d.polygon([(0,11),(11,0),(227,0),(227,87),(210,104),(0,104)],fill=tuplec(PINE)+(250,),outline=NEON,width=2)
 d.line((1,23,1,81),fill=NEON,width=4);text(d,15,14,D['service'].upper(),17,MINT,mono=True,track=.6,maxa=193)
 a=text(d,15,43,PRICE,45,WHITE,800,maxa=142);fw=font(a,800).getlength(PRICE)
 text(d,15+fw+11,62,D['devise'],18,WHITE,mono=True,maxa=max(22,195-fw-11));return im

def header(im,f,small=True):
 patch(im,heads(),(0,0));
 if small and B0<=f<B1:patch(im,badge(),(448,96))

@lru_cache(maxsize=1)
def ticket():
 w,h=632,305; im=Image.new('RGBA',(w,h));mask=Image.new('L',(w,h));poly=[(0,17),(17,0),(w-30,0),(w-1,28),(w-1,h-36),(w-35,h-1),(0,h-1)]
 ImageDraw.Draw(mask).polygon(poly,fill=255)
 y,x=np.mgrid[0:h,0:w];p=(.17+.77*x/w)[:,:,None];lo=np.array(tuplec(PINE));hi=np.array(tuplec(GREEN));g=np.clip(lo[None,None,:]*(1-p)+hi[None,None,:]*p,0,255).astype(np.uint8);a=Image.fromarray(g,'RGB');im.paste(a,(0,0),mask);d=ImageDraw.Draw(im);d.line(poly+poly[:1],fill=NEON,width=2)
 text(d,25,24,D['service'],43,WHITE,800,maxa=440)
 rr(d,(469,21,610,56),11,INK);text(d,539.5,30,'TARIF DÉMO',17,MINT,mono=True,align='center',track=.8)
 n=text(d,22,81,PRICE,115,WHITE,800,maxa=442);a=font(n,800).getlength(PRICE)
 text(d,34+a,138,D['devise'],38,WHITE,790,maxa=560-a)
 for k in range(24,w-25,13):d.line((k,219,k+6,219),fill=tuplec(MINT)+(128,),width=1)
 text(d,26,244,D['benefice'],32,WHITE,750,maxa=570)
 return im

def bottom_label(im,k,head,sub=None,accent=NEON):
 d=ImageDraw.Draw(im);d.rectangle((44,928,51,1004 if sub else 980),fill=accent)
 text(d,68,921,k.upper(),19,MINT,mono=True,track=2,maxa=600)
 text(d,67,953,head,53,WHITE,800,maxa=590)
 if sub:text(d,68,1026,sub,28,WHITE,625,maxa=590)

def first(img,f,shot):
 if shot['stage']=='hook':
  im=img.copy();patch(im,SCRIM,(0,0));header(im,f,False);d=ImageDraw.Draw(im);e=ease((f-shot['in'])/FX['hook_ease'])
  rr(d,(44,822,144,858),13,PINE);text(d,94,832,'L’OFFRE',19,MINT,mono=True,align='center',track=.8)
  text(d,42,878+16*(1-e),D['service'],78,WHITE,800,maxa=633)
  text(d,47,989+10*(1-e),D['benefice'],37,WHITE,685,maxa=619)
  d.line((47,1060,221,1060),fill=NEON,width=3)
  text(d,47,1082,D['ville'].upper()+'  /  FILM DÉMO',17,MINT,mono=True,track=1.3,maxa=630)
  return im
 # Offer split: resize the portrait photograph; the price tile enters from the right.
 start=shot['in']; a=smooth((f-start+1)/AT[start]['frames']); w=round(lerp(720,632,a));h=round(lerp(1280,580,a)); x=44*a;y=186*a
 im=STUDIO.copy();vwin(im,img,(x,y,w,h),round(26*a),(0.49,lerp(.48,.32,a)),a>.8)
 if a<.70:patch(im,SCRIM,(0,0))
 header(im,f,False);d=ImageDraw.Draw(im)
 if a>.75:
  rr(d,(61,699,205,742),13,INK,None);text(d,133,711,M['marque_entree'].upper(),17,MINT,mono=True,align='center',track=.5,maxa=126)
 patch(im,ticket(),(lerp(739,44,a),758+round(60*(1-a))))
 if a>.91:text(d,45,1086,'STUDIO DÉMO  /  '+D['ville'].upper(),17,MINT,mono=True,track=1.3,maxa=630)
 return im

@lru_cache(maxsize=1)
def phone_base():
 im=Image.new('RGBA',(303,562));d=ImageDraw.Draw(im)
 rr(d,(4,4,300,558),37,(0,18,19,163));rr(d,(2,0,296,550),36,INK,NEON,2)
 rr(d,(12,10,286,540),28,'#EAF7EF');rr(d,(107,18,191,36),9,INK);text(d,33,54,D['salon'],20,INK,800,maxa=232)
 text(d,33,90,D['service'],24,INK,800,maxa=232);text(d,33,128,PRICE+' '+D['devise'],18,PINE,mono=True,maxa=240)
 d.line((32,164,264,164),fill='#AACDBE',width=1);text(d,33,187,'Choisir un créneau',22,INK,760,maxa=235)
 text(d,33,228,'HORAIRES FICTIFS',15,PINE,mono=True,track=.65)
 return im

def phone(p):
 im=phone_base().copy();d=ImageDraw.Draw(im)
 for i,h in enumerate(['10:00','11:30','16:00']):
  y=267+i*65;select=i==1 and p>FX['booking_select_at']
  rr(d,(30,y,266,y+49),13,PINE if select else '#F7FFF8',None if select else '#98C6B3',1)
  text(d,48,y+14,h,22,WHITE if select else INK,mono=True)
  rr(d,(226,y+10,252,y+37),13,MINT if select else '#D1EDE0');
  if select:d.line((233,y+23,238,y+27,246,y+18),fill=INK,width=2)
 rr(d,(32,474,264,515),13,INK);text(d,148,486,'APERÇU DÉMO',15,MINT,mono=True,align='center',track=.8)
 return im

def booking(img,f,shot):
 start=shot['in']; v=smooth((f-start+1)/AT[start]['frames']);p=clamp((f-start)/(shot['out']-start));im=STUDIO.copy();d=ImageDraw.Draw(im); header(im,f)
 text(d,45,249,M['action_prochaine'].upper(),17,MINT,mono=True,track=1.5,maxa=608)
 text(d,44,287,M['action_preuve'],55,WHITE,800,maxa=632)
 vwin(im,img,(44,385,410,600),28,(.53,.42))
 d=ImageDraw.Draw(im);rr(d,(59,916,234,962),13,INK);text(d,146,929,D['ville'].upper(),17,MINT,mono=True,align='center',track=1.2,maxa=158)
 ph=phone(p); angle=-2.25*(1-v);ph=ph.rotate(angle,Image.Resampling.BICUBIC,expand=True) if abs(angle)>.09 else ph
 patch(im,ph,(lerp(725,365,v),440+50*(1-v)))
 d=ImageDraw.Draw(im);text(d,45,1045,'Un créneau pour la prestation affichée.',24,WHITE,620,maxa=632)
 return im

@lru_cache(maxsize=2)
def ctapat(big):
 w=632;h=177 if big else 126;im=Image.new('RGBA',(w,h)); d=ImageDraw.Draw(im)
 rr(d,(0,0,w-1,h-1),23,PINE,NEON,2)
 if big:
  text(d,24,22,D['cta'],43,WHITE,800,maxa=536);text(d,24,85,D['indication'],27,MINT,650,maxa=530)
  d.line((24,136,605,136),fill=GREEN,width=1);text(d,24,149,D['contact'].upper(),15,MINT,mono=True,track=1.05,maxa=562)
 else:
  text(d,24,23,D['cta'],42,WHITE,800,maxa=525);text(d,24,82,D['indication'],24,MINT,670,maxa=525)
 rr(d,(560,22,607,69),15,NEON);arrow(d,583,45,12)
 return im

def action(img,f):
 im=img.copy(); patch(im,TOP,(0,0)); header(im,f);d=ImageDraw.Draw(im)
 text(d,45,914,'À '+D['ville'],44,WHITE,790,maxa=630)
 patch(im,ctapat(False),(44,978));return im

@lru_cache(maxsize=1)
def end_pad():
 im=background(W,670,'end'); d=ImageDraw.Draw(im);d.rectangle((0,0,719,6),fill=NEON)
 vmark(d,48,50,1.05);text(d,96,48,D['salon'],38,WHITE,800,maxa=565)
 text(d,47,104,D['ville']+' · '+D['pays'],25,MINT,660,maxa=625)
 text(d,47,168,D['service']+'   /   '+PRICE+' '+D['devise'],28,WHITE,730,maxa=626)
 patch(im,ctapat(True),(44,225));d=ImageDraw.Draw(im)
 text(d,45,441,D['condition'].upper(),18,MINT,mono=True,track=1.05,maxa=626)
 return im

def lockup(img,f):
 im=Image.new('RGB',S,INK);vwin(im,img,(0,0,720,650),0,(.51,.38),False);patch(im,END,(0,0));d=ImageDraw.Draw(im);rr(d,(44,96,200,134),12,INK);text(d,122,106,'FILM DÉMO',17,MINT,mono=True,track=1,align='center');patch(im,end_pad(),(0,627));return im

def single(shot,f):
 img=rush(shot,f); st=shot['stage']
 if st in ('hook','offer'):return first(img,f,shot)
 if st=='booking':return booking(img,f,shot)
 if st=='action':return action(img,f)
 if st=='lockup':return lockup(img,f)
 im=img.copy();patch(im,TOP,(0,0));header(im,f)
 if st.startswith('cut'):bottom_label(im,'Le geste',M['methode_detail'])
 elif st.startswith('detail'):bottom_label(im,M['detail'],M['detail_texte'])
 elif st.startswith('result'):bottom_label(im,'Le résultat',M['resultat'],M['resultat_texte'])
 return im

# Two controlled, short branded apertures. The frame before and after always belongs to the normal timeline.
Y,X=np.ogrid[:H,:W]
IX,IY=FX['iris_center']
DIST=np.sqrt(((X-IX)/1.0)**2+((Y-IY)/1.0)**2)
FAR=float(DIST.max())+3
G=tuplec(GREEN); E=tuplec(INK); L=tuplec(NEON)

def iris(a,b,p):
 if p<.52:
  z=smooth(p/.52);r=max(0,z*(FAR+26)); im=a.copy();d=ImageDraw.Draw(im)
  vals=[(r+21*z,E),(r,G),(max(0,r-2),G)]
  for rg,col in vals:d.ellipse((IX-rg,IY-rg,IX+rg,IY+rg),fill=col)
  # The perimeter echoes the rim of the offer badge, without a copied brand asset.
  if 6<r<FAR:d.ellipse((IX-r,IY-r,IX+r,IY+r),outline=L,width=2)
  return im
 q=smooth((p-.52)/.48); r=q*(FAR+2);mask=Image.fromarray(np.clip((r-DIST+1.7)/3.4,0,1).__mul__(255).astype(np.uint8))
 im=Image.new('RGB',S,G);im.paste(b,(0,0),mask);return im

def compose(f):
 idx=max(j for j,v in enumerate(START) if v<=f)
 for i,cut in enumerate(CUTS):
  if cut['id']!='iris_vert':continue
  n=cut['frames']; c=cut['at']; a0=c-n//2
  if a0<=f<a0+n:
   return iris(single(SHOTS[i],min(c-1,f)),single(SHOTS[i+1],max(c,f)),(f-a0+1)/(n+1))
 img=single(SHOTS[idx],f)
 # The mock-up grows across its own cut instead of adding a fifth footage source.
 cut=AT.get(SHOTS[idx]['in'])
 if cut and cut['id']=='ui_push' and f<cut['at']+cut['frames']:
  p=smooth((f-cut['at']+1)/cut['frames']);prev=single(SHOTS[idx-1],cut['at']-1)
  x=int(W*p); mask=Image.new('L',S);d=ImageDraw.Draw(mask);d.polygon([(W-x+40,0),(W,0),(W,H),(W-x-40,H)],fill=255)
  prev.paste(img,(0,0),mask);d=ImageDraw.Draw(prev)
  if .06<p<.94:d.line((W-x+40,0,W-x-40,H),fill=NEON,width=3)
  return Image.blend(img,prev,max(0,1-p)) if p>.91 else prev
 return img

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT/'media'/C['sortie']['file']);ap.add_argument('--frames',nargs='+',type=int);ap.add_argument('--frame-dir',type=Path,default=ROOT/'livrables'/'photogrammes');a=ap.parse_args()
 if a.frames:
  a.frame_dir.mkdir(parents=True,exist_ok=True)
  for f in a.frames:compose(f).save(a.frame_dir/f'{f:03d}.jpg',quality=93)
  return
 out=a.output;tmp=out.with_suffix('.tmp.mp4');out.parent.mkdir(exist_ok=True,parents=True)
 cmd=[ffmpeg(),'-hide_banner','-loglevel','error','-nostdin','-y','-f','rawvideo','-pix_fmt','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-map','0:v:0','-an','-c:v','libx264','-threads','3','-preset','medium','-crf','17','-vf','scale=out_color_matrix=bt709:out_range=tv,setsar=1','-pix_fmt','yuv420p','-colorspace','bt709','-color_trc','bt709','-color_primaries','bt709','-movflags','+faststart','-metadata','title=Vitrine Vidéo — Le passage vert (test muet)',str(tmp)]
 with subprocess.Popen(cmd,stdin=subprocess.PIPE) as p:
  for f in range(C['sortie']['frames']):
   p.stdin.write(compose(f).tobytes())
   if f%150==0:print(f'{f:03d}/900',flush=True)
  p.stdin.close()
  if p.wait()!=0:raise RuntimeError('Encodeur en échec')
 tmp.replace(out)
 print(out.name,sha(out),out.stat().st_size,flush=True)
if __name__=='__main__': main()
