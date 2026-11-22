#!/usr/bin/env python3
"""Atelier prototype T4, uniquement sur 127.0.0.1, jamais production ni publication.
Données temporaires effacées à l'arrêt normal ; aucun log de noms, fichiers ou fiches.
"""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock,Thread
from urllib.parse import urlsplit
from uuid import uuid4
import argparse,json,os,re,secrets,subprocess,sys
from fiche_t4 import verifier,vers_image,FicheInvalide
from image_t4 import render,overlay,LABELS
from son_t4 import rendre
from sous_titres import valider as valider_sous_titres,appliquer as appliquer_sous_titres,image_texte,SousTitresInvalides
D=Path(__file__).resolve().parent

def fiche_admissible(raw):
 f=verifier(raw);v=vers_image(f)
 try:
  with TemporaryDirectory(prefix='t4-verif-texte-') as tmp:
   for i,k in enumerate(LABELS):overlay(v[k],Path(tmp)/f'{i}.png',v.get('signature','') if i==3 else '')
 except AssertionError:raise FicheInvalide('Le texte ou la signature est trop long pour être affiché sans coupure.')
 return f

class App(ThreadingHTTPServer):
 daemon_threads=True
 def __init__(self,addr,root):
  super().__init__(addr,Handler);self.root=root;self.token=secrets.token_urlsafe(32);self.jobs={};self.lock=Lock();self.encode=Lock()
 def worker(self,j):
  try:
   with self.encode:
    j.update(status='en_cours',message='Préparation des quatre prises…');inputs=[]
    for i in range(1,5):
     raw=j['path']/f'brut-{i}.bin';out=j['path']/f'S{i}.mp4'
     cmd=['ffmpeg','-nostdin','-y','-v','error','-xerror','-protocol_whitelist','file,pipe','-i',str(raw),'-map','0:v:0','-an','-vf','fps=30,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1','-frames:v',str([6,13,8,7][i-1]*30),'-c:v','libx264','-preset','veryfast','-crf','20','-threads','2','-pix_fmt','yuv420p',str(out)]
     subprocess.run(cmd,check=True,capture_output=True,timeout=120);inputs.append(out)
    j.update(message='Montage de l’image…');master=j['path']/'master.mp4';render(vers_image(j['fiche']),inputs,master)
    if j.get('sous_titres'):
     j.update(message='Incrustation des sous-titres saisis…');legende=j['path']/'master-sous-titres.mp4';appliquer_sous_titres(master,j['sous_titres'],legende);master=legende
    j.update(message='Ajout de la musique et contrôles…');voice=j['path']/'voix.bin';result=rendre(master,j['path']/'film.mp4',self.root/'rotation.sqlite',voix=voice if voice.is_file() else None);j.update(status='termine',message='Montage de test terminé.',credit=result['credit'])
  except Exception as e:
   # Détail de debug local borné ; ne jamais donner ni contenu de fiche ni chemin dans l'interface.
   j.update(status='echec',message='Montage impossible. Vérifie les prises et réessaie.',debug_type=type(e).__name__,debug=str(e)[:200])

class Handler(BaseHTTPRequestHandler):
 server_version='Prototype-T4';sys_version=''
 def log_message(self,*a):pass
 def respond(self,status,body,ctype='application/json; charset=utf-8'):
  if not isinstance(body,bytes):body=json.dumps(body,ensure_ascii=False).encode()
  self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('Referrer-Policy','no-referrer');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; font-src data:; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'");self.end_headers();self.wfile.write(body)
 def authorized(self):
  host=self.headers.get('Host','');expected=f'127.0.0.1:{self.server.server_port}'
  if host!=expected or self.headers.get('Sec-Fetch-Site')=='cross-site':return False
  origin=self.headers.get('Origin');return (not origin or origin==f'http://{expected}') and secrets.compare_digest(self.headers.get('X-T4-Session',''),self.server.token)
 def body(self,maxi):
  if self.headers.get('Transfer-Encoding'):raise ValueError('Transfert non autorisé')
  n=int(self.headers.get('Content-Length','0'))
  if not 0<n<=maxi:raise ValueError('Taille non autorisée')
  b=self.rfile.read(n)
  if len(b)!=n:raise ValueError('Lecture incomplète')
  return b
 def guard(self,fn):
  try:fn()
  except (ValueError,FicheInvalide,json.JSONDecodeError,UnicodeDecodeError):self.respond(400,{'error':'Fiche ou prise invalide.'})
  except (BrokenPipeError,ConnectionResetError):pass
  except Exception:self.respond(500,{'error':'Atelier local indisponible.'})
 def do_GET(self):self.guard(self.get)
 def do_POST(self):self.guard(self.post)
 def do_PUT(self):self.guard(self.put)
 def get(self):
  if self.path=='/' and self.headers.get('Host')==f'127.0.0.1:{self.server.server_port}':
   data=(D/'capture-t4-prototype.html').read_text().replace('__SESSION_TOKEN__',self.server.token).encode();self.respond(200,data,'text/html; charset=utf-8');return
  if not self.authorized():self.respond(403,{'error':'Session locale requise.'});return
  m=re.fullmatch(r'/api/job/([0-9a-f]{32})(/film)?',self.path)
  if not m or m[1] not in self.server.jobs:self.respond(404,{'error':'Montage introuvable.'});return
  j=self.server.jobs[m[1]]
  if m[2]:
   if j['status']!='termine':self.respond(409,{'error':'Montage non terminé.'});return
   self.respond(200,(j['path']/'film.mp4').read_bytes(),'video/mp4');return
  self.respond(200,{k:j.get(k) for k in ('status','message','credit')})
 def post(self):
  if not self.authorized():self.respond(403,{'error':'Session locale requise.'});return
  x=json.loads(self.body(16384).decode())
  if self.path=='/api/fiche/verifier':
   try:fiche_admissible(x)
   except FicheInvalide as e:self.respond(422,{'error':str(e)});return
   self.respond(200,{'statut':'fiche reçue pour test local'});return
  if self.path=='/api/job':
   f=fiche_admissible(x)
   with self.server.lock:
    if len(self.server.jobs)>=8:self.respond(429,{'error':'Trop de montages dans cet essai.'});return
    uid=uuid4().hex;path=self.server.root/uid;path.mkdir(mode=0o700);self.server.jobs[uid]={'fiche':f,'path':path,'status':'prises','message':'En attente des prises.'}
   self.respond(201,{'id':uid});return
  m=re.fullmatch(r'/api/job/([0-9a-f]{32})/sous-titres',self.path)
  if m and m[1] in self.server.jobs:
   j=self.server.jobs[m[1]]
   if j['status']!='prises':self.respond(409,{'error':'Montage déjà commencé.'});return
   try:
    cues=valider_sous_titres(x)
    with TemporaryDirectory(prefix='t4-verif-st-') as tmp:
     for i,c in enumerate(cues):image_texte(c,Path(tmp)/f'{i}.png')
   except SousTitresInvalides as e:self.respond(422,{'error':str(e)});return
   j['sous_titres']=cues;self.respond(200,{'nombre':len(cues)});return
  m=re.fullmatch(r'/api/job/([0-9a-f]{32})/rendre',self.path)
  if not m or m[1] not in self.server.jobs or x!={}:self.respond(404,{'error':'Montage introuvable.'});return
  with self.server.lock:
   j=self.server.jobs[m[1]]
   if j['status']!='prises' or not all((j['path']/f'brut-{i}.bin').is_file() for i in range(1,5)):self.respond(409,{'error':'Quatre prises sont nécessaires.'});return
   if j.get('sous_titres') and not (j['path']/'voix.bin').is_file():self.respond(409,{'error':'La voix des sous-titres est nécessaire.'});return
   j.update(status='en_cours',message='Préparation du montage…');Thread(target=self.server.worker,args=(j,),daemon=True).start()
  self.respond(202,{'status':'en_cours'})
 def put(self):
  if not self.authorized():self.respond(403,{'error':'Session locale requise.'});return
  m=re.fullmatch(r'/api/job/([0-9a-f]{32})/(S[1-4]|voix)',self.path)
  if not m or m[1] not in self.server.jobs:self.respond(404,{'error':'Montage introuvable.'});return
  j=self.server.jobs[m[1]]
  if j['status']!='prises':self.respond(409,{'error':'Montage déjà commencé.'});return
  kind=m[2];b=self.body((16 if kind=='voix' else 48)*1024*1024);target=j['path']/('voix.bin' if kind=='voix' else f'brut-{kind[1]}.bin')
  with target.open('xb') as f:f.write(b)
  self.respond(200,{'element':kind,'octets':len(b)})

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8766);a=p.parse_args();assert 0<=a.port<=65535
 with TemporaryDirectory(prefix='vv-t4-local-') as t:
  root=Path(t);os.chmod(root,0o700)
  with App(('127.0.0.1',a.port),root) as app:
   print(f'Atelier T4 local de test, http://127.0.0.1:{app.server_port}/',flush=True)
   try:app.serve_forever()
   except KeyboardInterrupt:pass
if __name__=='__main__':main()
