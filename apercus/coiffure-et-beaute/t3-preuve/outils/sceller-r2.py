#!/usr/bin/env python3
"""Vérifie et scelle le lot de revue r2 (aucune publication)."""
from argparse import ArgumentParser
from hashlib import file_digest, sha256
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
from base64 import b64decode

def sha(p):
 with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def seal(p):
 p=p.resolve();qa=load(p/'rapports/Recette-r2.json');media=load(p/'rapports/Media-integre.json');g=load(p/'capture/guide.json')
 assert [len(qa[k]['vues']) for k in ('mobile','bureau')]==[12,12] and qa['acces_directs']['liens_seuls']==12
 assert qa['essai']['garde_explicite']==4 and qa['hors_ligne_apercu']['vues']==12 and qa['hors_ligne_apercu']['planche_hors_ligne']
 assert sha(p/'media'/media['master'])==g['film']['sha256']==media['sha256_master']
 assert [v['id'] for v in media['derivees']['extraits']]==[f'S{n}' for n in range(1,5)]
 h=(p/'index.html').read_text(encoding='utf-8')
 def data(id):return json.loads(re.search(fr'<script type="application/json" id="{id}">(.*?)</script>',h,re.S)[1]);
 assert sha256(b64decode(data('vv-planche-data'))).hexdigest()==sha(p/'capture/planche-12-ecrans.jpg')
 x=data('vv-data');assert sha256(b64decode(x['film']['b64'])).hexdigest()==media['derivees']['film']['sha256']
 assert [sha256(b64decode(s['b64'])).hexdigest() for s in x['scenes']]==[s['sha256'] for s in media['derivees']['extraits']]
 assert len(list((p/'capture/ecrans').glob('*.jpg')))==12
 write(p/'Etat-de-la-revue.json',{'revision':'r2','statut':'lot pour la revue du propriétaire','phase_no':5,'accord_P3':None,'catalog_id':None,'master_P2_r3_inchange':True,'production_validee':False,'branche_de_revue':'review/t3-preuve-12-ecrans','preuve_publication':'hors lot','inclut_moteur':False,'cam_mic':False,'audio_prive':False,'ancienne_publication':'90d9b25c48af3f7fe80a667f4b6928943fcac2ff ; r1, non modifiée'})
 pieces={f.relative_to(p).as_posix():f for f in sorted(p.rglob('*')) if f.is_file() and f.name not in ('manifest.json','SHA256SUMS')}
 fragments=set(f'#{i}' for i in range(1,13))|set(f'#seul-{i}' for i in range(1,13))|{'#fiche','#essai','#resultat','#credits','#accueil','#planche'}
 for n,f in pieces.items():
  if not n.endswith('.md'):continue
  for l in re.findall(r'\]\(([^)\s]+)\)',f.read_text(encoding='utf-8')):
   u=urlsplit(l)
   if u.scheme or u.netloc:continue
   target=(f.parent/unquote(u.path)).resolve() if u.path else f
   assert target.is_relative_to(p) and (target.exists() or target in {p/'manifest.json',p/'SHA256SUMS'}),(n,l)
   if target==p/'index.html' and u.fragment:assert '#'+u.fragment in fragments,(n,l)
 manifest={'revision':'r2','statut':'lot de revue ; publication attestée séparément','fiche':'formulaire/Fiche-questions-T3.md','entree':'index.html','planche':'capture/planche-12-ecrans.jpg','master_sha256':media['sha256_master'],'fichiers':{n:{'sha256':sha(f),'octets':f.stat().st_size} for n,f in pieces.items()}}
 write(p/'manifest.json',manifest)
 hashes={n:v['sha256'] for n,v in manifest['fichiers'].items()}|{'manifest.json':sha(p/'manifest.json')}
 (p/'SHA256SUMS').write_text(''.join(f'{v}  {n}\n' for n,v in sorted(hashes.items())),encoding='utf-8')
 print(f'{len(pieces)+2} pièces ; SHA du manifeste {hashes["manifest.json"]}')

if __name__=='__main__':
 a=ArgumentParser(description=__doc__);a.add_argument('lot',type=Path);seal(a.parse_args().lot)
