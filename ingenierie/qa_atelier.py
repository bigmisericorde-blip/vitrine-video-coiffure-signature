#!/usr/bin/env python3
"""Recette navigateur + vrai encodeur, sans importer de voix d'essai dans le moteur."""
import argparse
from hashlib import sha256
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright
from core import HERE, save, sha
from mix_voix import command


def verify(base, folder, captures=None):
    fixture=Path(folder)
    voice=fixture/'narration-en.wav'; picture=fixture/'montage-parle.mp4';long=fixture/'trop-long.wav'
    assert voice.is_file() and picture.is_file()
    command('-v','error','-y','-f','lavfi','-i','sine=frequency=370:d=35','-c:a','pcm_s16le',long)
    steps=[]
    def ok(line): steps.append(line);print('PASS',line,flush=True)
    def digest(url):
        with urlopen(url,timeout=15) as f:
            h=sha256()
            while b:=f.read(65536): h.update(b)
            return h.hexdigest()
    with sync_playwright() as pw:
        b=pw.chromium.launch(args=['--no-sandbox','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream',
                                   f'--use-file-for-fake-audio-capture={voice.resolve()}'])
        c=b.new_context(viewport={'width':390,'height':820},accept_downloads=True)
        p=c.new_page();errs=[];p.on('pageerror',lambda e:errs.append(str(e)))
        p.goto(base+'atelier.html');expect(p.locator('#render')).to_be_enabled(timeout=8000)
        assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
        def choose(group,value):
            p.locator(f'input[name={group}][value={value}] + span').click()
        def submit(code=201):
            with p.expect_response(lambda r:r.url.endswith('/api/montages') and r.request.method=='POST',timeout=58000) as response:
                p.locator('#render').click()
            res=response.value;data=res.json();assert res.status==code,(res.status,data)
            if code==201:
                expect(p.locator('#download')).to_have_attribute('href',data['url']+'?download=1')
                expect(p.locator('#result')).to_have_attribute('src',data['url'])
                p.wait_for_function('document.querySelector("#result").readyState >= 1')
                assert abs(p.locator('#result').evaluate('v => v.duration')-data['duree_s'])<.055
                assert p.locator('#result').evaluate('v => v.muted') is False
            return data
        choose('voiceMode','texte');p.locator('#lang').select_option('fon');p.locator('#script').fill('Texte à lire avec ma propre voix.')
        expect(p.locator('#render')).to_be_disabled();p.locator('#speakInstead').click()
        expect(p.locator('#prompter')).to_be_visible();expect(p.locator('#prompterCopy')).to_have_text('Texte à lire avec ma propre voix.')
        ok('Le texte non synthétisé reste accessible à la personne qui l’enregistre')

        choose('voiceMode','texte');p.locator('#lang').select_option('fr');p.locator('#script').fill('Bonjour. Pour découvrir le salon, choisis le créneau qui te convient.')
        a=submit();assert a['voix']['synthese']['code']=='fr' and a['voix']['presente'];assert a['voix']['ducking_db']==13 and not a['voix']['debit_modifie']
        first=a['url'];p.locator('#result').evaluate('v => v.play()');p.wait_for_function('document.querySelector("#result").currentTime>0.15');p.locator('#result').evaluate('v => v.pause()')
        with p.expect_download() as d: p.locator('#download').click()
        assert sha(d.value.path())==digest(base+first)==a['sha256']
        p.reload();expect(p.locator('#result')).to_have_attribute('src',first)
        ok('Texte français réellement synthétisé et mixé ; lecture, téléchargement et rechargement gardent le même MP4')
        if captures: p.screenshot(path=str(Path(captures)/'atelier-mobile.png'),full_page=True)

        choose('voiceMode','audio');p.locator('#entry').select_option('file');p.locator('#sourceAudio').set_input_files(str(long))
        assert 'n’accélère pas' in submit(422)['error'];expect(p.locator('#result')).to_have_attribute('src',first)
        p.locator('#sourceAudio').set_input_files(str(voice));bb=submit();assert bb['voix']['presente'] and bb['voix']['type']=='audio'
        ok('Import voix sans imposer de langue ; narration trop longue refusée sans couper ni changer le MP4 précédent')

        choose('imageMode','file');p.locator('#sourceVideo').set_input_files(str(picture));p.locator('#entry').select_option('video');cc=submit()
        assert cc['image']=='personnelle' and cc['voix']['position_s']==0 and abs(cc['duree_s']-8)<.01
        assert .9<cc['voix']['fenetres_voix_s'][0][0]<1.52,cc['voix']
        ok('Vidéo personnelle : sa voix est gardée à son horloge, muxée dans le MP4')

        choose('imageMode','demo');choose('voiceMode','texte');p.locator('#lang').select_option('en');p.locator('#script').fill('Discover the difference. Book your next appointment online.')
        dd=submit();assert dd['voix']['synthese']['code']=='en'
        ids=[row['piste']['id'] for row in [a,bb,cc,dd]];assert len(set(ids))==4,ids
        ok('Texte anglais synthétisé ; les quatre fonds ont tourné une fois, aucun doublon consécutif')

        choose('voiceMode','sans');p.locator('#music').uncheck();silence=submit();assert not silence['piste'] and not silence['voix']['presente'] and not silence['son']
        ok('Option vraiment muette sans musique ni narration')
        choose('voiceMode','audio');p.locator('#entry').select_option('mic');p.locator('#music').check()
        p.locator('#record').click();expect(p.locator('#micState')).to_contain_text('Le micro enregistre',timeout=8000)
        p.wait_for_timeout(2500);p.locator('#record').click();expect(p.locator('#micListen')).to_be_visible()
        e=submit();assert e['voix']['presente'] and e['piste']['id']!=dd['piste']['id']
        ok('Capture micro enregistrée et mixée ; changement de fond même à la frontière du cycle')
        assert not errs,errs
        b.close()
    return {'resultat':'PASS','ateliers':steps,'rotation_quatre_ids':ids,'durations':[a['duree_s'],bb['duree_s'],cc['duree_s'],dd['duree_s']],
            'attenuation_db':13,'synthese_testee':['fr','en'],'viewport_px':[390,820],
            'validation':'La preuve navigateur utilise des textes et fichiers de test temporaires. Aucun n’est dans le catalogue.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',default='http://127.0.0.1:8080/');p.add_argument('--fixtures',type=Path,required=True);p.add_argument('--captures',type=Path)
    a=p.parse_args();r=verify(a.url.rstrip('/')+'/',a.fixtures,a.captures);save(HERE/'recette-atelier.json',r)
