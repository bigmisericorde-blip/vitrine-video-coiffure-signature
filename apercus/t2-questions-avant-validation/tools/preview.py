#!/usr/bin/env python3
"""Serveur de prévisualisation uniquement. Publication = site statique GitHub Pages."""
import argparse
import os
import re
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial
from urllib.parse import urlsplit, unquote

class Site(SimpleHTTPRequestHandler):
    def send_head(self):
        parts = unquote(urlsplit(self.path).path).split('/')
        if any(x.startswith('.') for x in parts if x) or any(x in ('tools','local','node_modules') for x in parts):
            self.send_error(404); return None
        # Permet de parcourir les extraits de la référence locale sans recharger tout le film.
        self.range_length=None
        path=self.translate_path(self.path);r=self.headers.get('Range')
        if r and os.path.isfile(path):
            m=re.fullmatch(r'bytes=(\d+)-(\d*)',r)
            if m:
                f=open(path,'rb');size=os.fstat(f.fileno()).st_size;start=int(m.group(1));end=min(int(m.group(2)) if m.group(2) else size-1,size-1)
                if start>=size or end<start:
                    f.close();self.send_error(416);return None
                self.send_response(206);self.send_header('Content-Type',self.guess_type(path));self.send_header('Accept-Ranges','bytes');self.send_header('Content-Range',f'bytes {start}-{end}/{size}');self.range_length=end-start+1;self.send_header('Content-Length',str(self.range_length));self.end_headers();f.seek(start);return f
        return super().send_head()
    def copyfile(self,source,out):
        if self.range_length is None:return super().copyfile(source,out)
        remaining=self.range_length
        while remaining:
            data=source.read(min(65536,remaining))
            if not data:break
            out.write(data);remaining-=len(data)
    def list_directory(self, path):
        self.send_error(404); return None
    def end_headers(self):
        self.send_header('Cache-Control','no-cache')
        super().end_headers()

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--port',default=8092,type=int);p.add_argument('--host',default='0.0.0.0');a=p.parse_args()
    s=ThreadingHTTPServer((a.host,a.port),partial(Site,directory=str(Path(__file__).resolve().parents[1])))
    print(f'Vitrine Vidéo : {a.host}:{a.port}',flush=True);s.serve_forever()
