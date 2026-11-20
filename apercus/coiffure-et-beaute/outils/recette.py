#!/usr/bin/env python3
"""Recette navigateur sur les prises filmées de l’aperçu. Serveur local lancé séparément."""
import argparse, hashlib, json, os, re, subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from playwright.sync_api import sync_playwright, expect

BASE=Path(__file__).resolve().parents[1]
SITE=BASE/'site'
FF=os.environ.get('FFMPEG','ffmpeg')
PROBE=os.environ.get('FFPROBE','ffprobe')
METIERS=['coiffure','manucure','pedicure','visage','corps','maquillage','regard','autre']
CASES={'manucure':('Pose de vernis rouge','Poser le vernis au pinceau','Le bord net du vernis','main'),
       'visage':('Pose d’un masque visage','Étaler le masque à la spatule','Une couche régulière','visage')}

def ready(p):
    expect(p.locator('html')).to_have_attribute('data-ready','yes',timeout=13000)

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def probe(path):
    return json.loads(subprocess.check_output([PROBE,'-v','error','-show_streams','-show_format','-of','json',str(path)]))

def ahash(path):
    return subprocess.check_output([FF,'-hide_banner','-v','error','-nostdin','-i',str(path),'-map','0:a:0','-c','copy','-f','hash','-']).decode().strip()

def caption_file(version,tag):
    return (SITE/'t1/media/afrobeat'/f'{tag}.m4a') if version=='t1' else (SITE/'t2/audio/music/fonds'/f'{tag}.m4a')

def fit(page):
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')


def check_forms(p,origin):
    p.goto(origin);fit(p)
    expect(p.locator('[name=metier]')).to_have_count(len(METIERS));expect(p.locator('#ouvrirT1')).to_be_disabled();expect(p.locator('#ouvrirT2')).to_be_disabled()
    p.get_by_text('Maquillage',exact=True).first.click()
    p.locator('#ouvrirT2').click();ready(p);expect(p.locator('#metier')).to_have_value('maquillage')
    p.locator('#home').click();expect(p.locator('[name=metier][value=maquillage]')).to_be_checked()
    p.get_by_text('Pédicure esthétique',exact=True).first.click();p.locator('#ouvrirT1').click();ready(p);expect(p.locator('#metier')).to_have_value('pedicure')
    checks=[]
    for version in ('t1','t2'):
        for metier in METIERS:
            p.goto(f'{origin}/{version}/index.html?metier={metier}');ready(p);fit(p)
            expect(p.locator('#metier')).to_have_value(metier);expect(p.locator('#source')).to_have_value('client');expect(p.locator('#service')).to_have_value('')
            assert p.locator('#source option[value=demo]').evaluate('x=>x.disabled')==(metier not in ('coiffure','manucure','visage'))
            # Les exemples de réponses, y compris accentués, passent le formulaire et restent dans l’onglet.
            for field in ['service'] if version=='t1' else ['service','geste','preuve']:
                p.locator('#'+field).fill(p.locator('#'+field).get_attribute('placeholder').removeprefix('Ex. '))
            p.locator('#salon').fill('Établissement de test');p.locator('#ville').fill('Cotonou')
            if version=='t1':p.locator('#consent').check()
            p.locator('#checkedCase').check();p.locator('#startTest').click();p.wait_for_url('**/simulation.html?**');ready(p)
            expect(p.locator('#app')).to_have_attribute('data-prise','S1');expect(p.locator('#app')).to_have_attribute('data-state','A')
            assert 'Établissement' not in p.url and 'Cotonou' not in p.url and p.locator('#cam').get_attribute('src') is None
            params=parse_qs(urlparse(p.url).query);assert params['metier']==[metier] and re.fullmatch(r'[0-9a-f]{32}',params['fiche'][0])
            expect(p.locator('#editFiche')).to_have_attribute('href',re.compile(f'metier={metier}'))
            checks.append({'atelier':version,'metier':metier,'fiche':'acceptée','prise':'S1_A'})
    return checks


def bitrate_check(path,version,tag):
    meta=probe(path);v,a=meta['streams'];assert (v['codec_name'],v['width'],v['height'],v['nb_frames'],v['r_frame_rate'])==('h264',720,1280,'900','30/1'),v
    assert abs(float(meta['format']['duration'])-30)<.025,meta['format']['duration']
    assert (a['codec_name'],a['sample_rate'],a['channels'])==('aac','48000',2)
    assert ahash(path)==ahash(caption_file(version,tag)),tag
    subprocess.run([FF,'-hide_banner','-v','error','-nostdin','-xerror','-threads','2','-i',str(path),'-f','null','-'],check=True)
    return {'h264':'720x1280','frames':900,'duration_s':float(meta['format']['duration']),'aac_paquets_identiques':True,'decode_integral':True,'sha256':sha(path),'bytes':path.stat().st_size}


def match_sample(p,sel,path):
    got=p.locator(sel).evaluate('''async v=>{const b=await (await fetch(v.currentSrc||v.src)).arrayBuffer();return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b)),v=>v.toString(16).padStart(2,'0')).join('');}''')
    assert got==sha(path), (sel,path,got)


def add_take(p,version,metier,i,demo):
    slot=f'S{i}';shots=SITE/'exemples'/metier;app=p.locator('#app')
    expect(app).to_have_attribute('data-prise',slot);expect(app).to_have_attribute('data-state','A')
    if i==1:expect(p.locator('#listFilm')).to_contain_text(CASES[metier][3])
    if demo:p.locator('#cta').click()
    else:p.locator('#takeFile').set_input_files(shots/(slot+'.mp4'))
    expect(app).to_have_attribute('data-state','B',timeout=14000)
    p.wait_for_function('document.querySelector("#cam").currentTime>.12&&parseFloat(document.querySelector("#barFill").style.width)>0',timeout=14000)
    p.locator('#cam').evaluate('v=>{v.playbackRate=5;}')
    expect(app).to_have_attribute('data-state','C',timeout=18000);expect(p.locator('#next')).to_be_enabled(timeout=12000)
    p.wait_for_function('document.querySelector("#replay").currentTime>.18')
    if i==1 or i==3 or i==4:match_sample(p,'#replay',shots/(slot+'.mp4'))


def export(p,origin,version,metier,demo,out,reuse=False):
    service,geste,preuve,word=CASES[metier]
    p.goto(f'{origin}/{version}/index.html?metier={metier}');ready(p);fit(p)
    if demo:
        p.locator('#source').select_option('demo');expect(p.locator('#service')).to_have_value(service)
    else:
        for key,val in {'salon':'Atelier de recette','ville':'Cotonou','service':service}.items():p.locator('#'+key).fill(val)
        if version=='t1':
            p.locator('#consent').check();p.locator('[name=resultatChoix][value=autre]').check();p.locator('#resultatAutre').fill('Les ongles vernis en rouge.')
        else:
            p.locator('#geste').fill(geste);p.locator('#preuve').fill(preuve)
            p.locator('#canal').select_option('telephone');p.locator('#contact').fill('+229 019 999 0000');p.locator('#contactConfirme').check()
    if version=='t1' or not demo:p.locator('#checkedCase').check()
    p.locator('#startTest').click();p.wait_for_url('**/simulation.html?**');ready(p)
    states=[]; declined=False
    for i in range(1,5):
        if i==3 and reuse:
            p.locator('#reuseTake').click();expect(p.locator('#app')).to_have_attribute('data-detail-preview','true',timeout=45000);expect(p.locator('#next')).to_be_enabled()
            assert p.evaluate('!window.__capture().accepted.includes("S3")')
            p.locator('#redo').click();expect(p.locator('#app')).to_have_attribute('data-state','A');declined=True
            p.locator('#reuseTake').click();expect(p.locator('#app')).to_have_attribute('data-detail-preview','true',timeout=45000);expect(p.locator('#next')).to_be_enabled()
            p.wait_for_function('document.querySelector("#replay").currentTime>.22')
        else:add_take(p,version,metier,i,demo)
        states+= [f'S{i}_{x}' for x in 'ABC'];p.locator('#next').click()
    p.wait_for_function('''({v})=> (v==='t1'?!document.querySelector('#montageGo').disabled:!document.querySelector('#resultPage').hidden)||document.querySelector('#montageHeading').textContent==='Le montage n’a pas abouti' ''',arg={'v':version},timeout=169000)
    assert p.locator('#montageHeading').text_content()!='Le montage n’a pas abouti',p.locator('#montageStatus').text_content()
    if version=='t1':p.locator('#montageGo').click()
    media=p.locator('#ad');p.wait_for_function('document.querySelector("#ad").readyState>=2')
    if version=='t2':p.locator('#replayAd').click()
    p.wait_for_function('document.querySelector("#ad").currentTime>.2 && document.querySelector("#ad").videoWidth===720');media.evaluate('v=>v.pause()')
    assert media.get_attribute('src')==p.locator('#endDownload').get_attribute('href')
    if version=='t1':p.locator('#adClose').click();meta=p.locator('#endMeta')
    else:
        meta=p.locator('#resultPage')
        if demo:expect(p.locator('#resultContact')).to_be_hidden()
        else:expect(p.locator('#resultContact')).to_have_attribute('href','tel:+2290199990000')
    expect(meta).to_have_attribute('data-sources','3' if reuse else '4');expect(meta).to_have_attribute('data-frames','900')
    tag=meta.get_attribute('data-track');assert tag
    with p.expect_download() as dl:p.locator('#endDownload').click()
    dl.value.save_as(out)
    rec=bitrate_check(out,version,tag);ui_sha=meta.get_attribute('data-sha256');assert not ui_sha or ui_sha==rec['sha256']
    if version=='t2' and not demo:
        assert '0199990000' not in json.dumps(probe(out))
    return {'atelier':version,'metier':metier,'source':'exemple filmé' if demo else 'import de prises filmées',
            'ecrans':states,'reemploi_s3':reuse,'refus_puis_relecture':declined,'audio':tag,'lecteur_et_telechargement':'même fichier',**rec}


def check_gallery(p, origin):
    out=[]
    for v in ('t1','t2'):
        for metier in ('coiffure','manucure','visage'):
            p.goto(f'{origin}/{v}/ecrans.html?metier={metier}');ready(p);fit(p)
            expect(p.locator('[data-ecran]')).to_have_count(12);expect(p.locator('#film')).to_be_visible()
            folder='coiffure-'+v if metier=='coiffure' else metier
            for n in range(1,13):
                p.locator('#screenSelect').select_option(str(n));frame=p.frame_locator('#screenLive');state='ABC'[(n-1)%3];i=(n-1)//3+1
                expect(frame.locator('#app')).to_have_attribute('data-prise','S'+str(i),timeout=11000);expect(frame.locator('#app')).to_have_attribute('data-state',state)
                expect(frame.locator('#next')).to_be_disabled();expected=f'{origin}/exemples/{folder}/S{i}.mp4';vsel='#replay' if state=='C' else '#cam'
                expect(frame.locator(vsel)).to_have_attribute('src',expected)
                p.wait_for_function('''({sel,src,clock})=>{const d=document.querySelector('#screenLive').contentDocument;const v=d?.querySelector(sel);return v?.src===src&&v.readyState>=2&&(!clock||v.currentTime>.16&&!v.paused);}''',arg={'sel':vsel,'src':expected,'clock':state!='A'},timeout=12000)
            with p.expect_download() as dl:p.locator('#downloadDemo').click()
            assert dl.value.suggested_filename.endswith('.mp4')
            p.locator('#film').evaluate('v=>v.play()');p.wait_for_function('document.querySelector("#film").currentTime>.24')
            p.locator('#film').evaluate('v=>v.pause()')
            out.append({'atelier':v,'metier':metier,'ecrans':12,'lectures_effectives':8,'validation_possible':False,'lecture_film':True})
        p.goto(f'{origin}/{v}/ecrans.html?metier=pedicure#3');ready(p)
        f=p.frame_locator('#screenLive');expect(f.locator('#sansExtrait')).to_be_visible();expect(f.locator('#next')).to_be_disabled();expect(p.locator('#resultat')).to_be_hidden()
    return out


def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--url',default='http://127.0.0.1:8112');a.add_argument('--phase',choices=['films','imports','galerie'],required=True);a.add_argument('--work',type=Path,required=True);a.add_argument('--mode',choices=['t1','t2','all'],default='all');args=a.parse_args()
    origin=args.url.rstrip('/');args.work.mkdir(parents=True,exist_ok=True)
    errors,blocked,fails,report=[],[],[],{}
    def gate(route):
        r=route.request
        if r.method not in ('GET','HEAD') or not r.url.startswith(origin+'/'):blocked.append(r.url);route.abort()
        else:route.continue_()
    with sync_playwright() as pw:
        b=pw.chromium.launch(args=['--no-sandbox']);c=b.new_context(viewport={'width':390,'height':843},accept_downloads=True,service_workers='block');c.route('**/*',gate);p=c.new_page();p.set_default_timeout(16000)
        p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:fails.append([r.status,r.url]) if r.status>=400 else None)
        report['chromium']=b.version
        if args.phase=='galerie':
            report['fiches']=check_forms(p,origin);print('Fiches : 8 métiers × 2 ateliers',flush=True)
            report['galeries']=check_gallery(p,origin);print('Galeries : 72 écrans, 48 lectures des prises',flush=True)
        else:
            versions=['t1','t2'] if args.mode=='all' else [args.mode]
            results=[]
            for v in versions:
                for met in (CASES if args.phase=='films' else ['manucure']):
                    dest=(SITE/'exemples'/met/f'film-{v}.mp4') if args.phase=='films' else (args.work/f'import-{v}-{met}.mp4')
                    row=export(p,origin,v,met,args.phase=='films',dest,reuse=args.phase=='imports' and v=='t2')
                    results.append(row);print(f'{v} · {met} : {row["frames"]} images · {row["duration_s"]} s · fond {row["audio"]}',flush=True)
            report['films']=results
        c.close();b.close()
    report.update(erreurs_js=errors,requetes_bloquees=blocked,erreurs_http=fails)
    name=f'Controle-{args.phase}'+('' if args.mode=='all' else '-'+args.mode)+'.json'
    (BASE/'recette'/name).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert not errors and not blocked and not fails, (errors,blocked,fails)

if __name__=='__main__':main()
