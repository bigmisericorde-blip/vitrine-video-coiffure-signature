#!/usr/bin/env python3
"""Contrôle local T3 r2, y compris dans un aperçu HTML sans réseau et à origine opaque."""
from argparse import ArgumentParser
from base64 import b64decode, b64encode
import re
from functools import partial
from hashlib import sha256
from html import escape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from time import monotonic
import json

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import expect, sync_playwright

SIZES={'mobile':(390,844),'bureau':(1260,930)}
OUTER={'.top':['display','border-bottom-color'],'.screen-layout-v2':['display','grid-template-areas','grid-template-columns'],'.headline':['font-family','font-size','font-weight','letter-spacing'],'.screen-view.card':['background-color','border-radius','padding','position'],'#screenSelect':['background-color','border-radius','height','font-size'],'#screenLive':['height','width','border-radius','pointer-events'],'.screen-row':['display','column-gap'],'#resultat':['background-color','border-radius']}
INNER={'.sheet':['background-color','border-top-left-radius','max-height','backdrop-filter'],'.scene-title':['font-family','font-size','font-weight'],'.duration':['background-color','border-top-color','color'],'.cta':['background-color','height','border-radius'],'.chrono':['background-color','position','border-radius','color'],'.dot':['background-color'],'.bar':['position','background-color'],'.review':['background-color','bottom','padding'],'.review .btn.primary':['background-color','font-family','border-radius'],'#app>video':['object-fit','background-color']}

class Static(SimpleHTTPRequestHandler):
 def log_message(self,*_):pass
 def copyfile(self,src,out):
  try:super().copyfile(src,out)
  except (BrokenPipeError,ConnectionResetError):pass

def metrics(loc,criteria):return {q:loc.locator(q).first.evaluate('(e,k)=>Object.fromEntries(k.map(n=>[n,getComputedStyle(e).getPropertyValue(n)]))',keys) for q,keys in criteria.items()}

def read(player):
 return player.evaluate('v=>({t:v.currentTime,d:v.duration,playing:!v.paused,ready:v.readyState,w:v.videoWidth,h:v.videoHeight,muted:v.muted,src:v.currentSrc,error:v.error?.message})')

def wait_media(player,check):
 end=monotonic()+7;state={}
 while monotonic()<end:
  state=read(player)
  if state['error']:raise AssertionError(state)
  if state['ready']>=2 and check(state):return state
 raise AssertionError(state)

def clip_hash(player):
 # Même test sous origine opaque, sans API crypto privilégiée. FFmpeg a aussi comparé au master.
 encoded=player.evaluate('''async v=>{const bin=new Uint8Array(await (await fetch(v.currentSrc)).arrayBuffer());
   if(bin.toBase64)return bin.toBase64();let tmp='';for(let i=0;i<bin.length;i+=32768)tmp+=String.fromCharCode(...bin.subarray(i,i+32768));return btoa(tmp);}''')
 return sha256(b64decode(encoded)).hexdigest()

def ready(doc,state,p):
 expect(doc.locator('html')).to_have_attribute('data-ready','yes',timeout=8000)
 expect(doc.locator('#app')).to_have_attribute('data-prise',p['id'])
 expect(doc.locator('#app')).to_have_attribute('data-state',state)
 doc.locator('body').evaluate('()=>document.fonts.ready.then(()=>true)')

def capture_state(doc,k,p,media,hash_it):
 ready(doc,k,p);assert doc.locator('body').evaluate('document.documentElement.scrollWidth<=innerWidth+1')
 assert doc.locator('body').evaluate('window.__capture()').get('accepted')==[]
 v=doc.locator('#replay' if k=='C' else '#cam')
 s=wait_media(v,lambda st: (not st['playing'] and abs(st['t']-p['freeze'])<.095) if k=='A' else st['playing'] and .20<st['t']<2)
 assert (s['w'],s['h'])==(360,640) and s['muted'] and abs(s['d']-p['duree'])<.004,(p['id'],s)
 if hash_it:assert clip_hash(v)==media['sha256'],(p['id'],k)
 if k=='A':
  assert doc.locator('#listFilm li').count()==2;expect(doc.locator('#durationLabel')).to_have_text(f"{p['duree_filmer_s']} secondes");expect(doc.locator('#listAvoid li')).to_contain_text(p['a_eviter']);expect(doc.locator('#cta')).to_be_disabled();expect(doc.locator('#sheet')).to_be_visible()
 elif k=='B':
  expect(doc.locator('#rec')).to_have_class('rec on');expect(doc.locator('#cancelCapture')).to_be_hidden(); assert float(doc.locator('#barFill').evaluate('el=>parseFloat(el.style.width)'))>0
 else:
  expect(doc.locator('#reviewQuestion')).to_have_text(p['question']);expect(doc.locator('#reviewMode')).to_contain_text('aucune prise validée');expect(doc.locator('#redo')).to_be_disabled();expect(doc.locator('#next')).to_be_disabled();expect(doc.locator('.review')).to_be_visible()
 assert doc.locator('input[type=file]').count()==0
 return s

def review_page(b,url,o,g,media,size,wh,lens):
 ctx=b.new_context(viewport={'width':wh[0],'height':wh[1]},accept_downloads=True,service_workers='block');p=ctx.new_page();errors=[];foreign=[]
 p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:foreign.append(r.url) if r.url.startswith(('http:','https:')) and not r.url.startswith(url.split('/index.html')[0]+'/') else None)
 p.set_default_timeout(4200);assert p.goto(url+'#1').ok; expect(p.locator('html')).to_have_attribute('data-ready','yes');p.evaluate('document.fonts.ready.then(()=>true)'); assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
 assert p.locator('#screenList a').count()==12 and p.locator('#screenSelect option').count()==12
 expect(p.locator('#screenPrev')).to_be_disabled();p.locator('#screenNext').click();expect(p.locator('#screenLabel')).to_contain_text('Écran 02/12');p.locator('#screenPrev').click();expect(p.locator('#screenLabel')).to_contain_text('Écran 01/12');
 outer=metrics(p,OUTER);inner=None;shots=o/'capture/ecrans';report=[]
 if lens:assert outer==lens['t1']['outer']==lens['t2']['outer'],(size,outer)
 for n in range(1,13):
  i,j=divmod(n-1,3); shot=g['scenes'][i]; k='ABC'[j]
  if n%2==0:p.locator(f'#screenList a[href="#{n}"]').click()
  else:p.locator('#screenSelect').select_option(str(n))
  expect(p.locator('#screenLabel')).to_contain_text(f'Écran {n:02d}/12');expect(p.locator('#screenList [aria-current=step]')).to_have_attribute('href',f'#{n}')
  expect(p.locator('#screenAlone')).to_have_attribute('href',f'#seul-{n}');f=p.frame_locator('#screenLive');s=capture_state(f,k,shot,media[i],size=='mobile')
  if n==1:
   inner=metrics(f,INNER)
   if lens:assert inner==lens['t1']['inner']==lens['t2']['inner'],(size,inner)
   p.evaluate('scrollTo(0,0)');p.screenshot(path=str(o/'rapports'/f'Galerie-{size}.jpg'),type='jpeg',quality=87)
  if size=='mobile':p.locator('#screenLive').screenshot(path=str(shots/f'{n:02d}.jpg'),type='jpeg',quality=89)
  report.append({'vue':n,'prise':shot['id'],'etat':k,'duree_s':s['d'],'mode':'photo arrêtée' if k=='A' else 'lecture','validations':0})
 expect(p.locator('#screenNext')).to_be_disabled()
 # La dernière vue peut s’ouvrir seule avec son propre lien, sans valider.
 p.locator('#screenAlone').click();solo=p.frame_locator('#vv-solo-frame');capture_state(solo,'C',g['scenes'][3],media[3],False)
 expect(p.locator('#vv-back')).to_have_attribute('href','#12');p.locator('#vv-back').click();expect(p.locator('#screenLabel')).to_contain_text('Écran 12/12');
 p.locator('#jumpFilm').click();expect(p.locator('#film')).to_be_in_viewport();v=p.locator('#film');v.evaluate('v=>v.play()');assert wait_media(v,lambda s:s['t']>.2)['d']==30
 with p.expect_download() as d:p.locator('#downloadDemo').click()
 downloaded=Path(d.value.path());assert d.value.suggested_filename.endswith('mp4')
 p.locator('#return').click();expect(p.locator('#vv-fiche')).to_be_visible();assert p.locator('#vv-fiche tbody tr').count()==4 and p.evaluate('document.documentElement.scrollWidth<=innerWidth+1');p.locator('#vv-fiche .top a').click()
 p.locator('#secteur').click();expect(p.locator('#vv-accueil')).to_be_visible();p.locator('#vv-accueil .top a').click();p.locator('footer a[href="#credits"]').click();expect(p.locator('#vv-credits')).to_be_visible()
 assert errors==foreign==[],(errors,foreign)
 result={'vues':report,'css_galerie':outer,'css_prise':inner,'sha256_download_film':sha256(downloaded.read_bytes()).hexdigest(),'aucun_appel_externe':True};ctx.close();return result

def narrow_and_direct(b,url,g,media):
 c=b.new_context(viewport={'width':320,'height':640});p=c.new_page();p.set_default_timeout(4000)
 assert p.goto(url+'#seul-12').ok;f=p.frame_locator('#vv-solo-frame');capture_state(f,'C',g['scenes'][3],media[3],True)
 for n in range(1,13):
  p.goto(url+f'#seul-{n}');i,j=divmod(n-1,3);k='ABC'[j];s=g['scenes'][i];caption=p.locator('#vv-solo-label');expect(caption).to_contain_text(f'Écran {n:02d}/12')
  capture_state(f,k,s,media[i],False)
  if j==0:
   h=f.locator('#scrollHint');expect(h).to_be_visible();h.click();assert f.locator('#sheetBody').evaluate('x=>x.scrollTop')>0
 p.goto(url+'#ecran-08');expect(p.locator('#screenLabel')).to_contain_text('Écran 08/12');p.goto(url+'#resultat');expect(p.locator('#film')).to_be_in_viewport();c.close();return {'liens_seuls':12,'largeur':320,'defilement_guides':4,'ancien_lien_ecran_08':True,'acces_film_sans_garde':True}

def simulation(b,url,g):
 c=b.new_context(viewport={'width':375,'height':812});p=c.new_page();p.set_default_timeout(4500);p.goto(url+'#essai');f=p.frame_locator('#vv-solo-frame');p0=g['scenes'][0]
 ready(f,'A',p0);assert f.locator('body').evaluate('window.__capture().demo');
 f.locator('#cta').click();ready(f,'B',p0);f.locator('#cancelCapture').click();ready(f,'A',p0)
 f.locator('#cta').click();ready(f,'B',p0);f.locator('#cam').evaluate("v=>v.src='data:video/mp4;base64,AA=='");expect(f.locator('#mediaFeedback')).to_be_visible();f.locator('#mediaBack').click();ready(f,'A',p0)
 def chrono_relecture(s):
  f.locator('#cta').click();ready(f,'B',s);v=f.locator('#cam');st=wait_media(v,lambda x:x['t']>.22 and x['playing']);expect(f.locator('#app')).to_have_attribute('data-state','C',timeout=12000);expect(f.locator('#next')).to_be_enabled();
  st2=read(f.locator('#replay'));assert st2['src']==st['src'] and st2['d']==st['d'] and st2['muted'] and st2['playing'];return st['d']
 chrono_relecture(p0);f.locator('#redo').click();ready(f,'A',p0);assert f.locator('body').evaluate('window.__capture().accepted')==[]
 for i,s in enumerate(g['scenes']):
  chrono_relecture(s);assert f.locator('body').evaluate('window.__capture().accepted')==[f'S{n}' for n in range(1,i+1)];expect(f.locator('#next')).to_contain_text('GARDER');f.locator('#next').click()
 expect(p.locator('#film')).to_be_in_viewport(timeout=5000);assert p.evaluate('location.hash')=='#resultat';p.goto(url+'#essai');ready(f,'A',p0);assert f.locator('body').evaluate('window.__capture().accepted')==[]
 c.close();return {'chronos':4,'annulation_vers_meme_prise':True,'erreur_vers_meme_prise':True,'refaire_vers_meme_prise':True,'garde_explicite':4,'film_apres_quatre':True,'reouverture_sans_etat':True}

def sandbox(b,o,g,m):
 c=b.new_context(viewport={'width':390,'height':844},offline=True);p=c.new_page();p.set_default_timeout(4400);errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 h=(o/'index.html').read_text(encoding='utf-8');p.set_content('<style>html,body{margin:0}iframe{width:100vw;height:100dvh;border:0}</style><iframe sandbox="allow-scripts" allow="autoplay" srcdoc="'+escape(h,quote=True)+'"></iframe>');outer=p.frame_locator('body>iframe');f=outer.frame_locator('#screenLive');expect(outer.locator('html')).to_have_attribute('data-ready','yes');
 for n in range(1,13):
  outer.locator('#screenSelect').select_option(str(n));i,j=divmod(n-1,3);capture_state(f,'ABC'[j],g['scenes'][i],m[i],j==2)
 outer.locator('#screenAlone').click();expect(outer.locator('#vv-solo-label')).to_contain_text('Écran 12/12');capture_state(outer.frame_locator('#vv-solo-frame'),'C',g['scenes'][3],m[3],False)
 outer.locator('#vv-back').click();outer.locator('#jumpFilm').click();v=outer.locator('#film');expect(v).to_be_in_viewport();v.evaluate('v=>v.play()');assert wait_media(v,lambda s:s['t']>.2)['d']==30
 outer.locator('#vv-planche-link').click();pic=outer.locator('#vv-planche-img');expect(pic).to_be_visible();assert pic.evaluate('async i=>{await i.decode();return i.naturalWidth===1112&&i.naturalHeight===2456}');
 assert not errors,errors;c.close();return {'planche_hors_ligne':True,'vues':12,'navigation_ecran_seul_et_film':True,'film_s':30,'reseau':False,'origine_opaque':True}

def planche(o,g):
 w,h=1112,2456;img=Image.new('RGB',(w,h),'#04191b');d=ImageDraw.Draw(img)
 def font(sz,b=False):
  try:return ImageFont.truetype('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf',sz)
  except OSError:return ImageFont.load_default(size=sz)
 d.text((26,21),'T3 · SOIN DU VISAGE',font=font(15,True),fill='#bdf4d8');d.text((24,41),'Les 12 écrans.',font=font(47,True),fill='#f5faf3');d.text((28,106),'Prise par prise · la consigne, le chrono et la relecture',font=font(19),fill='#b1c9bf');
 for i,s in enumerate(g['scenes']):
  y=148+i*568;d.line((26,y,1086,y),fill='#39716a',width=2);d.text((26,y+9),f'PRISE {i+1}  ·  {s["titre"].upper()}',font=font(19,True),fill='#bdf4d8')
  for j,name in enumerate(('Consigne','Chrono','Relecture')):
   x=26+j*356;n=3*i+j+1;d.text((x,y+39),f'{n:02d}  {name}',font=font(17,True),fill='#ecfaf2')
   with Image.open(o/f'capture/ecrans/{n:02d}.jpg') as m:m.thumbnail((262,503),Image.Resampling.LANCZOS);img.paste(m,(x,y+65))
 d.text((26,2429),'Revue r2 · Extraits T3 muets · Captures réelles du parcours de consultation',font=font(14),fill='#b1c9bf');img.save(o/'capture/planche-12-ecrans.jpg',quality=86,optimize=True)

def main(args):
 o=args.lot.resolve();(o/'capture/ecrans').mkdir(exist_ok=True);g=json.loads((o/'capture/guide.json').read_text());meta=json.loads((o/'rapports/Media-integre.json').read_text());m=meta['derivees']['extraits'];ref=json.loads(args.reference.read_text()) if args.reference else None
 srv=ThreadingHTTPServer(('127.0.0.1',0),partial(Static,directory=o));Thread(target=srv.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{srv.server_port}/index.html'
 result={}
 def write_report():
  (o/'rapports/Recette-r2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 def add_planche():
  planche(o,g);f=o/'index.html';content=f.read_text(encoding='utf-8');raw=b64encode((o/'capture/planche-12-ecrans.jpg').read_bytes()).decode('ascii');new,n=re.subn(r'(id="vv-planche-data">)(?:null|"[A-Za-z0-9+/=]+")(?=</script>)',lambda m:m[1]+json.dumps(raw),content);assert n==1;tmp=f.with_suffix('.tmp');tmp.write_text(new,encoding='utf-8');tmp.replace(f)
 try:
  with sync_playwright() as p:
   b=p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage','--mute-audio']);result['chromium']=b.version
   for size,wh in SIZES.items():
    result[size]=review_page(b,url,o,g,m,size,wh,ref[size] if ref else None);assert result[size]['sha256_download_film']==meta['derivees']['film']['sha256'];print(f'{size} : 12 écrans, styles, navigation et film OK.',flush=True);write_report()
   add_planche()
   result['acces_directs']=narrow_and_direct(b,url,g,m);print('12 accès directs à 320 px, défilement et film OK.',flush=True);write_report()
   result['essai']=simulation(b,url,g);print('Essai séparé : annuler, erreur, reprendre, lire et garder OK.',flush=True);write_report()
   result['hors_ligne_apercu']=sandbox(b,o,g,m);print('Aperçu Arena reproduit : 12 vues et film hors ligne OK.',flush=True);b.close()
 finally:srv.shutdown()
 result['comparaison_styles_T1_T2']=bool(ref);write_report()

if __name__=='__main__':
 parser=ArgumentParser(description=__doc__);parser.add_argument('lot',type=Path);parser.add_argument('--reference',type=Path);main(parser.parse_args())
