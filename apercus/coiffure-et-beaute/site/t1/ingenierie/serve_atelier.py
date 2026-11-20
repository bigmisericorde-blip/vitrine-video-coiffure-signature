#!/usr/bin/env python3
"""Serveur atelier, montage à la demande. Seuls les exports temporaires sont servis."""
from email import policy
from email.parser import BytesParser
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
import argparse
import json
import logging
import os
import re
import secrets
import socket
import tempfile
import threading
import time
from urllib.parse import urlparse

from core import ROOT
from mix_voix import MediaError
from postproduction import finalize
from serve import Handler
from voix_texte import available

TTL=45*60
MIB=1024*1024
VIDEO_LIMIT=64*MIB
VOICE_LIMIT=12*MIB
TOTAL=VIDEO_LIMIT+VOICE_LIMIT+16384
FIELDS={'mode','lang','texte','browser','precedente','music','video','voix','liaison','fond'}


class AtelierServer(ThreadingHTTPServer):
    daemon_threads=True

    def __init__(self, address, handler, work, *, atelier_home=False):
        self.atelier_home=atelier_home
        self.work=Path(work).resolve()
        if self.work.is_relative_to(ROOT): raise ValueError('Les fichiers clients doivent rester hors dossier public.')
        self.exports=self.work/'exports'
        self.exports.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.rotation=self.work/'rotation.sqlite'
        self.render_slots=threading.BoundedSemaphore(2)
        super().__init__(address,handler)

    def expire(self):
        before=time.time()-TTL
        for p in self.exports.glob('*.mp4'):
            try:
                if p.stat().st_mtime<before: p.unlink(missing_ok=True)
            except FileNotFoundError: pass


class AtelierHandler(Handler):
    def setup(self):
        super().setup();self.connection.settimeout(60)

    def data(self,code,payload):
        raw=json.dumps(payload,ensure_ascii=False).encode()
        self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store')
        self.end_headers()
        if self.command!='HEAD':
            try: self.wfile.write(raw)
            except (BrokenPipeError,ConnectionResetError,TimeoutError): pass

    def translate_path(self,path):
        self._export_path=False
        u=urlparse(path)
        m=re.fullmatch(r'/api/montages/([a-f0-9]{32})\.mp4',u.path)
        if m:
            self._export_path=True
            return str(self.server.exports/(m[1]+'.mp4'))
        return super().translate_path(path)

    def send_head(self):
        p=urlparse(self.path).path
        self._export_path=False
        if p=='/' and self.server.atelier_home:
            self.send_response(302);self.send_header('Location','atelier.html');self.send_header('Content-Length','0');self.end_headers()
            return None
        if p=='/api/atelier/config':
            self.data(200,{'ok':True,'duree_max':30,'max_video_octets':VIDEO_LIMIT,
                           'max_voix_octets':VOICE_LIMIT,'langues_texte':available(),'expiration_minutes':TTL//60,'liaison_t2':True})
            return None
        if p.startswith('/api/'):
            if not re.fullmatch(r'/api/montages/[a-f0-9]{32}\.mp4',p):
                self.data(404,{'error':'Aucun résultat à cette adresse.'});return None
            self.server.expire()
        return super().send_head()

    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff')
        if getattr(self,'_export_path',False):
            self.send_header('Cache-Control','private, no-store')
            self.send_header('Referrer-Policy','no-referrer')
            if urlparse(self.path).query=='download=1':
                self.send_header('Content-Disposition','attachment; filename="vitrine-montage.mp4"')
        super().end_headers()

    def form(self):
        c=self.headers.get('Content-Type','')
        if len(c)>180 or not re.fullmatch(r'multipart/form-data; boundary=[-A-Za-z0-9_.]{1,90}',c):
            raise MediaError('Le formulaire envoyé n’est pas valide.')
        n=int(self.headers.get('Content-Length','0'))
        if not 1<=n<=TOTAL:
            raise MediaError('Fichier trop volumineux : maximum 64 Mo de vidéo ou 12 Mo d’audio.')
        raw=self.rfile.read(n)
        if len(raw)!=n: raise MediaError('Envoi incomplet. Réessaie.')
        msg=BytesParser(policy=policy.default).parsebytes(f'Content-Type: {c}\r\nMIME-Version: 1.0\r\n\r\n'.encode()+raw)
        out={}
        for part in msg.iter_parts():
            name=part.get_param('name',header='Content-Disposition')
            body=part.get_payload(decode=True)
            if name not in FIELDS or name in out or body is None or part.is_multipart():
                raise MediaError('Le formulaire contient une donnée inattendue.')
            if name in {'video','voix'}:
                limit=VIDEO_LIMIT if name=='video' else VOICE_LIMIT
                if not 1<=len(body)<=limit: raise MediaError('Limite dépassée : 64 Mo de vidéo ou 12 Mo d’audio.')
                out[name]=body
            else:
                if len(body)>3000: raise MediaError('Le texte est trop long.')
                out[name]=body.decode('utf-8')
        return out

    def do_POST(self):
        self.close_connection=True
        if self.path!='/api/montages': return self.data(404,{'error':'Adresse inconnue.'})
        if self.headers.get('Sec-Fetch-Site')=='cross-site': return self.data(403,{'error':'Ouvre l’atelier directement.'})
        if not self.server.render_slots.acquire(blocking=False):
            return self.data(429,{'error':'L’atelier termine un autre rendu. Réessaie dans quelques instants.'})
        try:
            fields=self.form(); mode=fields.get('mode','sans')
            browser=fields.get('browser',''); prev=fields.get('precedente','')
            if not re.fullmatch(r'[a-f0-9]{32}',browser) or (prev and not re.fullmatch(r'[a-z0-9-]{1,36}',prev)):
                raise MediaError('Session atelier invalide. Recharge la page.')
            linked=fields.get('liaison','')
            if linked not in ('','t2'): raise MediaError('Liaison de gabarit invalide.')
            self.server.expire(); key=secrets.token_hex(16)
            with tempfile.TemporaryDirectory(prefix='entree-',dir=self.server.work) as directory:
                temp=Path(directory);video=voice=None
                if 'video' in fields:
                    video=temp/'video.upload';video.write_bytes(fields['video'])
                if 'voix' in fields and mode=='audio':
                    voice=temp/'voix.upload';voice.write_bytes(fields['voix'])
                output=self.server.exports/(key+'.mp4')
                result=finalize(output,video=video,mode=mode,voice=voice,text=fields.get('texte',''),lang=fields.get('lang',''),
                                music=fields.get('music')!='0',atelier=browser,previous=prev,state=self.server.rotation,
                                linked_t2=linked=='t2',fixed_track=fields.get('fond'))
            result['url']='api/montages/'+key+'.mp4'
            self.data(201,result)
        except (MediaError,UnicodeError,ValueError) as e:
            self.data(422,{'error':str(e) if isinstance(e,MediaError) else 'Le fichier ou le formulaire n’est pas valide.'})
        except (socket.timeout,ConnectionResetError):
            self.data(408,{'error':'Transfert interrompu. Vérifie ta connexion.'})
        except Exception:
            logging.exception('Échec du moteur sans journaliser les entrées')
            self.data(500,{'error':'Le montage n’a pas pu être créé. Réessaie en choisissant un autre fichier.'})
        finally:
            self.server.render_slots.release()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8080)
    p.add_argument('--host',default='0.0.0.0')
    p.add_argument('--work',type=Path,default=Path(os.environ.get('VV_WORK_DIR') or Path.home()/'.local/state/vitrine-video/atelier'))
    p.add_argument('--atelier-home',action='store_true',help='Ouvrir l’atelier voix à la racine au lieu de la fiche T2')
    a=p.parse_args()
    with AtelierServer((a.host,a.port),partial(AtelierHandler,directory=str(ROOT)),a.work,atelier_home=a.atelier_home) as server:
        print(f'Gabarit T2 et atelier voix prêts sur {a.host}:{a.port}',flush=True)
        print('Langues de synthèse : '+(', '.join(t['label'] for t in available()) or 'aucun modèle installé'),flush=True)
        server.serve_forever()


if __name__=='__main__': main()
