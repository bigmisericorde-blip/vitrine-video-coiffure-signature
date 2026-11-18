"""Recette navigateur de la maquette : parcours séquentiel jusqu’au CTA (Playwright)."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from core import ROOT,HERE,CASE,load,save
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8080/');p.add_argument('--captures',type=Path);p.add_argument('--refresh-gallery',action='store_true');p.add_argument('--local',action='store_true',help='Serveur privé éphémère pour la recette');a=p.parse_args();u=a.url.rstrip('/')+'/';case=load(CASE);q='?test='+case['id'];checks=[];errors=[]
if a.local:
 from functools import partial
 from threading import Thread
 from http.server import ThreadingHTTPServer
 from serve import Handler
 class Quiet(Handler):
  def log_message(self,*args):pass
 srv=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT))); Thread(target=srv.serve_forever,daemon=True).start();u=f'http://127.0.0.1:{srv.server_port}/'
def report(x):checks.append(x);print('✓',x,flush=True)
def snap(page,name):
 if a.captures:a.captures.mkdir(exist_ok=True,parents=True);page.screenshot(path=str(a.captures/(name+'.png')),animations='disabled')
with sync_playwright() as pw:
 browser=pw.chromium.launch(args=['--no-sandbox','--autoplay-policy=no-user-gesture-required']);page=browser.new_page(viewport={'width':360,'height':780},device_scale_factor=1)
 page.on('pageerror',lambda err:errors.append(str(err)))
 page.on('response',lambda r:errors.append(f'{r.status} {r.url}') if r.status>=400 else None)
 page.goto(u+'simulation.html');expect(page.locator('#testCurtain')).to_be_visible();report('Accès direct sans identifiant : retour vers la fiche')
 gallery=browser.new_page(viewport={'width':320,'height':568});gallery.on('pageerror',lambda err:errors.append(str(err)))
 gallery.goto(u+'ecrans.html');expect(gallery.locator('[data-ecran]')).to_have_count(12);expect(gallery.locator('#screenLabel')).to_be_in_viewport();expect(gallery.locator('#screenNext')).to_be_in_viewport()
 assert gallery.evaluate('document.documentElement.scrollWidth<=innerWidth')
 for n in range(1,13):
  gallery.select_option('#screenSelect',str(n));stage=(n-1)%3;scene=case['scenes'][(n-1)//3]
  expect(gallery.locator('#screenLabel')).to_contain_text(f'Écran {n}/12')
  expect(gallery.locator(f'[data-ecran="{n}"]')).to_have_attribute('aria-current','true')
  expect(gallery.locator('#screenPreview')).to_have_attribute('src',f'livrables/12-ecrans/{n:02d}.webp?v=2');gallery.wait_for_function('document.getElementById("screenPreview").naturalWidth>0')
  if stage!=1:expect(gallery.locator('#screenText')).to_have_text(scene['consigne' if stage==0 else 'question_relecture'])
 expect(gallery.locator('#screenNext')).to_be_disabled();gallery.locator('#screenPrev').click();expect(gallery.locator('#screenLabel')).to_contain_text('Écran 11/12');gallery.go_back();expect(gallery.locator('#screenLabel')).to_contain_text('Écran 12/12')
 gallery.goto(u+'ecrans.html#7');expect(gallery.locator('#screenSelect')).to_have_value('7');gallery.close();report('Les 12 aperçus lisibles à 320 px : choix direct, précédent/suivant et URL partageable')
 direct=browser.new_page(viewport={'width':320,'height':568});direct.on('pageerror',lambda err:errors.append(str(err)))
 def direct_screen(n):
  stage=(n-1)%3;scene=case['scenes'][(n-1)//3];direct.goto(u+'simulation.html'+q+f'&ecran={n}')
  expect(direct.locator('#sceneTitle')).to_have_text(scene['titre'])
  if stage==0:expect(direct.locator('#sheet')).to_have_class('sheet');expect(direct.locator('#cta')).to_be_in_viewport();expect(direct.locator('#cta')).to_be_disabled()
  if stage==1:expect(direct.locator('#rec')).to_have_class('rec on');expect(direct.locator('#barFill')).to_have_attribute('style','width: 40%;')
  if stage==2:expect(direct.locator('#review')).to_have_class('review on');expect(direct.locator('#reviewQuestion')).to_have_text(scene['question_relecture']);expect(direct.locator('#next')).to_be_in_viewport();expect(direct.locator('#next')).to_be_disabled()
  direct.wait_for_function('(id)=>{const v=document.getElementById(id);return v.readyState>=2&&!v.seeking;}',arg='replay' if stage==2 else 'cam')
  expect(direct.locator('#mediaFeedback')).to_be_hidden();assert direct.evaluate('window.__demo.validations().length')==0
 for n in range(1,13):direct_screen(n)
 report('Les 12 écrans réels ouverts un par un : prise correcte, image prête et contrôles visibles sur petit écran')
 broken=browser.new_page(viewport={'width':320,'height':568});broken.route('**/media/S1.mp4',lambda r:r.abort());broken.goto(u+'simulation.html'+q);broken.locator('#cta').click()
 expect(broken.locator('#mediaFeedback')).to_be_visible();expect(broken.locator('#mediaRetry')).to_be_visible();expect(broken.locator('#chronoVal')).to_have_text('0:00');expect(broken.locator('#rec')).to_have_class('rec on');assert broken.evaluate('window.__demo.validations().length')==0
 broken.unroute('**/media/S1.mp4');broken.locator('#mediaRetry').click();broken.wait_for_function('document.getElementById("cam").currentTime>0.1')
 expect(broken.locator('#mediaFeedback')).to_be_hidden();broken.close();report('Vidéo bloquée : chrono à zéro, aucune validation ; Réessayer relance la bonne prise')
 page.goto(u);expect(page.locator('#caseLabel')).to_contain_text(case['id']);expect(page.locator('.list li')).to_have_count(4);expect(page.locator('#startTest')).to_be_disabled();expect(page.locator('#service')).to_have_value(case['display']['service']);snap(page,'00-cas')
 expect(page.locator('[name=resultatChoix][value=profil]')).to_be_checked();page.fill('#service','Tresses');page.check('[name=resultatChoix][value=autre]');expect(page.locator('#resultatAutre')).to_be_visible();page.check('[name=resultatChoix][value=detail]');expect(page.locator('#resultatAutre')).to_be_hidden();page.select_option('#action','Rien pour le moment');expect(page.locator('#contact')).to_be_hidden();page.fill('#prix','');page.check('#checkedCase');page.locator('#startTest').click();expect(page).to_have_url(u+'simulation.html'+q+'&fiche=1');expect(page.locator('#caseContext')).to_have_text('Ton travail : Tresses');report('Question 5 : un choix par défaut et des exemples ; tresses / détail choisissables sans taper ni prix ni résultat')
 for i,s in enumerate(case['scenes'],1):
  expect(page.locator('#sceneCounter')).to_have_text(f'SCÈNE {i}/4');expect(page.locator('#sceneTitle')).to_have_text(s['titre']);expect(page.locator('#durationLabel')).to_have_text(f'{s["secondes"]} secondes');expect(page.locator('#caseContext')).to_have_text('À la fin : Un détail : une tresse, une boucle ou une mèche.' if i==4 else 'Ton travail : Tresses')
  assert page.evaluate('document.querySelector(".voice").compareDocumentPosition(document.querySelector(".exemple")) & 4')
  page.locator('#exempleText').scroll_into_view_if_needed();expect(page.locator('#exempleText')).to_contain_text(s['exemple']);expect(page.locator('#cta')).to_be_in_viewport();snap(page,f'{s["id"]}-A-fiche-bas')
  page.locator('#sheetBody').evaluate('p=>p.scrollTop=0');snap(page,f'{s["id"]}-A-consigne');page.locator('#cta').click();expect(page.locator('#rec')).to_have_class('rec on');expect(page.locator('#sheet')).to_have_class('sheet hidden');assert page.locator('#app').get_attribute('data-prise')==s['id'];page.wait_for_function('document.getElementById("cam").currentTime>0.1');snap(page,f'{s["id"]}-B-enregistrement')
  expect(page.locator('#review')).to_have_class('review on',timeout=11000);expect(page.locator('#reviewLabel')).to_have_text(f'PRISE {i} · 0:{s["secondes"]:02d}');expect(page.locator('#reviewQuestion')).to_have_text(s['question_relecture']);page.wait_for_function('document.getElementById("replay").readyState>=2');snap(page,f'{s["id"]}-C-validation')
  if i==2:
   page.locator('#redo').click();expect(page.locator('#sheet')).to_have_class('sheet');assert page.evaluate('window.__demo.validations().length')==1
   page.locator('#cta').click();expect(page.locator('#review')).to_have_class('review on',timeout=11000)
  assert abs(page.locator('#replay').evaluate('v=>v.duration')-s['secondes'])<.04
  expect(page.locator('#next')).to_have_text('VOIR MON MONTAGE' if i==4 else 'SCÈNE SUIVANTE');page.locator('#next').click();report(f'{s["id"]} : ordre des textes, source {s["media"]}, chrono automatique, révision, validation')
 expect(page.locator('#panelMontage')).to_have_class('panel on');assert page.evaluate('window.__demo.validations()')==['S1','S2','S3','S4'];snap(page,'09-montage');expect(page.locator('#montageGo')).to_be_enabled(timeout=12000)
 # Écouter les événements AVANT le clic ; ne pas chercher dans la vidéo pour la recette.
 page.evaluate('''() => {
   const v = document.getElementById('ad');
   const stats = window.vvPlayback = {ended:false, frameCount:0, badJumps:0, last:-1, milestones:[], starts:0, seek:0, errs:[]};
   for (const k of ['error','stalled','abort']) v.addEventListener(k, () => stats.errs.push(k));
   v.addEventListener('playing', () => { stats.starts++; stats.startedAt??=performance.now(); });
   v.addEventListener('seeking',()=>{ if (v.currentTime > .2) stats.seek++; });
   v.addEventListener('ended', () => {stats.ended=true; stats.elapsed=(performance.now()-stats.startedAt)/1000; stats.frameTiming=v.getVideoPlaybackQuality().toJSON?.()??{};});
   const visit = (_,m) => {
     if (stats.last >= 0 && m.mediaTime-stats.last>.22) stats.badJumps++;
     stats.frameCount++;
     stats.last=m.mediaTime;
     for (const t of [1.4,5,11,15.8,20.83,24,26.4,29.8]) if (m.mediaTime>=t && !stats.milestones.includes(t)) stats.milestones.push(t);
     if(!v.ended) v.requestVideoFrameCallback(visit);
   };
   v.requestVideoFrameCallback(visit);
 }''')
 page.locator('#montageGo').click();expect(page.locator('#adwrap')).to_have_class('adwrap on');page.wait_for_function('document.getElementById("ad").currentTime>0.4');elt=page.locator('#ad');assert abs(elt.evaluate('v=>v.duration')-30)<.01
 expect(page.locator('#caCta')).to_be_in_viewport();expect(page.locator('#demoFab')).to_be_hidden()
 page.wait_for_function('document.getElementById("ad").currentTime>27.4');snap(page,'10-publicite')
 expect(page.locator('#panelEnd')).to_have_class('panel on',timeout=10000);snap(page,'11-fin');playback=page.evaluate('window.vvPlayback');assert playback['ended'] and playback['seek']==0 and playback['last']>=29.8 and len(playback['milestones'])==8 and playback['frameCount']>=750 and 29<=playback['elapsed']<=34 and playback['badJumps']<=3 and not playback['errs'],playback
 report('Montage débloqué par S1–S4 ; lecture continue 30 s, sans saut demandé, puis écran de fin')
 expect(page.locator('#endCta')).to_have_text(case['display']['cta']);expect(page.locator('#endCta')).to_have_attribute('href',case['display']['route']+q)
 # Tester le CTA après lecture sans perdre l’étape Fin, puis le redémarrage.
 with page.context.expect_page() as clicked:
  page.locator('#endCta').click(modifiers=['Control'])
 detail=clicked.value;expect(detail).to_have_url(u+case['display']['route']+q);expect(detail.locator('#reserveData')).to_contain_text(case['display']['service']);detail.get_by_role('radio',name='11:30').click();detail.locator('#selectSlot').click();expect(detail.locator('#result')).to_contain_text('Aucun rendez-vous réel');snap(detail,'12-cta');detail.close();report('Clic du CTA → prestation identique → choix d’un horaire fictif')
 page.locator('#restart').click();expect(page.locator('#sceneCounter')).to_have_text('SCÈNE 1/4');assert page.evaluate('window.__demo.validations().length')==0;report('RECOMMENCER : retour S1 et validation remise à zéro')
 wide=browser.new_page(viewport={'width':430,'height':932});wide.goto(u+'simulation.html'+q);wide.evaluate('window.__demo.showCard(3)');expect(wide.locator('#sceneCounter')).to_have_text('SCÈNE 4/4');wide.locator('#exempleText').scroll_into_view_if_needed();expect(wide.locator('#cta')).to_be_in_viewport();snap(wide,'13-fiche-430');report('Lisibilité et bouton non masqué à 360 et 430 px')
 if a.refresh_gallery:
  from PIL import Image
  from io import BytesIO
  direct.set_viewport_size({'width':360,'height':780})
  for n in range(1,13):
   direct_screen(n);direct.evaluate('document.fonts.ready')
   with Image.open(BytesIO(direct.screenshot(animations='disabled'))) as im:im.convert('RGB').save(ROOT/'livrables'/'12-ecrans'/f'{n:02d}.webp',format='WEBP',quality=83,method=4)
 assert not errors,errors; browser.close()
save(HERE/'recette-parcours.json',{'cas':case['id'],'resultat':'PASS','navigateur':'Chromium headless','vue_px':[320,360,430],'checks':checks,'lecture_complete':playback,'erreurs':errors,'version':'navigation et questions v2','périmètre':'Maquette web ; aucune validation Android ni réservation réelle.'})
