"""Contrat T1 coiffure : les 4 prises, le plan image et le cas de test sont liés."""
from __future__ import annotations
import hashlib, json, os, re, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'ingenierie'
CASE=HERE/'cas-test.json'
PLAN=HERE/'plan.json'
CUT_ORDER=('split_slide','iris_vert','cut_geste','cut_geste','match_outil','cut_geste','iris_vert','match_profil','ui_push','cut_geste','rail_vert')
CUT_RANGES={'split_slide':range(8,25),'iris_vert':range(8,21,2),'ui_push':range(8,25)}
STAGES=('hook','offer','cut','cut_close','cut_alt','detail','detail_close','result','result_close','booking','action','lockup')
PRISERIE=('S1','S1','S2','S2','S2','S3','S3','S4','S4','S4','S4','S4')

def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,data):
 Path(p).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def ffmpeg():
 if os.environ.get('FFMPEG'):return os.environ['FFMPEG']
 if shutil.which('ffmpeg'):return shutil.which('ffmpeg')
 try:
  import imageio_ffmpeg
  return imageio_ffmpeg.get_ffmpeg_exe()
 except ImportError: raise SystemExit('Installer FFmpeg ou définir FFMPEG.')

def require(x,msg):
 if not x:raise ValueError(msg)

def validate(case,plan):
 require(case['schema']=='vv.coiffure.case/1.0' and plan['schema']=='vv.coiffure.plan/1.0','Schéma incompatible')
 require(plan['fixture']=='cas-test.json' and plan['spec_sources']['write_back'] is False,'La base T1 est en lecture seule')
 require(case['mode']=='demo','Cette fixture n’est pas un compte professionnel')
 o=case['sortie']; require((o['largeur'],o['hauteur'],o['fps'],o['frames'],o['audio'])==(720,1280,30,900,False),'Contrat vidéo T1 muet invalide')
 d=case['display']; bounds={'salon':30,'service':26,'benefice':36,'devise':5,'ville':24,'pays':20,'contact':28,'cta':29,'indication':27,'condition':34}
 for k,m in bounds.items(): require(isinstance(d[k],str) and 1<=len(d[k].strip())<=m and not re.search(r'[<>\x00-\x1f]',d[k]),f'Libellé invalide : {k}')
 require(type(d['prix'])==int and 1<=d['prix']<=999999,'Prix démo illisible ou non numérique')
 require(d['route']=='reservation.html' and 'fictive' in d['condition'].lower(),'La réservation démo doit rester locale et fictive')
 sc=case['scenes']; require([v['n'] for v in sc]==[1,2,3,4],'Exactement quatre prises ordonnées')
 for s in sc:
  require(s['id']==f'S{s["n"]}' and s['total']==4 and s['media']==f'{s["id"]}.mp4','Affectation écrans/prises invalide')
  require(s['secondes'] in range(5,11) and all(s[k] for k in ('titre','consigne','a_filmer','a_eviter','exemple','question_relecture')),'Fiche incomplète')
  st=s['stock']; require(bool(re.fullmatch(r'[a-f0-9]{64}',st['sha256'])) and st['cdn'].startswith('https://videos.pexels.com/video-files/'),'Source stock non verrouillée')
 require(len({s['stock']['id'] for s in sc})==4,'La fixture a quatre rushs distincts')
 div={s['id']:s['secondes']*o['fps'] for s in sc}
 shots=plan['shots']; cs=plan['cuts']; cursor=0
 require(len(shots)==12 and len(cs)==11,'Le plan de ce pilote comprend 12 plans et 11 raccords')
 require(tuple(dict.fromkeys(p['scene'] for p in shots))==tuple(div),'Ordre des quatre prises invalide')
 require(tuple(p['stage'] for p in shots)==STAGES and tuple(p['scene'] for p in shots)==PRISERIE,'Phases commerciales non liées aux quatre prises')
 design=plan['design']; motion=design['motion']
 require(design['badge_from_stage']=='cut' and design['badge_to_stage']=='lockup','Badge non aligné sur le geste et le carton')
 require(type(motion['hook_ease'])==int and 1<=motion['hook_ease']<=shots[0]['out'] and 0<motion['booking_select_at']<1,'Accroche ou sélection non bornée')
 require(len(motion['iris_center'])==2 and 0<=motion['iris_center'][0]<o['largeur'] and 0<=motion['iris_center'][1]<o['hauteur'],'Centre iris hors image')
 for j,s in enumerate(shots):
  require(s['id']==f'P{j+1:02d}' and s['in']==cursor<s['out'],'Trou ou chevauchement dans le montage')
  require(0<=s['src'] and s['src']+int((s['out']-s['in']-1)*s['speed'])<div[s['scene']],'Fenêtre hors de la prise')
  require(0<s['speed']<=1.25 and all(1<=q<=1.35 for q in s['zoom']) and all(0<=q<=1 for q in s['anchor']),'Mouvement hors tolérance')
  if j:
   c=cs[j-1]; require(c['at']==s['in'] and c['id']==CUT_ORDER[j-1] and type(c['frames'])==int and c['frames'] in CUT_RANGES.get(c['id'],(0,)),'Raccord non paramétré')
   if c['id']=='iris_vert':
    require(c['frames']//2<=min(s['out']-s['in'],shots[j-1]['out']-shots[j-1]['in']),'Iris trop long pour le raccord')
   else:
    require(c['frames']<s['out']-s['in'],'Transition plus longue que le plan')
  cursor=s['out']
 require(cursor==o['frames'] and (o['frames']-shots[-1]['in'])/o['fps']>=3.3,'Durée finale et lecture CTA non garanties')
 require(sum(c['id']=='iris_vert' for c in cs)==2 and not plan['audio']['enabled'],'Deux iris et aucune piste audio pour ce test')
 return case,plan

def compile_ui(case,plan):
 view={k:v for k,v in case.items() if k!='schema'}
 view['scenes']=[{k:v for k,v in s.items() if k not in ['stock']} for s in case['scenes']]
 view['plan']={"name":plan['name'],"duration":case['sortie']['frames']/case['sortie']['fps'],"prepared":True}
 (ROOT/'cas-demo.js').write_text('/* Généré par ingenierie/build_prises.py ; ne pas éditer. */\nwindow.CONSIGNES_T1 = '+json.dumps(view,ensure_ascii=False,indent=2).replace('</','<\\/')+';\n',encoding='utf-8')
