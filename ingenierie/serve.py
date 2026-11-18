"""Serve the package and support media byte ranges without exposing parent paths."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from functools import partial
import argparse, re, shutil, urllib.parse
ROOT=Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
 def send_head(self):
  self.byte_limit=None
  parts=urllib.parse.unquote(urllib.parse.urlparse(self.path).path).split('/')
  if any(t.startswith('.') or t=='__pycache__' for t in parts):self.send_error(404);return None
  p=Path(self.translate_path(self.path))
  if not p.is_file() or p.suffix!='.mp4' or not self.headers.get('Range'):return super().send_head()
  m=re.fullmatch(r'bytes=(\d*)-(\d*)',self.headers['Range'].strip());n=p.stat().st_size
  if not m or not (m[1] or m[2]):self.send_error(416);return None
  lo,hi=(int(m[1]),min(int(m[2]),n-1) if m[2] else n-1) if m[1] else (max(0,n-int(m[2])),n-1)
  if hi<lo or lo>=n:self.send_error(416);return None
  f=p.open('rb');f.seek(lo);self.byte_limit=hi-lo+1
  self.send_response(206);self.send_header('Content-Range',f'bytes {lo}-{hi}/{n}');self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(self.byte_limit));self.send_header('Content-Type','video/mp4');self.end_headers();return f
 def copyfile(self,source,outputfile):
  if self.byte_limit is None:
   try:shutil.copyfileobj(source,outputfile)
   except (BrokenPipeError,ConnectionResetError):pass
   return
  n=self.byte_limit
  try:
   while n and (a:=source.read(min(n,1<<17))):outputfile.write(a);n-=len(a)
  except (BrokenPipeError,ConnectionResetError):pass
 def list_directory(self,path):self.send_error(404);return None
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8080);p.add_argument('--host',default='0.0.0.0');a=p.parse_args()
 with ThreadingHTTPServer((a.host,a.port),partial(Handler,directory=str(ROOT))) as s:
  print(f'Vitrine Vidéo — serveur prêt : {a.host}:{a.port}',flush=True);s.serve_forever()
