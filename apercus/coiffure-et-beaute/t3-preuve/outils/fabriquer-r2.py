#!/usr/bin/env python3
"""T3, revue locale r2. Recompose la référence Signature épinglée, sans Git ni authentification."""
from argparse import ArgumentParser
from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor
from hashlib import file_digest, sha1
from html import escape
import json
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory
from urllib.request import urlopen

HERE=Path(__file__).resolve().parent
T3=HERE.parent
REF='1c8128d701ef163b4fd7c37e4cb03911872f36e8'
REPO='bigmisericorde-blip/vitrine-video-coiffure-signature'
ROOT='apercus/coiffure-et-beaute/site'
RAW=f'https://raw.githubusercontent.com/{REPO}/{REF}/{ROOT}/'
GALLERY=f'https://rawcdn.githack.com/{REPO}/{REF}/{ROOT}/'
MASTER='T3-Essai-P2-r3-muet.mp4'
MASTER_SHA='685d2a560aaca265407b596c8ba90bd9e6887488746424bf5c44d2e472e19f03'
BLOBS={
 't2/ecrans.html':'fde7dd54917eda316fd1015ccc92b3e696d9abce',
 't2/simulation.html':'b17814d879aa90b48d60df5021ab23ff5b6ad5c3',
 't2/assets/web.css':'2a3d7843206b18a70c4988432e2eb1575c5f6623',
 't2/assets/simulation-t2.css':'032687365fae75347bc9c1e954a914e7975770be',
 'commun/atelier.css':'2787853d637384e34e0286272a7fbfb8aa802f23',
 't2/assets/Manrope.ttf':'75274da58537d6123b14f2cd0c355ad4681fc2b3',
 't2/assets/IBMPlexMono-Medium.ttf':'33c546f68b6007a45a3f10e845523abb2db25399',
 't2/assets/Montserrat-Variable.ttf':'c97aca18592834d8706549c279cb8d5ac5d85f69',
 't2/assets/PlusJakartaSans-Variable.ttf':'0cb13a998ed525ba226d911b10d6c4c4f923a961',
 't2/assets/OFL.txt':'793d053a8ff58d7185913fc7a33903b58a9826ba',
 't2/assets/OFL-Plex.txt':'670c6c04ec17a19131aefbb47472a11c2a5d831c',
 't2/assets/OFL-Montserrat.txt':'3344bfd4619241f1a83f6431cb8e5c16ce57d2f2',
 't2/assets/OFL-PlusJakartaSans.txt':'cd444675c2836662f94e266a2e5a0d40198e3ae7',
}
LABELS=('Départ','Geste','Détail','Dernière vue')
STAGES=('A_GUIDE','B_RECORDING','C_REVIEW')
MIXKIT={52143:'a-young-woman-laying-on-a-relaxing-spa-bed-receives-52143',52148:'a-young-beautiful-woman-laying-on-the-spa-bed-receives-52148',52157:'young-woman-getting-a-facial-massage-52157',52150:'a-young-woman-with-her-eyes-shut-receives-a-relaxing-52150'}
OUT_CSS='''
/* Hors des douze écrans : écran seul, parcours d’essai et pages documentaires. */
#vv-solo{height:100dvh;display:flex;flex-direction:column;background:#04191b}
.vv-bar{display:flex;justify-content:space-between;align-items:center;gap:12px;font-size:12px;color:var(--mint);padding:10px max(12px,calc((100% - 420px)/2));border-bottom:1px solid var(--border)}
.vv-bar a{font-weight:800;white-space:nowrap}.vv-bar span{text-align:right}
#vv-solo-frame{display:block;width:100%;min-height:0;flex:1;border:0}
.vv-solo{overflow:hidden}.vv-aux{padding-top:30px}.vv-aux .card{max-width:720px}.vv-aux li{padding:4px 0}.vv-aux li span{color:var(--mint)}.vv-aux p{margin:0 0 12px}
.vv-aux h1{font-size:clamp(37px,7vw,56px);margin:14px 0 20px}
.vv-aux table{width:100%;table-layout:fixed;border-collapse:collapse;overflow-wrap:anywhere;margin:14px 0}
.vv-aux th,.vv-aux td{border-bottom:1px solid var(--border);padding:8px;vertical-align:top;text-align:left}
.vv-planche img{display:block;width:100%;height:auto;border-radius:10px}
.vv-aux th{color:var(--mint)}.vv-aux th:first-child{width:34px}
@media(max-width:480px){.vv-aux th,.vv-aux td{font-size:12px;padding:6px}.vv-aux th:first-child{width:25px}}

'''
IN_CSS='''
/* Un bouton d’annulation est accessible uniquement dans le parcours d’essai. */
.record-stop{pointer-events:auto;position:absolute;right:12px;bottom:37px;border:1px solid #538577;border-radius:999px;padding:7px 12px;background:#062629ee;color:#f5faf3;font:700 12px var(--sans);cursor:pointer}
.rec:has(.record-stop:not([hidden])) .rec-hint{bottom:70px}
'''

def sha(p):
 with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()

def dump(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def payload(j):return json.dumps(j,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
def b64(d):return b64encode(d).decode('ascii')
def ex(s):return escape(s,quote=True)

def reference(src,n,key):
 p=src/n
 if p.exists():data=p.read_bytes()
 else:
  with urlopen(RAW+n,timeout=18) as r:data=r.read(4_000_001)
 assert len(data)<=4_000_000 and sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()==key,n
 if not p.exists():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 return data

def cut(s,a,b,r=''):
 start=s.index(a);end=s.index(b,start);return s[:start]+r+s[end:]

def inline_css(css,blobs):
 def fix(m):return 'url(data:font/ttf;base64,'+b64(blobs['t2/assets/'+m[1]])+')'
 return re.sub(r'''url\(['"]?([^)'" ]+\.ttf)['"]?\)''',fix,css)

def aux_pages(fiche,credits):
 def wrap(id,title,content):
  return (f'<div class="shell vv-aux" id="vv-{id}" hidden><header class="top"><strong><span class="mark" aria-hidden="true">V</span>Vitrine Vidéo</strong>'
          '<div class="top-links"><a class="back" href="#1">← Les 12 écrans</a></div></header>'
          f'<main class="vv-aux"><p class="kicker">T3 · SOIN DU VISAGE</p><h1>{title}</h1><section class="card">{content}</section></main></div>')
 return (wrap('accueil','Coiffure et beauté.', '<h2>T3 — Apporter une preuve</h2><p>Quatre prises pour montrer le travail, dont un geste et un détail visible.</p><div class="links"><a class="button" href="#1">Les 12 écrans</a><a href="#fiche">Ma fiche →</a></div>')
   +wrap('fiche','Ma fiche.',fiche+'<div class="links"><a class="button" href="#1">Revoir les 12 écrans</a></div>')
   +wrap('credits','Crédits et limites.',credits)
   +wrap('planche','Les 12 vues.', '<div class="vv-planche"><img id="vv-planche-img" width="1112" height="2456" alt="Planche des douze écrans T3, de la consigne de la prise 1 à la relecture de la prise 4"></div>')
   +'<div id="vv-solo" hidden><header class="vv-bar"><a id="vv-back" href="#1">← Les 12 écrans</a><span id="vv-solo-label">Écran en lecture seule</span></header><iframe id="vv-solo-frame" title="Écran de prise T3" allow="autoplay"></iframe></div>')

def page_fiche(p):
 # Source unique : le Markdown propriétaire. Pas de formulaire actif ni de coordonnées d’exemple.
 from markdown_it import MarkdownIt
 md=p.read_text(encoding='utf-8').split('\n',2)[2]
 return MarkdownIt('commonmark',{'html':False}).enable('table').render(md).replace('<th>', '<th scope="col">')

def main(a):
 o=a.sortie.resolve();assert not o.exists(),f'Dossier de sortie déjà présent : {o}'
 inputs=T3 if (T3/'preparation-12-ecrans/capture.json').is_file() else T3/'sources'
 old=inputs/'preparation-12-ecrans'
 q=inputs/'Fiche-questions-T3.md'
 m=a.film.resolve()
 assert sha(m)==MASTER_SHA,'Le master P2-r3 ne correspond pas.'
 with ThreadPoolExecutor(max_workers=6) as pool:
  data=dict(zip(BLOBS,pool.map(lambda kv:reference(a.reference,*kv),BLOBS.items())))
 def ref(n):return data[n].decode('utf-8')
 for d in ('capture/ecrans','formulaire','recherche/polices','media','rapports','outils/sources/preparation-12-ecrans'):(o/d).mkdir(parents=True,exist_ok=True)
 shutil.copyfile(m,o/'media'/MASTER)
 shutil.copyfile(q,o/'formulaire/Fiche-questions-T3.md');shutil.copyfile(q,o/'outils/sources/Fiche-questions-T3.md')
 for n in ('Ecriture-et-audio.md','capture.json'):shutil.copyfile(old/n,o/'outils/sources/preparation-12-ecrans'/n)
 shutil.copyfile(old/'Ecriture-et-audio.md',o/'recherche/Ecriture-et-audio.md')
 for n in ('fabriquer-r2.py','galerie-r2.js','prise-r2.js','recette-r2.py','sceller-r2.py','INTEGRATION.md'):
  if (HERE/n).is_file():shutil.copyfile(HERE/n,o/'outils'/n)
 shutil.copyfile(HERE/'INTEGRATION.md',o/'INTEGRATION.md')
 for n in BLOBS:
  if n.endswith('.txt'):(o/'recherche/polices'/Path(n).name).write_bytes(data[n])
 dump(o/'recherche/Composants-Signature.json',{'commit':REF,'racine':RAW,'empreintes_git_blob':BLOBS,'polices': 'SIL OFL 1.1, fichiers TTF d’origine incorporés octet pour octet','vues_verifiees':[GALLERY+'t1/ecrans.html?metier=coiffure',GALLERY+'t2/ecrans.html?metier=manucure']})
 guide=json.loads((old/'capture.json').read_text(encoding='utf-8'));assert guide['film']['sha256']==MASTER_SHA
 guide['revision']='revue-parcours-r2';guide['portee']='Consultation non validante et essai séparé, sans caméra ni micro. Durées de tournage proposées ; les chronos suivent les vrais extraits du film.';fps=guide['film']['fps']; assert fps==24
 for i,(p,label) in enumerate(zip(guide['scenes'],LABELS),1):
  assert p['id']==f'S{i}'
  p['intention']=p['role'];p['role']=label;p['titre']=label
  p['ecrans']=[{'numero':(i-1)*3+j,'id':f"{p['id']}_{v}", 'galerie':f'#{(i-1)*3+j}','seul':f'#seul-{(i-1)*3+j}'} for j,v in enumerate(STAGES,1)]
  begin,end=p['extrait_images'];assert 0<=begin<end<=720 and begin/fps<=p['miniature_s']<end/fps
  p['duree']=(end-begin)/fps;p['freeze']=p['miniature_s']-begin/fps
 dump(o/'capture/guide.json',guide)
 def run(*args):return subprocess.run([a.ffmpeg,'-v','error','-nostdin','-threads','2',*map(str,args)],check=True,timeout=70,capture_output=True).stdout
 def encode(dest,trim,crf,maxrate):
  run('-i',m,'-map','0:v:0','-an','-sn','-dn','-vf',trim+'scale=360:640:flags=lanczos','-c:v','libx264','-r','24','-fps_mode','cfr','-threads','2','-preset','fast','-crf',crf,'-maxrate',maxrate,'-bufsize','580k','-g','48','-pix_fmt','yuv420p','-colorspace','bt709','-color_trc','bt709','-color_primaries','bt709','-movflags','+faststart',dest)
 def probe(dest):
  v=json.loads(subprocess.run([a.ffprobe,'-v','error','-count_frames','-show_streams','-of','json',str(dest)],check=True,timeout=30,capture_output=True).stdout)['streams'];assert len(v)==1
  x=v[0];assert x['codec_name']=='h264' and x['codec_type']=='video' and x['width']==360 and x['height']==640 and x['r_frame_rate']=='24/1' and x['pix_fmt']=='yuv420p', x
  return {'images':int(x['nb_read_frames']),'duree_s':float(x['duration']),'sha256':sha(dest),'octets':dest.stat().st_size,'son':False}
 src_stats=[]
 with TemporaryDirectory(prefix='T3-r2-media-',dir=o.parent) as tmp:
  t=Path(tmp);movie=t/'film.mp4';encode(movie,'','27','330k');movie_check=probe(movie);assert movie_check['images']==720 and movie_check['duree_s']==30
  film={'b64':b64(movie.read_bytes())};scenes=[]
  for p in guide['scenes']:
   i,j=p['extrait_images'];v=t/(p['id']+'.mp4');encode(v,f'trim=start_frame={i}:end_frame={j},setpts=N/(24*TB),','24','510k'); stats=probe(v)
   assert stats['images']==j-i and abs(stats['duree_s']-p['duree'])<.001,(p['id'],stats)
   # Comparaison de l’image au milieu avec l’image correspondante du master (luma, 90×160).
   # Tous les débuts/fins sont appliqués au numéro d’image de l’original, pas à un seek approximatif.
   def frame(src,n):return run('-i',src,'-vf',f'select=eq(n\\,{n}),scale=90:160:flags=area,format=gray','-frames:v','1','-f','rawvideo','-threads','1','pipe:1')
   n=(j-i)//2; x,y=frame(m,i+n),frame(v,n); assert len(x)==len(y)==14400
   delta=sum(abs(b-c) for b,c in zip(x,y))/len(x);assert delta<4.5,(p['id'],delta)
   src_stats.append(dict(id=p['id'],bornes=[i,j],luma_ecart_moyen=round(delta,3),**stats));scenes.append(dict(p,b64=b64(v.read_bytes())))
  jpg=run('-ss',guide['scenes'][0]['miniature_s'],'-i',m,'-vf','scale=360:640:flags=lanczos','-frames:v','1','-an','-q:v','5','-f','mjpeg','pipe:1')
 dump(o/'rapports/Media-integre.json',{'master':MASTER,'sha256_master':MASTER_SHA,'derivees':{'dimensions':[360,640],'fps':24,'film':movie_check,'extraits':src_stats},'rush_stock_fournis':False})
 commun=ref('commun/atelier.css')
 outer=inline_css(ref('t2/assets/web.css'),data)+'\n'+commun+'\n'+OUT_CSS
 inner=inline_css(ref('t2/assets/simulation-t2.css'),data)+'\n'+commun+'\n'+IN_CSS
 s=ref('t2/simulation.html')
 s=re.sub(r'<link\b[^>]*>', '', s).replace('<title>T2 · Coiffure et beauté · Les prises</title>','<title>T3 · Soin du visage · La prise</title>')
 s=s.replace('</head>',f'<style>{inner}</style></head>').replace('<body>','<body class="capture relecture-preview">')
 s=cut(s,'  <div id="testCurtain"','  <span class="test-id"');s=cut(s,'      <p class="take-help"','    </div>\n  </section>', '      <button type="button" class="cta" id="cta" disabled>LIRE LA PRISE D’EXEMPLE</button>\n')
 s=s.replace('<button id="toggleTakeAudio" type="button" class="minor" hidden>Écouter</button>','').replace('<button id="mediaRetry" type="button" hidden>Réessayer</button>','')
 s=cut(s,'  <!-- Montage -->','</html>','</main>\n<script type="application/json" id="vv-prise-data">__PRISE_CONFIG__</script>\n<script>'+ (HERE/'prise-r2.js').read_text(encoding='utf-8')+'</script></body>\n')
 u=ref('t2/ecrans.html');u=re.sub(r'<link\b[^>]*>|<script\b[^>]*></script>','',u)
 u=u.replace('</head>',f'<meta name="robots" content="noindex"><style>{outer}</style></head>').replace('<div class="shell">','<div class="shell" id="vv-gallery">',1).replace('T2 · Coiffure et beauté</title>','T3 · Coiffure et beauté</title>').replace('id="version">T2','id="version">T3')
 u=cut(u,'<div class="reperes-t2"','<div class="links"><a class="button" id="downloadDemo"')
 u=u.replace('id="downloadDemo" download','id="downloadDemo" download="T3-Soin-du-visage-apercu-muet.mp4"').replace('Faire ma propre vidéo →','Revoir ma fiche →').replace('../CREDITS.html','#credits').replace('Crédits des images et des musiques','Crédits des images et limites de l’essai')
 u=u.replace('index.html','#fiche').replace('href="../"','href="#accueil"').replace('href="simulation.html"','href="#seul-1"')
 u=u.replace('</footer>', ' <a id="vv-planche-link" href="#planche" hidden>Planche des 12 écrans ↗</a></footer>')
 u=u.replace('id="film" aria-label','id="film" muted aria-label').replace('id="screenLive" title','id="screenLive" aria-hidden="true" title')
 credits='''<h2>Les images</h2><p>Montage muet du soin du visage : extraits tirés du film d’exemple, et non des rushs bruts. Ce soin et ces personnes ne représentent pas une offre réelle. Le carton « Réserver ce soin » n’est lié à aucun numéro ou site.</p>
<p>Images : Mixkit, sous <a href="https://mixkit.co/license/modal/videoFree/" rel="noopener noreferrer" target="_blank">Stock Video Free License</a>. Les quatre extraits et le film sont sans voix ni musique.</p>
<h2>Le parcours</h2><p>Présentation commune des gabarits Signature T1 et T2 ; polices Manrope, IBM Plex, Plus Jakarta Sans et Montserrat (SIL OFL 1.1). Aucun média T1/T2 n’est repris. Le chrono lit des vidéos déjà montées. Pas de caméra, de micro, de coordonnées ou d’envoi.</p>'''
 cfg={'scenes':scenes,'film':film,'poster':'data:image/jpeg;base64,'+b64(jpg),'prise':s}
 u=u.replace('</body>',aux_pages(page_fiche(q),credits)+'<script type="application/json" id="vv-planche-data">null</script><script type="application/json" id="vv-data">'+payload(cfg)+'</script><script>'+ (HERE/'galerie-r2.js').read_text(encoding='utf-8')+'</script></body>')
 (o/'index.html').write_text(u,encoding='utf-8')
 docs(o,guide)
 print(f'Galerie r2 préparée : {o}/index.html ({(o/"index.html").stat().st_size:,} o.)',flush=True)

def docs(o,g):
 (o/'README.md').write_text('''# T3 · Les 12 écrans · Soin du visage · r2

**Revue locale, en attente de l’accord du propriétaire.** Aucun envoi GitHub.

- [Ouvrir la galerie](index.html) · [Les 12 vues et leurs captures](capture/12-ecrans.md) · [Planche](capture/planche-12-ecrans.jpg)
- [Fiche de questions](formulaire/Fiche-questions-T3.md) · [Guide et IDs](capture/guide.json) · [Film d’exemple original](media/T3-Essai-P2-r3-muet.mp4)
- [Intégration et limites](INTEGRATION.md) · [Droits et sources](recherche/Droits-et-perimetre.md) · [Écriture et références audio](recherche/Ecriture-et-audio.md)
- [Contrôles navigateur](rapports/Recette-r2.json) · [Contrôles médias](rapports/Media-integre.json) · [Manifeste](manifest.json) · [Contrôle des empreintes](SHA256SUMS)
''',encoding='utf-8')
 stock=' · '.join(f'[{i}](https://mixkit.co/free-stock-video/{slug}/)' for i,slug in MIXKIT.items())
 (o/'recherche/Droits-et-perimetre.md').write_text(f'''# Sources et périmètre — T3 r2

- **Montage T3 uniquement.** Film muet P2-r3, trente secondes, inchangé (SHA-256 `{MASTER_SHA}`). La galerie embarque une copie de lecture du film et quatre tranches intégrées, réencodées du montage. Aucun rush de stock n’est fourni à part.
- **Images : Mixkit.** Vidéos incorporées : {stock}. [Stock Video Free License](https://mixkit.co/license/modal/videoFree/) et [conditions](https://mixkit.co/terms/). Crédit : Mixkit. Ne pas utiliser ce lot comme banque de stock ; vérifier les droits de tiers pour de nouveaux usages. Les personnes montrées ne témoignent pas pour un prestataire réel.
- **Inspiration seulement :** [Hand & Stone · It’s Glow Time](https://www.ispot.tv/ad/TakD/hand-and-stone-brightening-facial-enhancement-its-glow-time). Pas de copie image ou son.
- **Interface commune :** [sources Signature au commit de référence](https://github.com/{REPO}/tree/{REF}/{ROOT}). Manrope, IBM Plex Mono, Plus Jakarta Sans et Montserrat sont incorporées sans modification ; avis complets [OFL Manrope](polices/OFL.txt), [OFL IBM Plex](polices/OFL-Plex.txt), [OFL Jakarta](polices/OFL-PlusJakartaSans.txt), [OFL Montserrat](polices/OFL-Montserrat.txt). Aucun moteur ni média de T1, T2 ou R04 : seuls les composants d’interface sont la référence.
- **Son :** aucun mix privé, voix ou piste de production dans ce lot. [Écriture et références d’écoute](Ecriture-et-audio.md). Clarifier la mention commercial/TV de raspberrymusic avant toute diffusion de la variante concernée.
- **Démo :** ni coordonnées, ni offre réelle, ni résultat clinique. Le carton « Réserver ce soin » n’a pas de destination. Aucun accès caméra ou micro, aucune collecte ou transmission. Pas de compatibilité iOS/Android physique revendiquée.
''',encoding='utf-8')
 lines=['# Les 12 écrans T3 — revue r2','','[Galerie](../index.html) · [Planche](planche-12-ecrans.jpg) · [Fiche](../formulaire/Fiche-questions-T3.md)','','Les liens ouvrent les vues en lecture seule. Dans l’essai séparé, une fin de chrono présente une relecture sans rien valider : on peut refaire la même prise ou la garder explicitement. Le film d’exemple a son propre accès de consultation.','','| Nº | ID | Contenu | Accès |','|:--:|---|---|---|']
 for p in g['scenes']:
  for j,s in enumerate(p['ecrans']):
   n=s['numero'];cop=(p['consignes'][0],f"Chrono simulé : {p['duree']:.3f} s. Fin → relecture dans l’essai.",p['question'])[j]
   lines.append(f"| {n:02d} | `{s['id']}` | {cop} | [Galerie](../index.html#{n}) · [Seul](../index.html#seul-{n}) · [Capture](ecrans/{n:02d}.jpg) |")
 lines.extend(['','| Prise | Bornes dans le master (fin exclue ; 24 i/s) | Durée de l’extrait | Durée proposée pour filmer |','|---|---|---:|---:|'])
 for p in g['scenes']:
  i,j=p['extrait_images'];lines.append(f"| {p['id']} · {p['titre']} | [{i}, {j}[ | {p['duree']:.3f} s | {p['duree_filmer_s']} s |")
 (o/'capture/12-ecrans.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':
 cli=ArgumentParser(description=__doc__)
 cli.add_argument('--film',type=Path,default=T3/'recherche/essais/T3-Soin-du-visage-Essai.mp4')
 cli.add_argument('--reference',type=Path,default=Path.home()/'.cache/vv-t3-envoi/comparaison-r2/reference')
 cli.add_argument('--sortie',type=Path,required=True);cli.add_argument('--ffmpeg',default='ffmpeg');cli.add_argument('--ffprobe',default='ffprobe')
 main(cli.parse_args())
