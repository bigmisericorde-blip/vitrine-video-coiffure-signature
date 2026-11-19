"""Vérifie la livraison du film narré. Ne publie rien et ne remonte aucune prise."""
from argparse import ArgumentParser
from contextlib import ExitStack
from functools import partial
from hashlib import sha256
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.request import Request, urlopen
import json
import subprocess

from core import HERE, ROOT, ffmpeg, load, sha

FILM='media/t2-signature-coiffure-narree.mp4'
VTT='media/t2-signature-voix.vtt'
RAPPORT='livrables/t2-final/recette-film.json'


def check_film(film, recette):
    r=recette['rendu']
    assert r['fichier']==FILM and film.stat().st_size==r['octets'] and sha(film)==r['sha256'], 'MP4 différent de la livraison'
    probe=json.loads(subprocess.check_output([
        'ffprobe','-v','error','-show_streams','-show_format','-of','json',str(film),
    ],timeout=30))
    v,a=probe['streams']
    assert v['codec_name']=='h264' and (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']))==(720,1280,'30/1',900)
    assert (a['codec_name'],a['profile'],int(a['sample_rate']),a['channels'])==('aac','LC',48000,2)
    assert all(abs(float(stream['duration'])-30)<.001 for stream in (v,a,probe['format']))
    avc=subprocess.check_output([ffmpeg(),'-v','error','-i',str(film),'-map','0:v:0',
        '-c:v','copy','-hash','sha256','-f','hash','-'],text=True,timeout=30).strip()
    assert avc==r['avc_copie_depuis_rendu_web'], 'Empreinte AVC inattendue'
    subprocess.run([ffmpeg(),'-v','error','-xerror','-i',str(film),'-map','0:v:0','-map','0:a:0','-f','null','-'],check=True,timeout=45)
    print(f'PASS : MP4 {r["octets"]} octets, SHA-256 {r["sha256"]}, H.264 900 images + AAC-LC, décodage sans erreur.',flush=True)


def check_http(base, paths, manifest, canonical=False):
    for path in paths:
        url=base.rstrip('/')+'/'+path
        req=Request(url,headers={'User-Agent':'Vitrine-Video-T2-verification','Cache-Control':'no-cache','Accept-Encoding':'identity'})
        with urlopen(req,timeout=45) as rep:
            data=rep.read()
            if canonical and path==FILM:assert rep.headers.get_content_type()=='video/mp4'
        row=manifest[path];assert len(data)==row['bytes'] and sha256(data).hexdigest()==row['sha256'],f'Octets différents : {url}'
    print(f'PASS : {len(paths)} fichiers servis conformes aux empreintes — {base}',flush=True)


def check_player(base, seconds, work, play_full):
    from playwright.sync_api import sync_playwright, expect
    errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
        page=browser.new_page(viewport={'width':320,'height':780},accept_downloads=True)
        page.on('pageerror',lambda err:errors.append(str(err)))
        page.on('response',lambda r:errors.append(f'{r.status} {r.url}') if r.status>=400 and r.url.startswith(base) else None)
        page.goto(base,wait_until='domcontentloaded',timeout=45000)
        page.locator('#finalFilmLink').click()
        expect(page.locator('h1')).to_have_text('Studio Vitrine')
        video=page.locator('#finalFilm')
        page.wait_for_function('document.getElementById("finalFilm").readyState >= 1',timeout=45000)
        assert video.evaluate('v=>[v.duration,v.videoWidth,v.videoHeight,v.muted]')==[seconds,720,1280,False]
        assert video.evaluate('v=>v.currentSrc')==page.locator('#filmDownload').evaluate('a=>a.href')
        video.evaluate('v=>{v.textTracks[0].mode="hidden"}')
        page.wait_for_function('document.querySelector("#finalFilm track").readyState === 2',timeout=25000)
        assert video.evaluate('v=>v.textTracks[0].cues.length')==5
        video.evaluate('v=>v.play()')
        page.wait_for_function('document.getElementById("finalFilm").currentTime > 0.32',timeout=45000)
        if play_full:
            page.wait_for_function('document.getElementById("finalFilm").ended',timeout=65000)
        video.evaluate('v=>{v.pause();v.currentTime=27.56}')
        page.wait_for_function('''() => { const v=document.getElementById("finalFilm");
            return !v.error && !v.seeking && v.readyState>=2 && Math.abs(v.currentTime-27.56)<.09; }''', timeout=45000)
        expect(page.locator('.frames img')).to_have_count(4)
        for image in page.locator('.frames img').all():
            image.scroll_into_view_if_needed(); image.evaluate('i=>i.decode()')
        page.locator('#rushs summary').click();expect(page.locator('.rush-grid video')).to_have_count(4)
        assert page.locator('.rush-grid video').evaluate_all('v=>v.map(i=>i.getAttribute("src"))')==[f'media/S{n}.mp4' for n in range(1,5)]
        for w in (320,360,430,1200):
            page.set_viewport_size({'width':w,'height':780})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'Débordement horizontal à {w}px'
        assert page.evaluate('''async () => (await Promise.all([
            document.fonts.load('64px Pinyon'),document.fonts.load('36px DMSerif')
        ])).every(a=>a.length && a.every(f=>f.status==='loaded'))''')
        with page.expect_download(timeout=60000) as result:page.locator('#filmDownload').click()
        downloaded=work/'telecharge.mp4';result.value.save_as(str(downloaded))
        assert sha(downloaded)==sha(ROOT/FILM),'Téléchargement différent du MP4 répertorié'
        browser.close()
    assert not errors,errors
    print('PASS : accès depuis la fiche, vidéo audible non muette'+(' lue jusqu’à la fin' if play_full else '')+', recherche du carton, 5 sous-titres, 4 sources, mise en page 320–1200 px, téléchargement identique.',flush=True)


def main():
    parser=ArgumentParser(description=__doc__)
    url=parser.add_mutually_exclusive_group();url.add_argument('--url');url.add_argument('--local',action='store_true')
    parser.add_argument('--raw-url',help='Racine raw.githubusercontent.com avec le commit épinglé')
    parser.add_argument('--play-full',action='store_true',help='Laisser le lecteur tourner jusqu’à la dernière image')
    opts=parser.parse_args();recipe=load(ROOT/RAPPORT);manifest={r['path']:r for r in load(HERE/'manifest-t2.json')['artifacts']}
    expected={r['fichier']:r['sha256'] for r in recipe['rushs']}|{r['chemin']:r['sha256'] for r in recipe['polices'].values()}|{recipe['plan']:recipe['plan_sha256']}
    assert all(sha(ROOT/k)==v for k,v in expected.items())
    check_film(ROOT/FILM,recipe)
    with ExitStack() as cleanup:
        work=Path(cleanup.enter_context(TemporaryDirectory(prefix='recette-film-t2-')))
        base=opts.url
        if opts.local:
            from serve import Handler
            class Quiet(Handler):
                def log_message(self,*args):pass
            server=cleanup.enter_context(ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT))))
            Thread(target=server.serve_forever,daemon=True).start();cleanup.callback(server.shutdown)
            base=f'http://127.0.0.1:{server.server_port}/'
        new=sorted(path for path in manifest if path.startswith('livrables/t2-final/') or path in {
            'README.md','CREDITS.md','index.html','final.html','assets/final-t2.css','livrables/09-film-final-t2.md',FILM,VTT})
        if opts.raw_url:check_http(opts.raw_url,new,manifest)
        if base:
            base=base.rstrip('/')+'/'
            check_http(base,sorted(set(new)|set(expected)),manifest,canonical=True)
            check_player(base,recipe['rendu']['duree_s'],work,opts.play_full)


if __name__=='__main__':main()
