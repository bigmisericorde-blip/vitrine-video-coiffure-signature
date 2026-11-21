#!/usr/bin/env python3
"""Passerelle locale de revue ; aucune dépendance Web ni publication de médias client."""
from argparse import ArgumentParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock, Thread
from uuid import uuid4
import json
import re
import secrets
import shutil
from engine.commun import ROOT, TAKES, TRACKS, MAX_TAKE, Outils, Erreur, exige, lire, lire_fiche, loi, jsonunique
from engine import musiques
from t3 import rendre, annuler


class Session:
    def __init__(self, dest):
        self.dest=dest;self.dest.mkdir(mode=0o700);self.lock=Lock();self.jobs={}


class Appli(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self, address, config, temp):
        super().__init__(address, Vue);self.config=config;self.temp=temp;self.sessions={};self.lock=Lock();self.calcul=Lock()
        self.outils=Outils(config.ffmpeg,config.ffprobe);self.musique=musiques.verifier(config.pack)


class Vue(BaseHTTPRequestHandler):
    sys_version='';server_version='Vitrine-T3'
    def setup(self):
        super().setup();self.connection.settimeout(30)

    def log_message(self, *args):
        pass # pas de contenu, chemin d’export, token ni nom de fichier dans les logs

    def repond(self, status, content, kind, extra=None):
        self.send_response(status)
        self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(content)))
        self.send_header('Cache-Control','no-store')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; media-src 'self' blob:; img-src 'self' data: blob:; object-src 'none'; base-uri 'none'; form-action 'self'")
        if extra:
            for k,v in extra.items():self.send_header(k,v)
        self.end_headers();self.wfile.write(content)

    def data(self, status, x):
        self.repond(status,json.dumps(x,ensure_ascii=False).encode(),'application/json; charset=utf-8')

    def garde(self, f):
        try:
            if self.headers.get('Sec-Fetch-Site')=='cross-site' and self.path.startswith('/api/'):
                self.data(403,{'erreur':{'code':'ORIGINE','message':'Appel hors du parcours T3.'}});return
            f()
        except (BrokenPipeError,ConnectionResetError,TimeoutError):pass
        except Erreur as e:self.data(422,{'erreur':e.as_dict()})
        except (OSError,KeyError,ValueError,TypeError):
            self.data(400,{'erreur':{'code':'REQUETE','message':'Action ou fichier non disponible.'}})

    def do_GET(self):self.garde(self.get)
    def do_POST(self):self.garde(self.post)
    def do_PUT(self):self.garde(self.put)
    def do_DELETE(self):self.garde(self.delete)

    def session(self):
        tok=self.headers.get('X-T3-Session','')
        exige(tok in self.server.sessions,'SESSION','Session absente. Recharge le parcours.')
        return self.server.sessions[tok]

    def job(self):
        m=re.fullmatch(r'/api/jobs/([0-9a-f]{32})(/[A-Z0-9a-z.]+)?',self.path)
        exige(bool(m),'REQUETE','Action non reconnue.');s=self.session();j=m[1]
        exige(j in s.jobs,'JOB','Ce rendu ne fait pas partie de cette session.')
        return s,j,s.jobs[j],m[2] or ''

    def taille(self,maxi):
        exige(not self.headers.get('Transfer-Encoding'),'REQUETE','Longueur du fichier requise.')
        n=int(self.headers.get('Content-Length','0'));exige(0<n<=maxi,'TAILLE','Fichier absent ou trop lourd.');return n

    def lire_json(self):
        exige(self.headers.get_content_type()=='application/json','REQUETE','Document JSON requis.')
        return jsonunique(self.rfile.read(self.taille(16000)).decode())

    def get(self):
        files={'/':('index.html','text/html'),'/app.css':('app.css','text/css'),'/app.js':('app.js','text/javascript')}
        if self.path in files:
            name,fmt=files[self.path];self.repond(200,(ROOT/'web'/name).read_bytes(),fmt+'; charset=utf-8');return
        c=self.server.config
        if self.path=='/api/config':
            cats=self.server.musique['titres']
            self.data(200,{'contrat':loi(),'exemple':lire(ROOT/'exemple/fiche.json'),'demo':c.demo,
                           'catalogue':[{'id':k,'titre':cats[k]['titre'],'artiste':cats[k]['artiste'],'licence':cats[k]['licence']} for k in TRACKS]});return
        m=re.fullmatch(r'/exemple/(S[1-4])\.mp4',self.path)
        if m:
            self.repond(200,(c.exemple/(m[1]+'.mp4')).read_bytes(),'video/mp4');return
        if self.path.startswith('/api/jobs/'):
            s,j,d,op=self.job();r=s.dest/'exports'/j
            if op in ('/film.mp4','/credit.txt'):
                exige(d['phase']=='termine','JOB','Le film n’est pas encore prêt.')
                if op=='/film.mp4':self.repond(200,(r/'T3.mp4').read_bytes(),'video/mp4')
                else:self.repond(200,(r/'Credit-musique.txt').read_bytes(),'text/plain; charset=utf-8')
                return
            if op=='':
                out={k:d[k] for k in ('phase','avancement')};out['erreur']=d.get('erreur')
                if d['phase']=='termine':out['resultat']=lire(r/'resultat.json')
                self.data(200,out);return
        self.data(404,{'erreur':{'code':'PAGE','message':'Page introuvable.'}})

    def post(self):
        app=self.server
        if self.path=='/api/session':
            exige(self.lire_json()=={},'REQUETE','Création de session invalide.')
            with app.lock:
                exige(len(app.sessions)<16,'LIMITE','Atelier occupé. Relance le service local si nécessaire.')
                token=secrets.token_urlsafe(32);app.sessions[token]=Session(app.temp/uuid4().hex)
            self.data(201,{'session':token});return
        if self.path=='/api/jobs':
            s=self.session();x=self.lire_json();exige(isinstance(x,dict) and set(x)=={'fiche','mode','piste','exemple'},'JOB','Job incomplet.')
            x['fiche']=lire_fiche(x['fiche']);exige(x['mode'] in loi()['audio_modes'] and x['piste'] in (*TRACKS,None) and
               (x['mode']!='muet' or x['piste'] is None) and type(x['exemple']) is bool,'JOB','Choix invalide.')
            exige(not app.config.demo or x['exemple'],'DEMO','Sur cet aperçu seules les prises synthétiques sont acceptées.')
            with s.lock:
                exige(len(s.jobs)<12,'LIMITE','Ferme des rendus avant d’en ouvrir d’autres.')
                j=uuid4().hex;u=s.dest/'imports'/j;u.mkdir(parents=True,mode=0o700)
                s.jobs[j]=x|{'phase':'imports','avancement':0,'dossier':u,'prises':{k:app.config.exemple/(k+'.mp4') for k in TAKES} if x['exemple'] else {}}
            self.data(201,{'job':j});return
        s,j,d,op=self.job();exige(op=='/rendre' and self.lire_json()=={},'REQUETE','Action de rendu invalide.')
        with s.lock:
            phase=d['phase']
            if phase in ('imports','echec'):
                exige(set(d['prises'])==set(TAKES),'PRISE','Garde les quatre prises avant le montage.')
                exige(app.calcul.acquire(blocking=False),'OCCUPE','Un rendu est en cours. Réessaie dans quelques secondes.')
                d.update(phase='controle',avancement=3,erreur=None)
                try:Thread(target=self.calculer,args=(app,s,j,d),daemon=True).start()
                except RuntimeError:
                    d.update(phase=phase,avancement=0);app.calcul.release();raise Erreur('OCCUPE','Impossible de démarrer. Réessaie.')
        self.data(200 if phase=='termine' else 202,{'job':j})

    @staticmethod
    def calculer(app,s,j,d):
        c=app.config
        def progress(p,n):
            # Le MP4 n’est annoncé terminé qu’après retour du moteur et état de rotation écrit.
            with s.lock:d.update(phase='verification' if p=='termine' else p,avancement=min(99,n))
        try:
            rendre(app.outils,d['fiche'],d['prises'],s.dest,c.polices,c.pack,j,d['mode'],d['piste'],False,progress)
            with s.lock:d.update(phase='termine',avancement=100)
        except (Erreur,OSError,RuntimeError) as e:
            with s.lock:d.update(phase='echec',erreur=e.as_dict() if isinstance(e,Erreur) else {'code':'RENDU','message':'Échec du rendu. Les fichiers originaux n’ont pas été modifiés.'})
        finally:app.calcul.release()

    def put(self):
        s,j,d,op=self.job();p=op[1:];exige(p in TAKES and not d['exemple'] and not self.server.config.demo,'PRISE','Import indisponible ici.')
        exige(self.headers.get_content_type()=='application/octet-stream','PRISE','Envoie le fichier vidéo complet.')
        n=self.taille(MAX_TAKE)
        with s.lock:
            exige(d['phase']=='imports','PRISE','Ce rendu est déjà lancé.')
            out=d['dossier']/(p+'.clip');tmp=out.with_suffix('.tmp')
            try:
                with tmp.open('wb') as file:
                    while n:
                        b=self.rfile.read(min(262144,n));exige(b,'PRISE','Transfert interrompu.',p);file.write(b);n-=len(b)
                tmp.replace(out);d['prises'][p]=out
            finally:tmp.unlink(missing_ok=True)
        self.data(200,{'prise':p})

    def delete(self):
        s,j,d,op=self.job();exige(not op,'REQUETE','Action inconnue.')
        with s.lock:
            exige(d['phase'] in ('importe','imports','echec','termine'),'JOB','Attends la fin du rendu.')
            exige(self.server.calcul.acquire(blocking=False),'OCCUPE','Attends la fin de l’export en cours.')
            try:
                annuler(s.dest,j);shutil.rmtree(d['dossier'],ignore_errors=True);shutil.rmtree(s.dest/'exports'/j,ignore_errors=True);del s.jobs[j]
            finally:self.server.calcul.release()
        self.data(200,{'ok':True})


def main():
    p=ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8094);p.add_argument('--host',default='127.0.0.1')
    p.add_argument('--demo',action='store_true',help='Limiter les prises aux mires synthétiques du lot')
    for name in ('pack','exemple','polices'):p.add_argument('--'+name,type=Path,default=ROOT/('audio' if name=='pack' else name))
    p.add_argument('--ffmpeg');p.add_argument('--ffprobe');a=p.parse_args()
    if not a.demo and a.host not in ('127.0.0.1','localhost'):p.error('Sur une interface réseau, utiliser --demo : pas d’import client.')
    if not all((a.exemple/(s+'.mp4')).is_file() for s in TAKES):p.error('Mires S1–S4 manquantes ; voir INTEGRATION.md.')
    with TemporaryDirectory(prefix='t3-session-') as temp,Appli((a.host,a.port),a,Path(temp)) as server:
        print(f'Atelier T3 prêt sur le port {server.server_port} (démo : {a.demo})',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass


if __name__=='__main__':main()
