#!/usr/bin/env python3
"""Sous-titres manuels de test en DM Sans 600. Les temps visent la vidéo finale, pas la voix brute.
Pas de reconnaissance vocale ni de preuve que le texte correspond à l'enregistrement.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import os,re,subprocess
from PIL import Image,ImageDraw,ImageFont
from son_t4 import image_ok,sha
D=Path(__file__).resolve().parent
class SousTitresInvalides(ValueError):pass

def valider(cues):
 if not isinstance(cues,list) or len(cues)>12:raise SousTitresInvalides('Douze sous-titres maximum.')
 last=0;out=[]
 for cue in cues:
  if not isinstance(cue,dict) or set(cue)!={'debut','fin','texte'}:raise SousTitresInvalides('Sous-titre incomplet.')
  a,b,s=cue['debut'],cue['fin'],cue['texte']
  if type(a) not in (int,float) or type(b) not in (int,float) or not 0<=a<b<=30 or a<last or b-a<.5:raise SousTitresInvalides('Vérifie les temps : 0 à 30 s, sans chevauchement et au moins 0,5 s.')
  if a<24.23<b:raise SousTitresInvalides('Sépare le sous-titre au passage de la dernière scène, à 24,23 s.')
  if not isinstance(s,str) or not s.strip() or len(s)>90 or re.search(r'[<>\x00-\x1f]',s):raise SousTitresInvalides('Sous-titre vide ou trop long.')
  out.append({'debut':round(a,3),'fin':round(b,3),'texte':s.strip()});last=b
 return out

def image_texte(cue,dest):
 im=Image.new('RGBA',(720,1280));d=ImageDraw.Draw(im);f=ImageFont.truetype(str(D/'polices/DMSans.ttf'),38);f.set_variation_by_axes([14,600]);lines=[];line=''
 for word in cue['texte'].split():
  nxt=(line+' '+word).strip()
  if d.textlength(nxt,font=f)>572 and line:lines.append(line);line=word
  else:line=nxt
 if line:lines.append(line)
 if len(lines)>2 or any(d.textlength(x,font=f)>572 for x in lines):raise SousTitresInvalides('Sous-titre trop large : raccourcis-le ou sépare-le en deux.')
 # Pendant la signature finale, on remonte au centre pour éviter le carton de coordonnées.
 endscene=cue['debut']>=24.23;bottom=880 if endscene else 1112;h=32+47*len(lines);top=bottom-h
 w=int(max(d.textlength(x,font=f) for x in lines)+32);d.rounded_rectangle(((720-w)//2,top,(720+w)//2,bottom),radius=16,fill=(31,20,28,217))
 y=top+13
 for line in lines:d.text((360,y),line,font=f,anchor='mt',fill=(255,247,238,255));y+=47
 im.save(dest)

def appliquer(master,cues,out):
 cues=valider(cues);master=Path(master);out=Path(out);assert cues and out.suffix.lower()=='.mp4' and not out.exists() and out.resolve()!=master.resolve();image_ok(master);src=sha(master);out.parent.mkdir(parents=True,exist_ok=True)
 with TemporaryDirectory(prefix='.st-t4-',dir=out.parent) as t:
  tmp=Path(t);cmd=['ffmpeg','-hide_banner','-nostdin','-v','error','-y','-filter_complex_threads','1','-i',str(master)]
  for i,c in enumerate(cues):
   img=tmp/f'{i}.png';image_texte(c,img);cmd+=['-loop','1','-framerate','30','-i',str(img)]
  graph=[];prev='0:v'
  for i,c in enumerate(cues):
   outname='outv' if i==len(cues)-1 else f'st{i}';graph.append(f'[{prev}][{i+1}:v]overlay=0:0:enable=\'gte(t,{c["debut"]})*lt(t,{c["fin"]})\':shortest=1[{outname}]');prev=outname
  result=tmp/'legendes.mp4';cmd+=['-filter_complex',';'.join(graph),'-map','[outv]','-frames:v','900','-an','-c:v','libx264','-preset','veryfast','-crf','19','-threads','2','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',str(result)]
  subprocess.run(cmd,check=True,capture_output=True,timeout=300);image_ok(result);assert sha(master)==src;os.link(result,out)
 return {'statut':'proposition locale : synchronisation et mots à vérifier avec la voix','source_sha256':src,'image_sha256':sha(out),'cues':cues,'police':'DM Sans 600','voix_ou_texte_verify':False}
