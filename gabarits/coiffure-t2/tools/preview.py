#!/usr/bin/env python3
"""Serveur de prévisualisation uniquement. Publication = site statique GitHub Pages."""
import argparse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial
from urllib.parse import urlsplit, unquote

class Site(SimpleHTTPRequestHandler):
    def send_head(self):
        parts = unquote(urlsplit(self.path).path).split('/')
        if any(x.startswith('.') for x in parts if x) or any(x in ('tools','local','node_modules') for x in parts):
            self.send_error(404); return None
        return super().send_head()
    def list_directory(self, path):
        self.send_error(404); return None
    def end_headers(self):
        self.send_header('Cache-Control','no-cache')
        super().end_headers()

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--port',default=8092,type=int);p.add_argument('--host',default='0.0.0.0');a=p.parse_args()
    s=ThreadingHTTPServer((a.host,a.port),partial(Site,directory=str(Path(__file__).resolve().parents[1])))
    print(f'Vitrine Vidéo : {a.host}:{a.port}',flush=True);s.serve_forever()
