#!/usr/bin/env python3
"""Recette d'atelier T4 12 états + capture simulée Chromium + rendu depuis ces 4 vidéos.
Jamais un test d'appareil physique ni un test de prise réelle.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import hashlib,json,time,urllib.request,urllib.error,subprocess
from fiche_t4 import vers_image
from playwright.sync_api import sync_playwright
from atelier_local import App
from son_t4 import sha,probe,video_hash
D=Path(__file__).resolve().parent
with TemporaryDirectory(prefix='vv-t4-qa-') as t:
 root=Path(t);signal=root/'signal-fictif.wav';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=3','-ar','48000','-y',str(signal)],check=True)
 with App(('127.0.0.1',0),root) as srv:
  Thread(target=srv.serve_forever,daemon=True).start();u=f'http://127.0.0.1:{srv.server_port}/';print('Serveur local prêt',flush=True)
  try:
   urllib.request.urlopen(u+'api/job/'+'0'*32,timeout=5);raise AssertionError('Session absente acceptée')
  except urllib.error.HTTPError as e:assert e.code==403
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream','--autoplay-policy=no-user-gesture-required']);page=browser.new_page(viewport={'width':390,'height':844},bypass_csp=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   try:
    page.goto(u,wait_until='domcontentloaded',timeout=45000);page.wait_for_function("document.documentElement.dataset.ready==='yes'");page.fill('#nom_offre','Gloss transparent');page.fill('#situation_conseillee','Pour un peu de brillance sans couleur');page.fill('#detail_visible','Le reflet à la lumière');page.select_option('#action','commande');page.check('#action_confirmee');page.fill('#accroche','Envie de brillance ?');page.locator('#fiche-container details summary').click();page.fill('#prix','2500');page.click('#fiche-form button');page.wait_for_selector('#fiche-error:visible');assert 'monnaie' in page.locator('#fiche-error').inner_text();page.fill('#devise','FCFA');page.select_option('#type_prix','depart');page.fill('#nom_affiche','Nom fictif');page.fill('#lieu_affiche','Lieu fictif');page.select_option('#moyen','message');page.fill('#destination','CONTACT FICTIF');page.click('#fiche-form button');page.wait_for_function("__capture().state==='A'");page.screenshot(path=str(D/'Capture-prototype-consigne.png'))
    print('Annulation enregistrée',flush=True);page.locator('#cta').click();page.wait_for_function("__capture().state==='B'",timeout=15000);page.locator('#cancelCapture').click();page.wait_for_function("__capture().state==='A' && !__capture().videoActive");assert page.evaluate('__capture().accepted.length')==0
    for i in range(1,5):
     print('Capture simulée',i,flush=True);assert page.evaluate('__capture().prise')==f'S{i}';page.locator('#cta').click();page.wait_for_function("__capture().state==='B'",timeout=15000);page.wait_for_function("__capture().state==='C'",timeout=22000);page.wait_for_function("!document.getElementById('next').disabled",timeout=20000);assert len(page.evaluate('__capture().accepted'))==i
     if i==2:page.screenshot(path=str(D/'Capture-prototype-relecture.png'))
     if i==4:
      page.locator('#voiceFile').set_input_files(str(signal));page.locator('#voiceZone details summary').click();page.fill('#sousTitres','0.5 | 3.0 | Signal de test sans paroles');page.check('#stConfirme')
     page.locator('#next').click()
     if i<4:page.wait_for_function("__capture().state==='A'",timeout=10000)
    print('Rendu des vidéos capturées',flush=True);page.wait_for_function("!document.getElementById('result').hidden || !document.getElementById('mediaFeedback').hidden",timeout=300000)
    assert page.locator('#result').is_visible(), 'Le montage a échoué'
    assert page.locator('#resultCredit').inner_text().startswith('« ');assert page.locator('#resultFilm').get_attribute('src').startswith('blob:');assert not errors,errors
    assert len(srv.jobs)==1;j=next(iter(srv.jobs.values()));assert j['status']=='termine';assert j['fiche']['prix']=='2500' and j['fiche']['prix_confirme'] is False and j['fiche']['destination']=='CONTACT FICTIF';raw=[j['path']/f'brut-{i}.bin' for i in range(1,5)];assert all(p.stat().st_size>500 for p in raw)
    normalized=[j['path']/f'S{i}.mp4' for i in range(1,5)];duration=[float(probe(p)['format']['duration']) for p in normalized];assert all(abs(d-n)<.04 for d,n in zip(duration,[6,13,8,7]));master=j['path']/'master.mp4';film=j['path']/'film.mp4';layout=vers_image(j['fiche']);assert layout['signature']=='Nom fictif · Lieu fictif' and '2500' not in layout['signature'] and 'CONTACT FICTIF' not in layout['signature'];subprocess.run(['ffmpeg','-v','error','-ss','27','-i',str(master),'-frames:v','1','-y',str(D/'Capture-prototype-carton-final.png')],check=True);stmaster=j['path']/'master-sous-titres.mp4';assert stmaster.is_file() and video_hash(master)!=video_hash(stmaster) and video_hash(stmaster)==video_hash(film);receipt=json.loads((j['path']/'film.json').read_text());assert receipt['piste'] in 'ABCD' and receipt['voix']['presente'] and receipt['voix']['ducking_db']==13 and receipt['voix']['debit_modifie'] is False
    report={'statut':'PASS','portee':'Chromium headless, caméra et micro SIMULÉS : 12 états et 4 fichiers MediaRecorder effectivement capturés, normalisés puis consommés par prototype image+audio. Pas d’appareil physique, ni cas réels, ni validation ni publication.','viewport':[390,844],'csp_test_instrumente':'désactivée dans cette recette pour Playwright ; vérification séparée sans bypass dans Recette-csp-refus.json','autorisation_cross_session_rejetee':True,'annulation_et_liberation_camera':'PASS','durees_valides_s':duration,'mp4_resultat_sha256':sha(film),'master_sha256':sha(master),'flux_video_preserve':'PASS : master sous-titré copié intact dans le film avec audio ; master initial conservé séparément','sous_titres':'Texte fictif saisi et incrusté ; pas de transcription ni synchronisation vérifiées sur voix humaine','piste':receipt['piste'],'credit':receipt['credit'],'erreurs_javascript':errors,'fiche_optionnelle':'Nom et lieu fictifs affichés ; prix non confirmé et destination non autorisée exclus ; réalité non vérifiée','prix_incomplet_rejete_avant_capture':'PASS','voix_off':'Signal synthétique importé depuis l’interface, pas une narration humaine','limites':['Contrôle réel des coordonnées et promesses incombe encore à l’annonceur','Voix humaine et sous-titres non testés','Transitions visuelles non conformes à la référence R2','Pas de production ni déploiement','Serveur lié à localhost uniquement']};(D/'Recette-capture-simulee.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('PASS capture simulée et montage',flush=True)
   except Exception:
    try:page.screenshot(path=str(D/'Capture-prototype-erreur.png'));print('Etat page',page.evaluate("window.__capture ? __capture() : null"),flush=True);print('Messages',page.locator('#mediaMessage').text_content(),flush=True);print('Jobs',[(j['status'],j.get('debug_type'),j.get('debug')) for j in srv.jobs.values()],flush=True);import shutil;[shutil.copytree(j['path'],Path.home()/'.cache/vv-t4-capture-echec',dirs_exist_ok=True) for j in srv.jobs.values()]
    except Exception:pass
    raise
   finally:browser.close()
  srv.shutdown()
