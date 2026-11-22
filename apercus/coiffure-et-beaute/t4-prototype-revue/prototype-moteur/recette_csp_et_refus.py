#!/usr/bin/env python3
"""Contrôles navigateur sans désactivation CSP : accueil, caméra refusée et origine étrangère."""
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import json,urllib.request,urllib.error
from playwright.sync_api import sync_playwright,expect
from atelier_local import App
D=Path(__file__).resolve().parent
with TemporaryDirectory(prefix='t4-securite-') as t:
 with App(('127.0.0.1',0),Path(t)) as s:
  Thread(target=s.serve_forever,daemon=True).start();u=f'http://127.0.0.1:{s.server_port}/'
  with urllib.request.urlopen(u,timeout=5) as r:
   csp=r.headers['Content-Security-Policy'];assert "frame-ancestors 'none'" in csp and "'unsafe-eval'" not in csp
  req=urllib.request.Request(u+'api/job',data=b'{}',headers={'X-T4-Session':s.token,'Origin':'https://exemple-invalide.test','Content-Type':'application/json'})
  try:urllib.request.urlopen(req,timeout=5);raise AssertionError('Origine étrangère acceptée')
  except urllib.error.HTTPError as e:assert e.code==403
  with sync_playwright() as pw:
   b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--deny-permission-prompts']);ctx=b.new_context(viewport={'width':320,'height':568});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(u,wait_until='domcontentloaded');expect(page.locator('#fiche-container')).to_be_visible();page.fill('#nom_offre','Service fictif');page.fill('#situation_conseillee','Pour une occasion');page.fill('#detail_visible','Une finition visible');page.select_option('#action','aucune');page.click('#fiche-form button');expect(page.locator('#sheet')).to_be_visible();page.click('#cta');expect(page.locator('#mediaFeedback')).to_be_visible(timeout=15000);expect(page.locator('#mediaMessage')).to_contain_text('autorisations');assert not errors,errors
   page.screenshot(path=str(D/'Capture-prototype-refus.png'));ctx.close();b.close()
  s.shutdown()
report={'resultat':'PASS','portee':'Chromium headless à 320 px sans désactivation CSP : formulaire, affichage consigne et permission refusée ; origine étrangère rejetée par HTTP. Pas de capture réelle ni sécurité production complète.','csp_en_place':csp,'caméra_refusée':'PASS','origine_etrangere':'PASS','erreurs_javascript':errors};(D/'Recette-csp-refus.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('PASS CSP et refus caméra')
