#!/usr/bin/env python3
"""Recette de la fiche jusqu’au MP4 (et, en option, jusqu’au remix voix lié)."""
import argparse
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import hashlib
import json
import re
import subprocess
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect, sync_playwright
from core import CASE, HERE, ROOT, ffmpeg, load, save, sha
from mixage import image_hash, measure
from serve import Handler

FIXTURE=HERE/'fixtures/fiche-t2-recette.json'
PREFIX='/vitrine-video-coiffure-signature/'


def digest_audio(path, *, encoded=False):
    cmd=[ffmpeg(),'-v','error','-i',str(path),'-map','0:a:0']
    if encoded: cmd+=['-c:a','copy']
    return subprocess.check_output([*cmd,'-f','hash','-hash','SHA256','-'],text=True).strip().split('=')[-1]


def probe(path):
    raw=subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],text=True)
    data=json.loads(raw);v=[t for t in data['streams'] if t['codec_type']=='video'];a=[t for t in data['streams'] if t['codec_type']=='audio']
    assert len(v)==len(a)==1,data['streams']
    v,a=v[0],a[0];duration=float(data['format']['duration'])
    assert duration==30 and v['codec_name']=='h264' and v['width']==720 and v['height']==1280 and v['avg_frame_rate']=='30/1' and v['nb_frames']=='900',v
    assert a['codec_name']=='aac' and a['sample_rate']=='48000' and a['channels']==2,a
    return {'duree_s':duration,'images':int(v['nb_frames']),'codec':v['codec_name'],'image':[720,1280,30],
            'audio':'AAC LC 48 kHz stéréo','taille_octets':path.stat().st_size,'sha256':sha(path)}


def run(base,out, *, personnalise=False, voix=False):
    fields=load(FIXTURE);case=load(CASE);checks=[]
    def good(message):
        checks.append(message);print('PASS',message,flush=True)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
        ctx=browser.new_context(viewport={'width':375,'height':812},accept_downloads=True)
        p=ctx.new_page();errors=[];requests=[]
        p.on('pageerror',lambda e: errors.append(str(e)))
        ctx.on('request', lambda r: requests.append((r.method,r.url)))
        p.add_init_script('Math.random = () => 0;')
        p.goto(base);assert p.evaluate('isSecureContext && typeof VideoEncoder === "function"')
        for k in ('salon','ville','service','prix'):p.fill('#'+k,fields[k])
        p.check('[name=resultatChoix][value=autre]');p.fill('#resultatAutre',fields['resultatAutre'])
        p.select_option('#action',fields['action']);p.fill('#contact',fields['contact'])
        if personnalise:p.check('[name=source][value=client]')
        p.check('#checkedCase');p.click('#previewScreens')
        identity=parse_qs(urlsplit(p.url).query)['fiche'][0];assert re.fullmatch('[0-9a-f]{32}',identity)
        expect(p.locator('#galleryCase')).to_contain_text(fields['salon'])
        for n in range(1,13):
            p.select_option('#screenSelect',str(n));f=p.frame_locator('#screenLive')
            expect(f.locator('#app')).to_have_attribute('data-state','ABC'[(n-1)%3])
            expect(f.locator('#app')).to_have_attribute('data-prise',f'S{(n-1)//3+1}')
            target=['#caseContext','#recContext','#reviewContext'][(n-1)%3]
            expect(f.locator(target)).to_contain_text(fields['resultatAutre'] if n>=10 else fields['service'])
            if n>=10:expect(f.locator(target)).to_be_visible()
            expect(p.locator('#screenAlone')).to_have_attribute('href',re.compile(f'fiche={identity}$'))
        p.locator('#screenAlone').click();expect(p.locator('#reviewContext')).to_contain_text(fields['resultatAutre']);expect(p.locator('#next')).to_be_disabled()
        assert p.evaluate('window.__demo.validations().length')==0
        good('Même fiche lisible dans les 12 états A/B/C et en ouverture directe ; aperçu sans validation')
        p.goto(base+'index.html?fiche='+identity)
        expect(p.locator('#salon')).to_have_value(fields['salon']);expect(p.locator('#contact')).to_have_value(fields['contact'])
        p.check('#checkedCase');p.click('#startTest');assert identity==parse_qs(urlsplit(p.url).query)['fiche'][0]
        assert fields['contact'] not in p.url and fields['salon'] not in p.url
        requests.clear()
        p.locator('#cam').evaluate('v=>v.defaultPlaybackRate=v.playbackRate=5')
        for i,s in enumerate(case['scenes']):
            expect(p.locator('#app')).to_have_attribute('data-prise',s['id'])
            if personnalise:
                if i==1:
                    p.locator('#takeFile').set_input_files(ROOT/'media/S1.mp4');expect(p.locator('#mediaMessage')).to_contain_text('Prise trop courte')
                    expect(p.locator('#app')).to_have_attribute('data-state','A')
                p.locator('#takeFile').set_input_files(ROOT/'media'/s['media'])
                expect(p.locator('#cam')).to_have_attribute('src',re.compile('^blob:'))
            else:p.click('#cta')
            expect(p.locator('#app')).to_have_attribute('data-state','B');expect(p.locator('#recContext')).to_be_visible()
            expect(p.locator('#next')).to_be_enabled(timeout=15000);expect(p.locator('#reviewContext')).to_be_visible()
            p.click('#next')
        p.wait_for_function("!document.querySelector('#montageGo').disabled || !document.querySelector('#montageRetry').hidden",timeout=180000)
        assert not p.locator("#montageGo").is_disabled(),p.locator("#montageStatus").inner_text()
        assert p.evaluate('window.__demo.validations()')==['S1','S2','S3','S4']
        assert any(urlsplit(url).path.endswith('/ingenierie/plan.json') for m,url in requests),requests
        assert not [url for m,url in requests if m!='GET'],requests
        if personnalise:
            assert not [url for _,url in requests if re.search(r'/media/S[1-4]\.mp4',url)],requests
            good('Quatre fichiers locaux utilisés ; clip trop court rejeté ; aucun clip d’exemple chargé pendant les prises')
        else:good('Plan T2 lu par le moteur ; quatre prises validées ; aucune donnée envoyée')
        p.click('#montageGo');video=p.locator('#ad');p.wait_for_function('document.querySelector("#ad").currentTime>.12')
        src=video.get_attribute('src');assert src.startswith('blob:')
        expect(p.locator('#caCta')).to_have_attribute('href','tel:'+re.sub('[^+0-9]','',fields['contact']))
        preview_sha=p.evaluate('''async()=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await (await fetch(document.querySelector('#ad').src)).arrayBuffer())),n=>n.toString(16).padStart(2,'0')).join('')''')
        p.click('#adClose');expect(p.locator('#endMeta')).to_have_attribute('data-template','T2@1.0.0')
        track=p.locator('#endMeta').get_attribute('data-track')
        expect(p.locator('#endDownload')).to_have_attribute('href',src)
        file=out/('t2-import.mp4' if personnalise else 't2-fiche-personnalisee.mp4')
        with p.expect_download() as item:p.click('#endDownload')
        item.value.save_as(file);assert sha(file)==preview_sha
        p.click('#replayAd');expect(video).to_have_attribute('src',src);p.click('#adClose')
        stats=probe(file)
        original=ROOT/'media'/'afrobeat'/(track+'.mp4');assert digest_audio(file,encoded=True)==digest_audio(original,encoded=True)
        sig=digest_audio(file);assert sig==digest_audio(original)
        lu,peak=measure(file)
        stats.update({'piste':track,'pcm_sha256':sig,'lufs_i':lu,'dbtp':peak})
        assert image_hash(file)!=image_hash(ROOT/'media'/case['sortie']['file'])
        good('Nouveau H.264/AAC de 900 images ; aperçu, relecture et téléchargement identiques ; AAC et PCM du fond conservés')
        mix=None
        if voix:
            p.click('#voiceOpen');a=p.frame_locator('#voiceFrame');expect(a.locator('#linkedVideo')).to_contain_text(fields['salon'])
            a.locator('[name=voiceMode][value=texte]').check();a.locator('#lang').select_option('fr')
            a.locator('#script').fill('Bienvenue chez Éclat des Boucles. Nous prenons le temps de soigner tes boucles. Regarde le résultat. Retrouve-nous à Porto-Novo.')
            expect(a.locator('#render')).to_be_enabled()
            with p.expect_response(lambda r:r.url.endswith('/api/montages') and r.request.method=='POST',timeout=90000) as answer:a.locator('#render').click()
            res=answer.value;r=res.json();assert res.status==201,r
            assert r['piste']['id']==track and r['image']=='t2' and r['voix']['presente'] and not r['voix']['debit_modifie'],r
            expect(a.locator('#download')).to_have_attribute('href',r['url']+'?download=1')
            expect(a.locator('#result')).to_have_attribute('src',r['url'])
            with p.expect_download() as item:a.locator('#download').click()
            spoken=out/('t2-import-voix.mp4' if personnalise else 't2-fiche-voix.mp4');item.value.save_as(spoken)
            mix=probe(spoken);assert mix['sha256']==r['sha256'] and image_hash(file)==image_hash(spoken)
            mix.update({'piste':track,'voix':r['voix'],'mesures':r['son']})
            p.click('#voiceClose');expect(p.locator('#endDownload')).to_have_attribute('href',src)
            good('Voix du texte client synthétisée en FR ; fond épinglé, débit conservé, image AVC copiée, vrai MP4 narré')
        assert not errors,errors
        browser.close()
    suffix='import' if personnalise else 'fiche'
    save(out/f'recette-t2-{suffix}.json',{'resultat':'PASS','mode':'import' if personnalise else 'exemple',
         'checks':checks,'sortie':stats,'sortie_voix':mix})


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--url');a.add_argument('--output',type=Path,required=True)
    a.add_argument('--importer',action='store_true');a.add_argument('--voix',action='store_true')
    args=a.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    if args.url:
        run(args.url.rstrip('/')+'/',args.output,personnalise=args.importer,voix=args.voix)
        return
    if args.voix:a.error('--voix demande l’URL de serve_atelier.py')
    class Pages(Handler):
        def log_message(self,*args):pass
        def send_head(self):
            if not self.path.startswith(PREFIX):self.send_error(404);return None
            self.path=self.path[len(PREFIX)-1:]; return super().send_head()
    with ThreadingHTTPServer(('127.0.0.1',0),partial(Pages,directory=str(ROOT))) as server:
        Thread(target=server.serve_forever,daemon=True).start()
        try:run(f'http://127.0.0.1:{server.server_port}{PREFIX}',args.output,personnalise=args.importer)
        finally:server.shutdown()


if __name__=='__main__': main()
