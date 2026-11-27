#!/usr/bin/env python3
"""Recette locale des profils métier et d'un export onglerie sur mires, jamais des images réelles."""
import argparse,importlib.util,json,sys
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import expect,sync_playwright
p=argparse.ArgumentParser();p.add_argument('--racine',type=Path,required=True);p.add_argument('--sortie',type=Path,required=True);a=p.parse_args();root=a.racine.resolve();out=a.sortie.resolve();out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(root/'tools'));spec=importlib.util.spec_from_file_location('qa',root/'tools/qa-production.py');qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
with ThreadingHTTPServer(('127.0.0.1',0),partial(qa.Quiet,directory=str(root))) as server,sync_playwright() as pw:
 Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
 b=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--disable-dev-shm-usage','--autoplay-policy=no-user-gesture-required']);ctx=b.new_context(viewport={'width':390,'height':820},accept_downloads=True);ctx.set_default_timeout(10000);page=ctx.new_page();errs=[];extern=[];posts=[]
 page.on('pageerror',lambda e:errs.append(str(e)))
 def gate(route):
  u=route.request.url
  if route.request.method not in ('GET','HEAD'):posts.append(route.request.method);route.abort()
  elif u.startswith(('blob:','data:',url+'/')):route.continue_()
  else:extern.append(u);route.abort()
 ctx.route('**/*',gate)
 page.goto(url+'/');qa.wait_ready(page);profiles=page.evaluate('VVBeaute.profiles.map(p=>({id:p.id,label:p.label,examples:p.services}))');assert len(profiles)==8
 summary=[]
 for row in profiles:
  id=row['id'];page.goto(url+'/');qa.wait_ready(page);page.locator('#metier').select_option(id);page.locator('#sample').click();expect(page.locator('#source')).to_have_value('demo');expect(page.locator('#sampleNote')).to_contain_text('clips graphiques fictifs');page.locator('#startTest').click();page.wait_for_url('**/simulation.html?fiche=*');qa.wait_ready(page)
  for i in range(4):
   scene=page.evaluate('(i)=>VVBeaute.profiles.find(p=>p.id===document.querySelector("#app").dataset.metier)?.aFilmer[i]',i) if False else None
   if i:
    # Galerie d'aperçu en lecture seule : mêmes guides, avec le ticket courant.
    ticket=page.url.split('fiche=')[1].split('&')[0];page.goto(f'{url}/simulation.html?fiche={ticket}&ecran={i*3+1}');qa.wait_ready(page)
   text=page.locator('#listFilm').inner_text();assert text and len(text)>40
   expected=page.evaluate('([id,i])=>VVBeaute.get(id).aFilmer[i]',[id,i]);assert expected in text,(id,i,text)
  summary.append({'metier':id,'guides_confirmes':4,'mires_explicites':True})
 # Galerie manucure complète, 12 états, sans fiche pour vérifier la propagation du profil.
 for n in range(1,13):
  page.goto(f'{url}/simulation.html?metier=manucure&ecran={n}');qa.wait_ready(page);expect(page.locator('#app')).to_have_attribute('data-state','ABC'[(n-1)%3]);expect(page.locator('#app')).to_have_attribute('data-prise',f'S{(n-1)//3+1}')
  expected=page.evaluate('(i)=>VVBeaute.get("manucure").aFilmer[i]',(n-1)//3);assert expected in page.locator('#listFilm').text_content()
 page.goto(url+'/ecrans.html?metier=manucure#12');qa.wait_ready(page);assert page.locator('#screenList a').count()==12;assert 'metier=manucure' in page.locator('#screenAlone').get_attribute('href')
 # Export client réaliste au niveau contrats uniquement, images de test graphiques.
 ex=dict(qa.EXAMPLES[0]['answers'],service='Pose de vernis',geste='Appliquer le vernis',preuve='Le bord net du vernis',accroche='',salon='',ville='',prix='',canal='aucun',contact='',contactConfirme=False)
 qa.fill(page,url,ex,start=False);page.locator('#metier').select_option('manucure');page.locator('#startTest').click();page.wait_for_url('**/simulation.html?fiche=*');qa.wait_ready(page);assert 'ongles' in page.locator('#listFilm').inner_text().lower()
 qa.captures(page,root/'fixtures/media');film=out/'Recette-onglerie-mires.mp4';result=qa.download(page,film,4,['Pose de vernis']);result['pixels']=qa.check_pixels(page,url,film,ex,result['variant'],['gesture','proof','service'],onglerie=True);print('Export onglerie sur mires PASS',flush=True)
 assert not errs and not extern and not posts,(errs,extern,posts)
 evidence={'profils':summary,'ecrans_manucure':12,'export_sur_mires':result,'erreurs_js':errs,'requetes_externes':extern,'posts':posts,'appareil_physique':False,'rushs_reels':False,'validation_visuelle_humaine':False,'voix_off':False}
 (out/'Recette-profils.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n');b.close();server.shutdown();print('Profils et recette PASS',flush=True)
