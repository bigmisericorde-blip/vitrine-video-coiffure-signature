#!/usr/bin/env python3
"""Recette des quatre vrais MP4 dans le lecteur, par HTTP local ou GitHub Pages."""
import argparse
from functools import partial
from hashlib import sha256
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen

from playwright.sync_api import expect, sync_playwright
from core import CASE, HERE, ROOT, load, save, sha
from serve import Handler


def verify(base, revision):
    cfg = load(HERE / 'afrobeat.json')
    mix = load(HERE / 'recette-sonore.json')
    case = load(CASE)
    entries = cfg['pistes']
    assert len(entries) == 4 and mix['resultat'] == 'PASS'
    expected = {r['id']: r['video_sha256'] for r in mix['pistes']}
    silent = 'media/' + case['sortie']['file']
    tag = f'?revision={revision}' if revision else ''
    checks = []

    def passed(label):
        checks.append(label)
        print('PASS', label, flush=True)

    def media_path(track):
        return f"media/afrobeat/{track['id']}.mp4"

    def check_http(file, digest):
        with urlopen(Request(base + file + tag, headers={'Cache-Control': 'no-cache'}), timeout=22) as r:
            assert r.status == 200 and r.headers.get_content_type() == 'video/mp4'
            h = sha256()
            for buf in iter(lambda: r.read(65536), b''):
                h.update(buf)
            assert h.hexdigest() == digest, file

    for t in entries:
        check_http(media_path(t), expected[t['id']])
    check_http(silent, mix['master_sha256'])
    passed('Cinq fichiers vidéo servis avec les empreintes attendues, master muet intact')

    with sync_playwright() as p:
        browser = p.chromium.launch(args=['--no-sandbox', '--autoplay-policy=no-user-gesture-required'])
        ctx = browser.new_context(viewport={'width': 320, 'height': 568}, accept_downloads=True)
        page = ctx.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.add_init_script('window.tiragesTest = 0; Math.random = () => {window.tiragesTest++; return 0;};')
        for t in entries:
            page.goto(base + f"film.html?test={case['id']}&piste={t['id']}&revision={revision}")
            assert page.evaluate('window.VVAfrobeat.tracks.length') == 4
            expect(page.locator('#download')).to_have_attribute('href', media_path(t))
            expect(page.locator('#sonInfo')).to_contain_text(t['auteur'])
            expect(page.locator('#sonSource')).to_have_attribute('href', t['source'])
            expect(page.locator('#sonLicence')).to_have_attribute('href', t['licence'])
            player = page.locator('#clip')
            expect(player).to_have_attribute('src', media_path(t))
            page.wait_for_function('document.querySelector("#clip").readyState >= 1')
            assert player.evaluate('v => !v.muted && Math.abs(v.duration-30)<.04')
            player.evaluate('v => v.play()')
            page.wait_for_function('document.querySelector("#clip").currentTime > .15')
            player.evaluate('v => v.pause()')
        passed('Les quatre films se lisent avec son et affichent auteur, source et licence')

        page.goto(base + f"film.html?test={case['id']}&revision={revision}")
        href = page.locator('#download').get_attribute('href')
        page.locator('#retirer').click()
        new_href = page.locator('#download').get_attribute('href')
        assert href != new_href and new_href == page.locator('#clip').get_attribute('src')
        page.reload()
        expect(page.locator('#download')).to_have_attribute('href', new_href)
        with page.expect_download() as item:
            page.locator('#download').click()
        assert sha(item.value.path()) == expected[Path(new_href).stem]
        page.locator('#muet').click()
        expect(page.locator('#clip')).to_have_attribute('src', silent)
        expect(page.locator('#download')).to_have_attribute('href', silent)
        expect(page.locator('#sonCredit')).to_be_hidden()
        passed('Retirage différent, rechargement stable, fichier téléchargé identique à celui lu, option muette')

        def break_mix(route):
            route.abort()

        page.route('**/media/afrobeat/*.mp4', break_mix)
        page.goto(base + 'film.html' + tag)
        expect(page.locator('#filmMessage')).to_contain_text('master muet')
        expect(page.locator('#download')).to_have_attribute('href', silent)
        page.unroute('**/media/afrobeat/*.mp4', break_mix)
        passed('Lecteur : échec du MP4 musical → lecture et téléchargement du master muet')

        def validate_takes():
            page.locator('#cam').evaluate('v => {v.defaultPlaybackRate = v.playbackRate = 5;}')
            for i in range(4):
                assert page.locator('#cam').evaluate('v => v.muted')
                page.locator('#cta').click()
                expect(page.locator('#next')).to_be_enabled(timeout=12000)
                assert page.locator('#replay').evaluate('v => v.muted')
                page.locator('#next').click()

        page.goto(base + f"simulation.html?test={case['id']}&revision={revision}")
        assert page.evaluate('window.tiragesTest') == 0
        validate_takes()
        expect(page.locator('#montageGo')).to_be_enabled(timeout=110000)
        page.locator('#montageGo').click()
        page.wait_for_function('document.querySelector("#ad").currentTime>.15')
        assert page.locator('#ad').evaluate('v => !v.muted')
        src=page.locator('#ad').get_attribute('src')
        page.locator('#adClose').click()
        expect(page.locator('#endDownload')).to_have_attribute('href',src)
        assert src.startswith('blob:') and page.evaluate('window.tiragesTest') == 1
        previous=page.locator('#endMeta').get_attribute('data-track')
        page.locator('#replayAd').click()
        expect(page.locator('#ad')).to_have_attribute('src',src)
        page.locator('#adClose').click()
        assert page.evaluate('window.tiragesTest') == 1
        expect(page.locator('#endSoundCredits')).to_be_visible()
        page.locator('#restart').click()
        assert page.evaluate('window.__demo.validations().length') == 0
        validate_takes()
        expect(page.locator('#montageGo')).to_be_enabled(timeout=110000)
        assert page.evaluate('window.tiragesTest') == 2
        assert page.locator('#endMeta').get_attribute('data-track') != previous
        assert page.locator('#ad').get_attribute('src') != src
        passed('Parcours T2 : tirage après quatre validations ; relecture et export du même MP4 ; nouveau fond au montage suivant')

        # Le moteur manquant ne laisse pas télécharger une démo à la place du montage.
        last_successful=page.evaluate('VVAfrobeat.last()')
        page.route('**/assets/t2-render.worker.mjs*',lambda route: route.abort())
        page.goto(base + f"simulation.html?test={case['id']}&revision={revision}")
        validate_takes()
        expect(page.locator('#montageRetry')).to_be_visible(timeout=15000)
        expect(page.locator('#montageGo')).to_be_disabled()
        assert not page.locator('#endDownload').get_attribute('href')
        assert page.evaluate('VVAfrobeat.last()') == last_successful
        assert not errors, errors
        browser.close()
        passed('Moteur indisponible : erreur explicite, pas de faux export ni de remplacement par le master')
    return {'resultat': 'PASS', 'version': 'T2-v1', 'mode': 'public' if revision else 'local',
            'revision': revision, 'viewport_px': [320,568], 'master_sha256': mix['master_sha256'],
            'pistes_sha256': expected, 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    place = parser.add_mutually_exclusive_group(required=True)
    place.add_argument('--local', action='store_true')
    place.add_argument('--url')
    parser.add_argument('--revision', default='')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.local:
        class Quiet(Handler):
            def log_message(self, *args): pass
        with ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT))) as srv:
            Thread(target=srv.serve_forever, daemon=True).start()
            try:
                report = verify(f'http://127.0.0.1:{srv.server_port}/', '')
            finally:
                srv.shutdown()
    else:
        report = verify(args.url.rstrip('/') + '/', args.revision)
    if args.report:
        save(args.report, report)


if __name__ == '__main__':
    main()
