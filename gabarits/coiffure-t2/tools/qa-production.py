#!/usr/bin/env python3
"""Recette du MP4 réellement téléchargé. Aucun accès Internet autorisé dans le navigateur."""
import argparse
import base64
from functools import partial
from fractions import Fraction
import hashlib
from http.server import ThreadingHTTPServer
from io import BytesIO
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from threading import Thread
from urllib.parse import urlparse
from PIL import Image, ImageChops
from playwright.sync_api import expect, sync_playwright
from preview import Site

ROOT=Path(__file__).resolve().parents[1]
FF=os.getenv('FFMPEG','ffmpeg'); FP=os.getenv('FFPROBE','ffprobe')
MUSIC=json.loads((ROOT/'audio/music/catalogue.json').read_text())
SLOTS=['S1','S2','S3','S4']
EXAMPLES=json.loads((ROOT/'formulaire/exemples.json').read_text())['examples']
KEY='vv-coiffure-rotation-1:COIFFURE-T2:coiffure-en-etapes:1.0.0'

class Quiet(Site):
    def log_message(self,*args): pass
    def copyfile(self,source,outputfile):
        try:super().copyfile(source,outputfile)
        except (BrokenPipeError,ConnectionResetError):pass  # Un aperçu peut changer de source avant la fin du GET.

def run(*args,**kw):
    return subprocess.check_output(args,**kw)

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def probe(file,*args):
    return json.loads(run(FP,'-v','error',*args,'-of','json',str(file)))

def ahash(path):
    return run(FF,'-nostdin','-v','error','-i',str(path),'-map','0:a:0','-c','copy','-f','hash','-hash','sha256','-',text=True).strip().split('=')[1]

def check_movie(path,variant,ui_sha,private_literals):
    data=probe(path,'-show_streams','-show_format')
    assert [s['codec_type'] for s in data['streams']]==['video','audio'],data['streams']
    v,a=data['streams'];times=probe(path,'-select_streams','v:0','-show_packets','-show_entries','packet=pts')['packets']
    pts=sorted(int(t['pts']) for t in times)
    assert (v['codec_name'],v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']))==('h264',720,1280,'30/1',900)
    assert len(pts)==900 and all(Fraction(v['time_base'])*p==Fraction(i,30) for i,p in enumerate(pts))
    assert (a['codec_name'],a.get('profile'),int(a['sample_rate']),a['channels'])==('aac','LC',48000,2),a
    assert float(a['start_time'])==0 and float(a['duration'])==30 and float(data['format']['duration'])==30
    t=next(x for x in MUSIC['tracks'] if x['id']==variant)
    audio=ahash(path);assert audio==ahash(ROOT/'audio/music'/t['path']), 'AAC différent du fond du catalogue'
    tags=json.dumps(data['format'].get('tags',{}),ensure_ascii=False)
    assert t['source'] in tags and t['licence'] in tags
    assert all(s not in tags for s in private_literals if s)
    subprocess.run([FF,'-nostdin','-v','error','-xerror','-threads','2','-i',str(path),'-f','null','-'],check=True)
    assert sha(path)==ui_sha
    return {'file':path.name,'bytes':path.stat().st_size,'sha256':ui_sha,'frames':900,'fps':30,'seconds':30,'avc_width':720,'avc_height':1280,'audio':'aac-lc/48000/2','variant':variant,'audio_packet_sha256':audio,'music_only_aac_bit_identical':True,'metadata_contact_absent':True,'decoded_completely':True}

def frame(path,n):
    data=run(FF,'-nostdin','-v','error','-threads','2','-i',str(path),'-vf',f'select=eq(n\\,{n})','-frames:v','1','-f','image2pipe','-c:v','png','-threads','1','-')
    return Image.open(BytesIO(data)).convert('RGB')

def near_white(image,n=190):
    r,g,b=image.convert('RGB').split()
    return ImageChops.darker(ImageChops.darker(r,g),b).point(lambda x:255 if x>=n else 0)

def check_pixels(page,base,mp4,answers,variant,keys,onglerie=False):
    masks=page.evaluate('''async ({base,answers,variant,keys,onglerie})=>{
      const [res,model,paint]=await Promise.all(['assets/engine/resources.mjs','assets/texte/modele-visuel.mjs','assets/texte/lettrage.mjs'].map(p=>import(base+'/'+p)));
      const core=await res.loadCore();await paint.lettrageFonts(...await res.loadFonts(core));
      const habillage=onglerie?await res.readJson('formulaire/habillage-onglerie.json'):core.habillage;
      const plan=model.makeVisualPlan(model.normalizeVisual(answers,core.questions,core.font),variant,habillage);
      const all=paint.prepareCaptions(plan);
      const c=document.createElement('canvas');c.width=720;c.height=1280;
      const ctx=c.getContext('2d'), result=[];
      for(const key of keys){
        const item=all.find(x=>x.key===key);if(!item)throw Error('Calque de contrôle absent');
        const n=Math.min(item.off-2,item.on+14);ctx.clearRect(0,0,720,1280);
        paint.drawCaptions(ctx,[item],n);result.push({key,n,text:item.text,png:c.toDataURL().split(',')[1]});
      }return result;
    }''',{'base':base,'answers':answers,'variant':variant,'keys':keys,'onglerie':onglerie})
    results={}
    for item in masks:
        expected=Image.open(BytesIO(base64.b64decode(item['png']))).convert('RGBA')
        expected_mask=ImageChops.multiply(near_white(expected,213),expected.getchannel('A').point(lambda x:255 if x>=224 else 0))
        actual_mask=near_white(frame(mp4,item['n']))
        n=expected_mask.histogram()[255];actual=ImageChops.multiply(expected_mask,actual_mask).histogram()[255]
        assert n>=450 and actual/n>=.80,(item['key'],item['text'],item['n'],actual,n)
        results[item['key']]={'frame':item['n'],'expected_text':item['text'],'light_pixels_matching':round(actual/n,4)}
    if not answers['prix'] and not answers['salon'] and not answers['ville']:
        assert near_white(frame(mp4,893).crop((50,1190,675,1245))).histogram()[255]<120,'Un texte facultatif semble apparaître sans réponse.'
        results['optional_empty_band_checked']=True
    return results

def wait_ready(page):expect(page.locator('html')).to_have_attribute('data-ready','yes')

def screens(page,url,out):
    folder=out/'12-ecrans';folder.mkdir(exist_ok=True)
    for i in range(1,13):
        page.goto(f'{url}/simulation.html?ecran={i}');wait_ready(page)
        state='ABC'[(i-1)%3];slot=f'S{(i-1)//3+1}'
        expect(page.locator('#app')).to_have_attribute('data-state',state);expect(page.locator('#app')).to_have_attribute('data-prise',slot)
        assert page.evaluate('window.__capture().accepted')==[]
        video='#replay' if state=='C' else '#cam'
        page.wait_for_function('s=>document.querySelector(s).readyState>=2',arg=video)
        page.wait_for_function('s=>!document.querySelector(s).seeking',arg=video)
        if state in 'AC':expect(page.locator('#cta' if state=='A' else '#next')).to_be_disabled()
        page.evaluate('document.fonts.ready');img=Image.open(BytesIO(page.screenshot(animations='disabled')));img.convert('RGB').save(folder/f'{i:02d}.webp',quality=83)
    page.goto(url+'/ecrans.html#12');wait_ready(page);expect(page.locator('#screenLabel')).to_contain_text('Écran 12/12')
    assert page.locator('#screenList a').count()==12
    assert 'ecran=12' in page.locator('#screenAlone').get_attribute('href')
    return 12

def fill(page,url,answers,framing='profil',start=True):
    page.goto(url+'/');wait_ready(page)
    for key in ['service','geste','preuve','accroche','salon','ville','prix']:page.locator('#'+key).fill(answers.get(key,''))
    if answers.get('prix'):page.locator('#prixMode').select_option(answers.get('prixMode','fixe'))
    page.locator('#canal').select_option(answers.get('canal','aucun'))
    if answers.get('canal','aucun')!='aucun':
        page.locator('#contact').fill(answers['contact']);page.locator('#contactConfirme').set_checked(answers.get('contactConfirme',False))
    page.locator('#framing').select_option(framing);page.locator('#checkedCase').check()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    if start:
        page.locator('#startTest').click();page.wait_for_url('**/simulation.html?fiche=*');wait_ready(page)
        assert re.fullmatch('fiche=[a-f0-9]{32}',urlparse(page.url).query)

def ready_take(page):
    expect(page.locator('#app')).to_have_attribute('data-state','B');expect(page.locator('#cam')).to_be_visible()
    page.locator('#cam').evaluate('v=>{v.playbackRate=5;v.play().catch(()=>{});}')
    expect(page.locator('#next')).to_be_enabled(timeout=16000)
    expect(page.locator('#app')).to_have_attribute('data-state','C')

def current_rotation(page):return page.evaluate('key=>JSON.parse(localStorage.getItem(key)||"null")',KEY)

def await_out(page):
    page.wait_for_function("!document.querySelector('#resultPage').hidden||document.querySelector('#montageHeading').textContent==='Le montage n’a pas abouti'",timeout=164000)
    if page.locator('#resultPage').is_hidden():raise AssertionError(page.locator('#montageStatus').inner_text())

def download(page,path,slots,literals,listen=False):
    await_out(page);p=page.locator('#resultPage');expect(p).to_have_attribute('data-sources',str(slots))
    assert page.locator('#ad').get_attribute('src')==page.locator('#endDownload').get_attribute('href')
    assert page.locator('#ad').evaluate('v=>!v.muted')
    tag=p.get_attribute('data-track')
    with page.expect_download() as event:page.locator('#endDownload').click()
    event.value.save_as(path)
    result=check_movie(path,tag,p.get_attribute('data-sha256'),literals)
    if listen:
        page.locator('#replayAd').click();page.wait_for_function("document.querySelector('#ad').currentTime>0.75")
        info=page.locator('#ad').evaluate('v=>({audio: v.webkitAudioDecodedByteCount, video: v.videoWidth, rate: v.playbackRate})')
        assert info['audio']>0 and info['video']==720 and info['rate']==1
        page.locator('#ad').evaluate('v=>v.pause()');result['browser_audio_decoded']=True
    return result

def captures(page,clips,*,reuse=False,tiny=None,tone=None,demo=False):
    for i in range(1,5):
        sid=f'S{i}';expect(page.locator('#app')).to_have_attribute('data-prise',sid);expect(page.locator('#app')).to_have_attribute('data-state','A')
        if i==1 and tiny:
            page.locator('#takeFile').set_input_files(str(tiny));expect(page.locator('#mediaMessage')).to_contain_text('trop courte')
            assert page.evaluate('window.__capture().accepted')==[]
        def add():
            if reuse and i==3:
                page.locator('#reuseTake').click();expect(page.locator('#next')).to_have_text('VALIDER CE DÉTAIL');expect(page.locator('#next')).to_be_enabled(timeout=50000)
                expect(page.locator('#reviewMode')).to_contain_text('Geste recadré');expect(page.locator('#toggleTakeAudio')).to_be_hidden()
                assert 0<page.locator('#replay').evaluate('v=>v.duration')<7
            else:
                if demo:page.locator('#cta').click()
                else:page.locator('#takeFile').set_input_files(str(tone if i==3 and tone else clips/(sid+'.mp4')))
                ready_take(page)
                if i==3 and tone:
                    expect(page.locator('#toggleTakeAudio')).to_be_visible();page.locator('#toggleTakeAudio').click()
                    assert page.locator('#replay').evaluate('v=>!v.muted');page.locator('#toggleTakeAudio').click()
        add()
        if i==3 and (reuse or tone):
            page.locator('#redo').click();expect(page.locator('#app')).to_have_attribute('data-state','A');assert page.evaluate('window.__capture().accepted')==['S1','S2'];add()
        page.locator('#next').click()
    assert page.evaluate('window.__capture().accepted')==SLOTS

def camera(browser,url,gate):
    p=browser.new_page(viewport={'width':390,'height':820},permissions=['camera']);p.route('**/*',gate)
    fill(p,url,EXAMPLES[0]['answers']);p.locator('#cta').click();expect(p.locator('#app')).to_have_attribute('data-state','B')
    p.wait_for_function("document.querySelector('#cam').videoWidth===360")
    expect(p.locator('#next')).to_be_enabled(timeout=15000)
    assert p.locator('#cam').evaluate('v=>v.srcObject===null')
    d=p.locator('#replay').evaluate('v=>v.duration');assert d>=5.983
    p.locator('#next').click();assert p.evaluate('window.__capture().accepted')==['S1'];p.close()
    return {'device':'Chromium / mire factice 360x640','recorded_slot':'S1','replay_seconds':round(d,4),'stream_released':True}

def concurrency(browser,url,gate):
    context=browser.new_context();context.route('**/*',gate);p=context.new_page();q=context.new_page();p.goto(url);q.goto(url)
    p.evaluate('''async ({url})=>{
      const c=await (await import(url+'/assets/engine/resources.mjs')).loadCore();
      const {rotate}=await import(url+'/assets/engine/rotation.mjs');
      window.__first=rotate(c,'0'.repeat(32),new AbortController().signal,async v=>{
        document.documentElement.dataset.lock='held';await new Promise(r=>setTimeout(r,450));
        return {result:{job_id:'0'.repeat(32),music:{variant:v}}};
      });
    }''',{'url':url});p.wait_for_function("document.documentElement.dataset.lock==='held'")
    b=q.evaluate('''async url=>{
      const c=await (await import(url+'/assets/engine/resources.mjs')).loadCore();
      const {rotate}=await import(url+'/assets/engine/rotation.mjs');
      return (await rotate(c,'0'.repeat(31)+'1',new AbortController().signal,async v=>({result:{job_id:'0'.repeat(31)+'1',music:{variant:v}}}))).result.music.variant;
    }''',url)
    a=p.evaluate('async()=> (await window.__first).result.music.variant');assert a!=b and current_rotation(q)['last']==b
    context.close();return {'parallel_tabs':2,'variants':[a,b],'last_is_second':True}

def main():
    cli=argparse.ArgumentParser();cli.add_argument('--out',type=Path,required=True);cli.add_argument('--local-rushs',type=Path,help='Exporte un film de revue privé au lieu de la recette publique');options=cli.parse_args()
    out=options.out.resolve();out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp, ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT))) as s, sync_playwright() as pw:
        temp=Path(tmp); Thread(target=s.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{s.server_port}'
        flags=['--disable-dev-shm-usage','--autoplay-policy=no-user-gesture-required']
        if not options.local_rushs:
            y4m=temp/'test.y4m';subprocess.run([FF,'-y','-v','error','-f','lavfi','-i','testsrc2=size=360x640:rate=30','-t','1','-pix_fmt','yuv420p','-f','yuv4mpegpipe',str(y4m)],check=True)
            flags+=['--use-fake-device-for-media-stream',f'--use-file-for-fake-video-capture={y4m}','--use-fake-ui-for-media-stream']
        b=pw.chromium.launch(headless=True,args=flags,executable_path=os.getenv('CHROMIUM','/usr/bin/chromium'));ctx=b.new_context(viewport={'width':390,'height':820},accept_downloads=True);ctx.set_default_navigation_timeout(45000)
        page=ctx.new_page();page.set_default_timeout(10000);errors=[];external=[];fail_music=[False,0];posts=[]
        def gate(route):
            u=route.request.url
            if route.request.method not in ('GET','HEAD'):posts.append(route.request.method);route.abort();return
            if u.startswith(('blob:','data:')) or u.startswith(url+'/'):
                if fail_music[0] and re.search(r'/audio/music/fonds/[A-D]\.m4a$',u):
                    fail_music[0]=False;fail_music[1]+=1;route.fulfill(status=200,body=b'recette: octets corrompus');return
                route.continue_()
            else:external.append(u);route.abort()
        ctx.route('**/*',gate);page.on('pageerror',lambda e:errors.append(str(e)))
        qa={'revision':'2.0.3-rc.1','chromium':b.version,'viewport':[390,820],'physical_device_tested':False}
        clips=ROOT/'fixtures/media';ex1=dict(EXAMPLES[0]['answers']);ex2=dict(EXAMPLES[1]['answers'],canal='telephone',contact='+2290100000000',contactConfirme=True)
        if options.local_rushs:
            fill(page,url,ex1);captures(page,options.local_rushs)
            qa['local_private_review']=download(page,out/'COIFFURE-T2-R04-EXPORT-SANS-VOIX.mp4',4,['Tresses en carrés'],True)
        else:
            qa['screens']=screens(page,url,out);print('12 états de capture et galerie OK',flush=True)
            fill(page,url,dict(ex1,prix='12 34'),start=False);page.locator('#startTest').click();expect(page.locator('#formAlert')).to_contain_text('Tarif');assert not '/simulation.html' in page.url
            page.goto(url+'/simulation.html?fiche='+'a'*32);wait_ready(page);expect(page.locator('#testCurtain')).to_be_visible()
            tiny=temp/'court.mp4';tone=temp/'son-original.mp4'
            subprocess.run([FF,'-v','error','-i',str(clips/'S1.mp4'),'-c','copy','-t','2',str(tiny)],check=True)
            subprocess.run([FF,'-v','error','-i',str(clips/'S3.mp4'),'-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-t','7',str(tone)],check=True)
            fill(page,url,ex1);fail_music[0]=True;captures(page,clips,tiny=tiny,tone=tone)
            expect(page.locator('#montageRetry')).to_be_visible(timeout=50000)
            expect(page.locator('#montageStatus')).to_contain_text('fond musical')
            bad=current_rotation(page);assert bad['last'] is None and bad['pending'] and fail_music[1]==1
            page.locator('#montageRetry').click()
            p4=out/'Recette-quatre-prises.mp4';q4=download(page,p4,4,['Tresses en carrés'],True)
            after=current_rotation(page);assert after['recent'][0][0]==bad['pending']['id'] and after['last']==q4['variant']==bad['pending']['variant']
            q4['pixels']=check_pixels(page,url,p4,ex1,q4['variant'],['gesture','proof','service'])
            qa['four_imports']=q4;qa['audio_failure_retry_same_job']=True;qa['source_audio_reviewed_not_exported']=True;print('4 imports, relance, musique et pixels associés à la fiche OK',flush=True)
            fill(page,url,ex2,'detail');captures(page,clips,reuse=True)
            p3=out/'Recette-trois-prises.mp4';q3=download(page,p3,3,[ex2['contact'],ex2['salon'],ex2['service']]);assert q3['variant']!=q4['variant']
            expect(page.locator('#resultContact')).to_have_attribute('href','tel:+2290100000000')
            q3['pixels']=check_pixels(page,url,p3,ex2,q3['variant'],['gesture','proof','service','signature','price']);qa['three_imports']=q3
            print('3 imports avec relecture du détail, nouveau fond, tarif et signature incrustés OK',flush=True)
            history=current_rotation(page)
            page.goto(url+'/');wait_ready(page);page.locator('#sample').click();expect(page.locator('#source')).to_have_value('demo');page.locator('#startTest').click();wait_ready(page)
            captures(page,clips,demo=True);qa['technical_fixture']=download(page,out/'Recette-mires.mp4',4,[])
            assert current_rotation(page)==history and page.locator('#resultContact').is_hidden()
            expect(page.locator('#resultCredit')).to_contain_text('mires');qa['fixture_did_not_advance_rotation']=True
            print('Simulation autonome et historique des fonds inchangé',flush=True)
            qa['camera_simulated']=camera(b,url,gate);qa['concurrent_local_rotation']=concurrency(b,url,gate)
        assert not errors and not external and not posts,(errors,external,posts)
        qa.update(external_requests=0,posts=0,errors=0)
        b.close();s.shutdown()
    report=out/'Recette-integrale.json';report.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    print('Recette intégrale OK :',report,flush=True)

if __name__=='__main__':main()
