#!/usr/bin/env python3
"""Aperçu de la copie Coiffure et beauté. Aucun déploiement ni accès GitHub."""
from argparse import ArgumentParser
from functools import partial
from pathlib import Path
import sys
from urllib.parse import urlsplit, unquote

SITE=Path(__file__).resolve().parent/'site'
sys.path.insert(0,str(SITE/'t1'/'ingenierie'))
from serve_atelier import AtelierServer, AtelierHandler


class Handler(AtelierHandler):
    def end_headers(self):
        self.send_header('Referrer-Policy','no-referrer')
        super().end_headers()

    def send_head(self):
        original=self.path
        path=unquote(urlsplit(original).path)
        if path.startswith('/t1/api/'):
            self.path=original[3:]
            try: return super().send_head()
            finally: self.path=original
        if path.startswith('/api/') or Path(path).suffix.lower() in {'.py','.pyc'}:
            self.send_error(404);return None
        return super().send_head()

    def do_POST(self):
        if self.path!='/t1/api/montages':
            self.close_connection=True;return self.data(404,{'error':'Adresse inconnue.'})
        self.path='/api/montages'
        super().do_POST()


def main():
    p=ArgumentParser(description=__doc__)
    p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8112)
    p.add_argument('--work',type=Path,default=Path.home()/'.local/state/vitrine-video/beaute-preview')
    a=p.parse_args()
    if a.work.resolve().is_relative_to(SITE):p.error('Le dossier de travail doit rester hors du site.')
    with AtelierServer((a.host,a.port),partial(Handler,directory=str(SITE)),a.work) as http:
        print(f'Coiffure et beauté · T1 et T2 · http://{a.host}:{http.server_port}/',flush=True)
        http.serve_forever()

if __name__=='__main__':main()
