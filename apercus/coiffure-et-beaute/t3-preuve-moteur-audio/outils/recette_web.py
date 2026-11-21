#!/usr/bin/env python3
"""Test hors réseau du parcours import/relecture → création → téléchargement réel."""
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.commun import ROOT, TAKES, lire, ecrire, sha
from service import Appli


def navigateur(a,temp,app,preview):
    from playwright.sync_api import sync_playwright
    u=f'http://127.0.0.1:{app.server_port}/';events=[];hors=[]
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=a.chromium,args=['--no-sandbox']);c=b.new_context(viewport={'width':390,'height':844},accept_downloads=True)
        def intercepte(route):
            if route.request.url.startswith(u):route.continue_()
            else:hors.append(route.request.url);route.abort()
        c.route('**/*',intercepte);page=c.new_page();page.on('pageerror',lambda e:events.append(str(e)))
        page.goto(u);page.locator('#example:not(:disabled)').wait_for()
        if preview:page.locator('#example').click()
        else:
            for k,v in lire(ROOT/'exemple/fiche.json').items():
                field=page.locator(f'[name={k}]')
                if k in ('nom','lieu'):continue
                if k=='action':field.select_option(v)
                else:field.fill(v)
        page.locator('#continuer').click()
        for s in TAKES:
            assert page.locator('#scene').inner_text().startswith(s+' ·')
            if not preview:page.locator('#fichier').set_input_files(a.exemple/(s+'.mp4'))
            page.locator('#relecture').wait_for(state='visible')
            page.locator('#relecture').evaluate('v=>v.play()')
            page.locator('#garder:not(:disabled)').wait_for();page.locator('#garder').click()
        assert page.locator('#slots .kept').count()==4
        assert page.evaluate('document.documentElement.scrollWidth===innerWidth')
        page.locator('#piste').select_option('01');page.locator('#rendre').click()
        page.locator('#resultat').wait_for(timeout=120000)
        page.locator('#film').evaluate('v=>v.play()')
        assert page.locator('#film').evaluate('v=>new Promise(resolve=>{v.addEventListener("timeupdate",()=>{if(v.currentTime>.18)resolve(true)},{passive:true});setTimeout(()=>resolve(false),4000)})')
        page.locator('#film').evaluate('v=>v.pause()')
        assert 'Copa' in page.locator('#titreResultat').inner_text()
        assert '1000Handz.com' in page.locator('#credit').inner_text()
        mp4=temp/'lecture.mp4';credit=temp/'credit.txt'
        with page.expect_download() as dd:page.locator('#dl').click()
        dd.value.save_as(mp4)
        with page.expect_download() as dd:page.locator('#dlCredit').click()
        dd.value.save_as(credit)
        assert '1000Handz.com' in credit.read_text(encoding='utf-8')
        sig=sha(mp4)
        assert page.locator('#dl').get_attribute('href')==page.locator('#film').get_attribute('src')
        assert page.locator('#piste option[value="01"]').is_disabled()
        assert not hors and not events
        page.screenshot(path=str(temp/'mobile.png'),full_page=True)
        b.close()
    session,=app.sessions.values();folder,=(session.dest/'exports').iterdir();r=lire(folder/'resultat.json')
    assert r['mp4_sha256']==sig and r['musique']['piste']=='01' and not r['image_reutilisee']
    assert r['image']['prises']['S2']['original_son']
    assert all(r['prises_sha256'][s]==sha(a.exemple/(s+'.mp4')) for s in TAKES)
    assert app.outils.signature(mp4,False)==r['image']['signature']
    return {'import_quatre_prises':not preview,'exemple_demo':preview,'quatre_relectures':True,'mobile_largeur':390,'lecture_mp4':True,'meme_fichier_lecture_telechargement':True,'piste':'01','empreinte':sig,'credit_Copa_telecharge':True,'repetition_du_dernier_succes_desactivee':True,'appels_hors_origine':hors,'erreurs_js':events}


def main():
    c=ArgumentParser(description=__doc__);c.add_argument('--sortie',type=Path,required=True);c.add_argument('--chromium');c.add_argument('--demo',action='store_true')
    for k in ('exemple','polices','pack'):c.add_argument('--'+k,type=Path,default=ROOT/('audio' if k=='pack' else k))
    c.add_argument('--ffmpeg');c.add_argument('--ffprobe');a=c.parse_args();a.sortie.mkdir(parents=True)
    with TemporaryDirectory(prefix='t3-recette-web-') as tmp,Appli(('127.0.0.1',0),a,Path(tmp)) as http:
        t=Thread(target=http.serve_forever,daemon=True);t.start()
        try:report=navigateur(a,a.sortie,http,a.demo)
        finally:http.shutdown();t.join()
    ecrire(a.sortie/'Controle-Parcours-Web.json',{'statut':'PASS',**report});print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
