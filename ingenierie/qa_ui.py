"""Recette navigateur de la maquette : parcours séquentiel jusqu’au CTA (Playwright)."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from core import ROOT,HERE,CASE,load,save
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8080/');p.add_argument('--captures',type=Path);p.add_argument('--local',action='store_true',help='Serveur privé éphémère pour la recette');a=p.parse_args();u=a.url.rstrip('/')+'/';case=load(CASE);q='?test='+case['id'];checks=[];errors=[]
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
 gallery=browser.new_page(viewport={'width':360,'height':780});gallery.on('pageerror',lambda err:errors.append(str(err)))
 gallery.goto(u+'ecrans.html');expect(gallery.locator('[data-ecran]')).to_have_count(12);f=gallery.frame_locator('#screenPreview')
 for n in range(1,13):
  gallery.locator(f'[data-ecran="{n}"]').click();stage=(n-1)%3;scene=case['scenes'][(n-1)//3]
  expect(gallery.locator('#screenLabel')).to_contain_text(f'Écran {n}/12');expect(f.locator('#sceneTitle')).to_have_text(scene['titre'])
  if stage==0:expect(f.locator('#sheet')).to_have_class('sheet');expect(f.locator('#consigne')).to_have_text(scene['consigne']);expect(f.locator('#cta')).to_be_disabled()
  if stage==1:expect(f.locator('#rec')).to_have_class('rec on');expect(f.locator('#barFill')).to_have_attribute('style','width: 40%;')
  if stage==2:expect(f.locator('#review')).to_have_class('review on');expect(f.locator('#reviewQuestion')).to_have_text(scene['question_relecture']);expect(f.locator('#next')).to_be_disabled()
  assert f.locator('#app').evaluate('()=>window.__demo.validations().length')==0
 gallery.close();report('Une page donne accès aux 12 écrans A/B/C, en aperçu sans validation')
 page.goto(u);expect(page.locator('#caseLabel')).to_contain_text(case['id']);expect(page.locator('.list li')).to_have_count(4);expect(page.locator('#startTest')).to_be_disabled();expect(page.locator('#service')).to_have_value(case['display']['service']);snap(page,'00-cas')
 page.fill('#service','Tresses');page.fill('#resultat','Tresses finies de côté');page.fill('#prix','');page.check('#checkedCase');page.locator('#startTest').click();expect(page).to_have_url(u+'simulation.html'+q+'&fiche=1');expect(page.locator('#caseContext')).to_have_text('Ton travail : Tresses');report('Coupe + barbe préremplie → même fiche avec Tresses et prix vide → contexte lié sans changer les prises')
 for i,s in enumerate(case['scenes'],1):
  expect(page.locator('#sceneCounter')).to_have_text(f'SCÈNE {i}/4');expect(page.locator('#sceneTitle')).to_have_text(s['titre']);expect(page.locator('#durationLabel')).to_have_text(f'{s["secondes"]} secondes');expect(page.locator('#caseContext')).to_have_text('À la fin : Tresses finies de côté' if i==4 else 'Ton travail : Tresses')
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
 assert not errors,errors; browser.close()
save(HERE/'recette-parcours.json',{'cas':case['id'],'resultat':'PASS','navigateur':'Chromium headless','vue_px':[360,430],'checks':checks,'lecture_complete':playback,'erreurs':errors,'périmètre':'Maquette web ; aucune validation Android ni réservation réelle.'})
