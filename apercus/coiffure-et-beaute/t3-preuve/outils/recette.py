#!/usr/bin/env python3
"""Recette des douze vues et des transitions ; aucune caméra ni réseau."""
import json
from pathlib import Path
import sys
import tempfile
import time
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright


def planche(root):
    W=1256; A=379; x0=38; gap=22; top=190; row=681
    img=Image.new('RGB',(W,top+row*4+53),'#edf1e6'); d=ImageDraw.Draw(img)
    fonts=Path('/usr/share/fonts/truetype/dejavu')
    def font(size,bold=False,serif=False):
        name='DejaVuSerif.ttf' if serif else ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')
        try:return ImageFont.truetype(str(fonts/name),size)
        except OSError:return ImageFont.load_default(size=size)
    d.rectangle((0,0,W,top-16),fill='#16372d'); d.rounded_rectangle((x0,27,93,59),radius=9,fill='#dfe9bd');d.text((65,43),'T3',anchor='mm',font=font(17,True),fill='#17362b')
    d.text((110,32),'VITRINE VIDÉO  /  COIFFURE ET BEAUTÉ',font=font(16,True),fill='#d7e7d1')
    d.text((x0,68),'Le parcours en 12 écrans',font=font(44,serif=True),fill='#fffced')
    d.text((x0,130),'4 prises · guide, chrono et relecture · exemple : soin du visage',font=font(19),fill='#d8e6d1')
    roles=['Guide','Chrono simulé','Relecture']; scenes=('Le départ','Le geste','Le détail','La dernière vue')
    for i in range(12):
        row_id,col=divmod(i,3); x=x0+col*(A+gap); y=top+row_id*row
        d.rounded_rectangle((x,y,x+A,y+row-16),radius=16,fill='#fbfaf1',outline='#ccd9ca',width=2)
        d.text((x+14,y+14),f'{i+1:02d}  ·  {roles[col]}',font=font(20,True),fill='#234b3b')
        d.text((x+14,y+45),f'S{row_id+1} · {scenes[row_id]}',font=font(16),fill='#54705e')
        with Image.open(root/f'capture/ecrans/{i+1:02d}.jpg') as image:
            image.thumbnail((A-22,row-98),Image.Resampling.LANCZOS); img.paste(image,(x+(A-image.width)//2,y+75))
    d.text((x0,top+4*row+7),'Revue r1  ·  Extraits du film déjà monté, caméra et micro non déclenchés.',font=font(15),fill='#3b5a4b')
    img.save(root/'capture/planche-12-ecrans.jpg',quality=88,optimize=True)


def run(root):
    cfg=json.loads((root/'capture/guide.json').read_text()); expected=[(s['id'],role) for s in cfg['scenes'] for role in ('A','B','C')]
    uri=(root/'index.html').as_uri(); faults=[]; remote=[]; vista=[]; tested=[]
    with sync_playwright() as p, tempfile.TemporaryDirectory(prefix='qa12-') as temp:
        br=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--mute-audio']); co=br.new_context(viewport={'width':390,'height':844},device_scale_factor=1,offline=True); page=co.new_page()
        page.on('pageerror',lambda e:faults.append(str(e)));page.on('request',lambda e:remote.append(e.url) if e.url.startswith(('http://','https://')) else None)
        def check(where,pred,ms=6500):
            limit=time.monotonic()+ms/1000
            while time.monotonic()<limit:
                a=where.locator('body').evaluate('()=>window.etatT3?.()');
                if a and pred(a):return a
                page.wait_for_timeout(45)
            raise AssertionError((a,faults))
        for n,(s,role) in enumerate(expected,1):
            page.goto(uri+f'#ecran-{n:02d}',wait_until='domcontentloaded'); assert page.locator('#nav button').count()==12
            q=check(page,lambda z:z['ecran']==n); assert (q['scene'],q['role'])==(s,role)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'); assert page.locator('#nav [aria-current]').count()==1
            view=page.locator('#telephone'); box=view.bounding_box(); assert 320<box['width']<=390 and 560<box['height']<765
            if role=='B': assert page.locator('#clock').is_visible() and page.locator('#cancel').is_visible()
            if role=='C': assert page.locator('#keep').is_disabled() and page.locator('.qa-label').is_visible()
            view.screenshot(path=root/f'capture/ecrans/{n:02d}.jpg',type='jpeg',quality=87,animations='disabled')
            vista.append({'numero':n,'prise':s,'role':role,'capture':f'capture/ecrans/{n:02d}.jpg','largeur_css':round(box['width'],1),'hauteur_css':round(box['height'],1)})
        # Cadre opaque analogue au lecteur de fichiers. Le HTML, posters et vidéo fonctionnent hors ligne.
        fixture=Path(temp)/'cadre.html'; h=(root/'index.html').read_text(encoding='utf-8'); srcdoc=h.replace('&','&amp;').replace('"','&quot;'); fixture.write_text(f'<body style="margin:0"><iframe title="Douze écrans" sandbox="allow-scripts" style="width:390px;height:844px;border:0" srcdoc="{srcdoc}"></iframe>',encoding='utf-8'); page.goto(fixture.as_uri(),wait_until='load'); fr=page.frame_locator('iframe'); assert fr.locator('#nav button').count()==12
        fr.locator('[data-screen="12"]:is(button)').click(); check(fr,lambda a:a['ecran']==12); assert fr.locator('#keep').is_disabled() and fr.locator('#complete').count()==0
        fr.locator('#tour').click(); check(fr,lambda a:a['ecran']==1 and not a['kept']); fr.locator('#start').click();check(fr,lambda a:a['ecran']==2 and a['playing']);fr.locator('#cancel').click();check(fr,lambda a:a['ecran']==1 and a['candidate'] is None and not a['kept'])
        for i,s in enumerate(cfg['scenes']):
            a,b=[n/cfg['film']['fps'] for n in s['extrait_images']]; ga=i*3+1; bc=ga+1; ck=ga+2
            def take():
                fr.locator('#start').click(); first=check(fr,lambda z:z['ecran']==bc and z['ready']>=2 and z['playing'] and z['time']>=a-.017); assert first['time']<min(a+1.,b-.2)
                t=check(fr,lambda z:z['ecran']==ck and z['candidate']==s['id'],ms=int(1000*(b-a)+4000)); assert s['id'] not in t['kept']; return first['time']
            t1=take()
            if i==2:
                fr.locator('#retry').click();check(fr,lambda z:z['ecran']==ga and z['candidate'] is None and z['kept']==['S1','S2']);take()
            fr.locator('#play').click(); first=check(fr,lambda z:z['ecran']==ck and z['playing'] and z['time']>=a-.017); assert first['time']<min(a+1.,b-.2)
            fr.locator('#keep').click();check(fr,lambda z:s['id'] in z['kept'] and z['ecran']==(ga+3 if i<3 else ck)); tested.append({'prise':s['id'],'chrono_et_relecture_video_lus':True,'debut_extrait_s':a,'premiere_lecture_chrono_s':t1,'premiere_relecture_s':first['time']})
        assert check(fr,lambda z:z['filmDispo'])['kept']==['S1','S2','S3','S4'];fr.locator('#complete').click();assert fr.locator('#film').is_visible(); fr.locator('#film-player').evaluate('v=>v.play()');fr.locator('#film-player').evaluate('v=>{v.currentTime=24.5}');
        assert fr.locator('#film-player').evaluate('v=>v.duration')==30
        fr.locator('#film button').click();assert not fr.locator('#film').is_visible()
        d=br.new_page(viewport={'width':1260,'height':930},offline=True); d.goto(uri+'#ecran-08',wait_until='domcontentloaded'); assert d.locator('#telephone').get_attribute('data-role')=='B'; assert d.locator('#inspect').is_visible() and d.evaluate('document.documentElement.scrollWidth<=innerWidth'); br.close()
        assert not remote and not faults,(remote,faults)
    planche(root)
    (root/'rapports/Controle-12-ecrans.json').write_text(json.dumps({'revision':'revue-parcours-r1','vues':vista,'lecture_4_extraits':tested,'navigation_complete':True,'annulation_protege_les_autres_prises':True,'reprise_s3_preserve_s1_s2':True,'relecture_apres_chrono':True,'raccourci_sans_validation_fictive':True,'film_seulement_apres_les_4':True,'mobile_css':[390,844],'bureau_css':[1260,930],'iframe_allow_scripts_sans_reseau':True,'photos_extraites_du_montage':True,'duree_film_s':30,'camera_physique_testee':False,'original_son_dans_exemple':False,'requetes_http_involontaires':remote,'erreurs_js':faults},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('12 vues, 4 chronos et relectures, annuler/refaire/garder, film à la fin : PASS.',flush=True)


if __name__=='__main__':run(Path(sys.argv[1]).resolve())
