#!/usr/bin/env python3
"""Prototype visuel de revue T4 : fiche fictive + 4 prises → master silencieux.
Bornes de montage et moteur provisoires ; ne pas livrer ni confondre avec Parfum R2 approuvé.
"""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,tempfile,os
from PIL import Image,ImageDraw,ImageFont
from son_t4 import probe,sha,image_ok,DEMO_SHA256
D=Path(__file__).resolve().parent
# Images de sortie d'après les repères de montage proposés R2, pas des durées validées.
FRAMES=(152,369,206,173);CAPTURE_SECS=(6,13,8,7);LABELS=('accroche','offre','detail_visible','invitation')

def clean_fiche(x):
 assert set(LABELS)<=set(x)<=set(LABELS)|{'signature'},'Fiche provisoire incorrecte.'
 for k in LABELS:
  s=x[k];assert isinstance(s,str) and len(s)<=65 and not re.search(r'[<>\x00-\x1f]',s) and (s.strip() or k=='invitation'),f'Champ {k} invalide'
 out={k:x[k].strip() for k in LABELS}
 if 'signature' in x:
  s=x['signature'];assert isinstance(s,str) and len(s)<=350 and not re.search(r'[<>\x00-\x1f]',s),'Signature invalide';out['signature']=s.strip()
 return out

def overlay(text,path,signature=''):
 im=Image.new('RGBA',(720,1280));d=ImageDraw.Draw(im);fontpath=D/'polices/CormorantGaramond.ttf';font=ImageFont.truetype(str(fontpath),64);font.set_variation_by_axes([560])
 if text:
  words=text.split();lines=[];line=''
  for w in words:
   q=(line+' '+w).strip()
   if d.textlength(q,font=font)>630 and line:lines.append(line);line=w
   else:line=q
  if line:lines.append(line)
  assert len(lines)<=3 and all(d.textlength(s,font=font)<=640 for s in lines),'Texte trop long pour ce prototype'
  for i in range(380):d.line([(0,i),(719,i)],fill=(23,7,15,max(0,145-int(i*145/380))))
  y=110
  for line in lines:
   d.text((360,y),line,font=font,anchor='mt',fill=(255,238,224,255),stroke_width=1,stroke_fill=(23,7,15,190));y+=72
 if signature:
  f=ImageFont.truetype(str(D/'polices/DMSans.ttf'),30);f.set_variation_by_axes([14,600]);lines=[];line=''
  for token in signature.split(' '):
   while d.textlength(token,font=f)>620:
    if line:lines.append(line);line=''
    n=len(token)
    while n>1 and d.textlength(token[:n],font=f)>620:n-=1
    lines.append(token[:n]);token=token[n:]
   candidate=(line+' '+token).strip()
   if d.textlength(candidate,font=f)>620 and line:lines.append(line);line=token
   else:line=candidate
  if line:lines.append(line)
  assert len(lines)<=6,'Signature trop longue pour être affichée sans couper les informations.'
  for y in range(965,1280):d.line([(0,y),(719,y)],fill=(23,7,15,max(0,int((y-965)*.62))))
  y=1014
  for line in lines:d.text((360,y),line,font=f,anchor='mt',fill=(255,247,238,255));y+=36
 im.save(path)

def render(fiche,prises,out):
 x=clean_fiche(fiche);assert len(prises)==4 and len({Path(p).resolve() for p in prises})==4;out=Path(out);assert out.suffix.lower()=='.mp4' and not out.exists();assert out.resolve() not in {Path(p).resolve() for p in prises}
 inputs=[]
 ref=DEMO_SHA256  # interdit la référence sans l'utiliser comme entrée ni la distribuer
 for i,p in enumerate(map(Path,prises)):
  assert p.is_file() and p.suffix.lower() in ('.mp4','.mov','.webm') and sha(p)!=ref,'Une prise locale différente du film R2 est nécessaire.'
  z=probe(p);v=[k for k in z['streams'] if k['codec_type']=='video'];assert len(v)==1 and float(z['format']['duration'])+.04>=CAPTURE_SECS[i], f'Prise {i+1} plus courte que la durée de tournage validée';inputs.append(p)
 initial_hashes=[sha(p) for p in inputs];out.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='.t4-image-',dir=out.parent) as tmp:
  tmp=Path(tmp);cmd=['ffmpeg','-hide_banner','-nostdin','-v','error','-y','-filter_complex_threads','1']
  for p in inputs:cmd+=['-protocol_whitelist','file,pipe','-i',str(p)]
  for i,k in enumerate(LABELS):
   q=tmp/f'{i}.png';overlay(x[k],q,x.get('signature','') if i==3 else '');cmd+=['-loop','1','-framerate','30','-i',str(q)]
  graphs=[]
  for i,n in enumerate(FRAMES):
   graphs.append(f'[{i}:v]fps=30,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,trim=end_frame={n},setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.12,format=yuv420p[v{i}]')
  graphs.append(''.join(f'[v{i}]' for i in range(4))+'concat=n=4:v=1:a=0[base]')
  windows=[(0.35,4.75),(5.4,15.3),(18.0,23.5),(24.6,29.8)];prev='base'
  for i,(start,end) in enumerate(windows):
   dest='outv' if i==3 else f'layer{i}';graphs.append(f'[{prev}][{i+4}:v]overlay=0:0:enable=\'between(t,{start},{end})\':shortest=1[{dest}]');prev=dest
  f=tmp/'image.mp4';cmd+=['-filter_complex',';'.join(graphs),'-map','[outv]','-an','-frames:v','900','-c:v','libx264','-preset','veryfast','-crf','20','-threads','2','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',str(f)]
  subprocess.run(cmd,check=True,timeout=300,capture_output=True);image_ok(f);assert [sha(p) for p in inputs]==initial_hashes,'Une prise a changé pendant le montage';os.link(f,out)
 return {'statut':'prototype de revue non validé ni publié','fiche':x,'prises_sha256':initial_hashes,'bornes_frames_proposees':[0,152,521,727,900],'master_sha256':sha(out),'durees_capture_validees_s':list(CAPTURE_SECS),'bornes_montage':'provisoires, pas de décision déduite','media_origine':'quatre prises ; son d’origine non conservé dans le master','limites':'effets réduits, pas d’adéquation R2 revendiquée, ni capture ni sous-titres de narration'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fiche',type=Path,required=True);p.add_argument('--fiche-complete',action='store_true',help='Lire la fiche expérimentale issue des questions validées');p.add_argument('--prises',type=Path,nargs=4,required=True);p.add_argument('--sortie',type=Path,required=True);a=p.parse_args();fiche=json.loads(a.fiche.read_text());
 if a.fiche_complete:
  from fiche_t4 import vers_image
  fiche=vers_image(fiche)
 print(json.dumps(render(fiche,a.prises,a.sortie),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
