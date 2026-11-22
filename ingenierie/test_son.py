"""Recette technique : signaux de test provisoires, jamais publiés comme des musiques."""
import functools
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import threading

import pytest

from core import CASE, HERE, PLAN, ROOT, load, sha, validate
from mixage import PLAN_SON, image_hash, render, run, selected_tracks, timing
from serve import Handler


def test_un_catalogue_incomplet_ne_part_pas():
    plan = {**load(PLAN_SON), 'pistes': []}
    with pytest.raises(ValueError, match='exactement quatre'):
        selected_tracks(plan, Path('/dossier-test-inexistant'))


def test_ordre_et_licence_bloquent_les_sources_non_autorisees():
    cfg = load(PLAN_SON)
    first, *rest = cfg['pistes']
    missing = Path('/dossier-test-inexistant')
    with pytest.raises(ValueError, match='dans l’ordre'):
        selected_tracks({**cfg, 'pistes': [*rest, first]}, missing)
    with pytest.raises(ValueError, match='licence commerciale'):
        selected_tracks({**cfg, 'pistes': [{**first, 'licence': 'https://creativecommons.org/licenses/by-nc/4.0/'}, *rest]}, missing)
    with pytest.raises(ValueError, match='0:00'):
        selected_tracks({**cfg, 'pistes': [{**first, 'depuis_s': 1.2}, *rest]}, missing)


def test_attaque_originale_prioritaire_sur_le_calage():
    case, plan = validate(load(CASE), load(PLAN))
    attack = {'bpm': 118, 'temps_fort_s': .09, 'depart_original': True}
    sync = timing(attack, case, plan)
    assert sync['debut_s'] == 0 and sync['depart_original']
    assert len(sync['ecart_grille_iris_ms']) == 2
    with pytest.raises(ValueError, match='0:00'):
        timing({**attack, 'depuis_s': 1.4}, case, plan)


def test_pulsation_plus_lente_preservee():
    case, plan = validate(load(CASE), load(PLAN))
    sync = timing({'bpm': 98.22, 'temps_fort_s': .04}, case, plan)
    assert 1 <= sync['vitesse'] <= 1.10
    assert sync['bpm_sortie'] == 105.556
    assert sync['ecart_grille_iris_ms'] == [0, 0]


@pytest.fixture(scope='module')
def banc(tmp_path_factory):
    base = tmp_path_factory.mktemp('quatre-signaux-de-test')
    tracks = []
    cfg = load(PLAN_SON)
    for i, (source, bpm) in enumerate(zip(cfg['pistes'], [110, 118, 122, 126], strict=True)):
        f = base / f'signal-{i}.wav'
        run('-f', 'lavfi', '-i', f'sine=f={128+31*i}:d=40', '-af', f'tremolo=f={bpm/60}:d=0.8', f)
        tracks.append({**source, 'titre': f'Signal de test {i+1}', 'auteur': 'Fixture technique',
                       'fichier': f.name, 'sha256': sha(f), 'intro_0_3_s': 'Signal synthétique, pas une sélection',
                       'bpm': bpm, 'temps_fort_s': .22, 'depuis_s': 0})
    manifest = base / 'plan-de-test.json'
    manifest.write_text(json.dumps({**cfg, 'pistes': tracks}))
    site = base / 'site'
    subprocess.run([sys.executable, str(HERE / 'mixage.py'), '--sources', str(base), '--plan-son', str(manifest),
                    '--demo', str(site)], check=True)
    case, plan = validate(load(CASE), load(PLAN))
    master = ROOT / 'media' / case['sortie']['file']
    mixed = site / 'media' / 'afrobeat'
    qa = load(site / 'ingenierie' / 'recette-sonore.json')
    assert qa['resultat'] == 'PASS' and qa['master_sha256'] == sha(master)
    assert len(list(mixed.glob('*.mp4'))) == 4 and not list(site.rglob('*.wav'))
    assert {image_hash(f) for f in mixed.glob('*.mp4')} == {image_hash(master)}
    for name in ('S1.mp4', 'S2.mp4', 'S3.mp4', 'S4.mp4', master.name):
        (site / 'media' / name).symlink_to(ROOT / 'media' / name)
    for src in (ROOT / 'assets').iterdir():
        f = site / 'assets' / src.name
        if not f.exists():
            f.symlink_to(src)
    for name in ('plan.json','prises-web.js'):
        (site / 'ingenierie' / name).symlink_to(HERE / name)
    for name in ('film.html', 'simulation.html', 'cas-demo.js'):
        (site / name).symlink_to(ROOT / name)
    return base, site, tracks, case, plan, master


def test_export_et_voix(banc):
    base, site, tracks, case, plan, master = banc
    src = base / tracks[0]['fichier']
    voice = base / 'signal-voix.wav'
    run('-f', 'lavfi', '-i', 'sine=f=440:d=3', voice)
    report = render(master, src, tracks[0], base / 'mix-avec-signal-voix.mp4', case, plan, voice)
    assert report['voix'] and report['duree_s'] == 30 and report['dbtp'] <= -1
    assert 114 <= report['bpm_sortie'] <= 126


def test_lecteur_et_un_montage(banc):
    pw = pytest.importorskip('playwright.sync_api')
    _, site, tracks, case, _, master = banc

    class Quiet(Handler):
        def log_message(self, *args): pass

    with ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(site))) as srv:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        u = f'http://127.0.0.1:{srv.server_port}/'
        try:
            with pw.sync_playwright() as p:
                b = p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
                ctx = b.new_context(viewport={'width': 320, 'height': 568}, accept_downloads=True)
                page = ctx.new_page()
                errors = []
                page.on('pageerror', lambda err: errors.append(str(err)))
                page.add_init_script('Math.random = () => 0;')
                page.goto(u + 'film.html')
                one = f'media/afrobeat/{tracks[0]["id"]}.mp4'
                two = f'media/afrobeat/{tracks[1]["id"]}.mp4'
                pw.expect(page.locator('#download')).to_have_attribute('href', one)
                pw.expect(page.locator('#retirer')).to_be_visible()
                pw.expect(page.locator('#sonLicence')).to_have_attribute('href', tracks[0]['licence'])
                pw.expect(page.locator('#sonSource')).to_have_attribute('href', tracks[0]['source'])
                page.locator('#retirer').click()
                pw.expect(page.locator('#download')).to_have_attribute('href', two)
                page.wait_for_function('document.getElementById("clip").currentTime > 0.1')
                page.locator('#clip').evaluate('v => v.pause()')
                with page.expect_download() as d:
                    page.locator('#download').click()
                assert d.value.suggested_filename == Path(two).name
                assert sha(d.value.path()) == sha(site / two)
                page.reload()
                pw.expect(page.locator('#download')).to_have_attribute('href', two)
                page.locator('#muet').click()
                pw.expect(page.locator('#tirageActions')).to_be_hidden()
                pw.expect(page.locator('#clip')).to_have_attribute('src', f'media/{master.name}')

                page.route('**/media/afrobeat/*.mp4', lambda r: r.abort())
                page.goto(u + 'film.html')
                pw.expect(page.locator('#filmMessage')).to_contain_text('master muet')
                pw.expect(page.locator('#clip')).to_have_attribute('src', f'media/{master.name}')
                page.unroute('**/media/afrobeat/*.mp4')

                page.goto(u + f'simulation.html?test={case["id"]}')
                page.locator('#cam').evaluate('v => {v.defaultPlaybackRate=5;v.playbackRate=5;}')
                for _ in case['scenes']:
                    page.locator('#cta').click()
                    pw.expect(page.locator('#next')).to_be_enabled(timeout=12000)
                    page.locator('#next').click()
                pw.expect(page.locator('#montageGo')).to_be_enabled(timeout=120000)
                page.locator('#montageGo').click()
                pw.expect(page.locator('#adBadge')).to_contain_text('Avec musique')
                page.wait_for_function('document.getElementById("ad").currentTime > .15')
                el = page.locator('#ad')
                assert el.evaluate('v => !v.muted && Math.abs(v.duration-30)<.04')
                same_file = el.get_attribute('src')
                el.evaluate('v => v.pause()')
                page.locator('#adClose').click()
                pw.expect(page.locator('#endDownload')).to_have_attribute('href', same_file)
                pw.expect(page.locator('#endLicence')).to_be_visible()
                assert same_file.startswith('blob:')
                page.locator('#restart').click()
                pw.expect(page.locator('#sceneCounter')).to_have_text('SCÈNE 1/4')
                assert page.evaluate('window.__demo.validations().length') == 0 and not errors
                b.close()
        finally:
            srv.shutdown()
