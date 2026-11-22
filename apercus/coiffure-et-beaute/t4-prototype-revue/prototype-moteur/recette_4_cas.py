#!/usr/bin/env python3
"""Quatre rendus T4 fictifs sur mires ; tests techniques, pas une production réelle."""
from pathlib import Path
import json,subprocess,tempfile
from image_t4 import render
from son_t4 import rendre,sha
D=Path(__file__).resolve().parent;O=D/'tests-sur-mires';O.mkdir(exist_ok=True)
cases=[{'id':'EX01-produit','accroche':'Un parfum pour tous les jours ?','offre':'Eau de parfum','detail_visible':'L’essai sur papier','invitation':'Demandez un essai.'}, {'id':'EX02-service','accroche':'Une fête en vue ?','offre':'Maquillage de fête','detail_visible':'Le fini satiné de près','invitation':'Prenez rendez-vous.'}, {'id':'EX03-produit','accroche':'Envie de brillance ?','offre':'Gloss transparent','detail_visible':'Le reflet à la lumière','invitation':'Passez commande.'}, {'id':'EX04-service','accroche':'Vous aimez les ongles courts ?','offre':'Manucure sur ongles courts','detail_visible':'Le bord arrondi','invitation':'Demandez conseil.'}]
rows=[]
with tempfile.TemporaryDirectory(prefix='t4-mires-') as tmp:
 tmp=Path(tmp);takes=[]
 for i,(duration,color) in enumerate(zip([6,13,8,7],['#534048','#75525f','#997985','#3c2732']),1):
  p=tmp/f'S{i}.mp4';label=f'MIRE SYNTHETIQUE S{i}'
  cmd=['ffmpeg','-v','error','-nostdin','-f','lavfi','-i',f'color=c={color}:s=360x640:r=30:d={duration}','-vf',f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='{label}':fontcolor=white:fontsize=20:x=(w-text_w)/2:y=h/2",'-c:v','libx264','-preset','veryfast','-threads','2','-pix_fmt','yuv420p','-y',str(p)];subprocess.run(cmd,check=True);takes.append(p)
 voice=tmp/'signal.wav';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=3','-ar','48000','-y',str(voice)],check=True)
 for i,c in enumerate(cases):
  print('Cas',c['id'],flush=True);base=O/(c['id']+'-mires-muet.mp4');audio=O/(c['id']+'-mires-audio.mp4');assert not base.exists() and not audio.exists();info=render({k:v for k,v in c.items() if k!='id'},takes,base);sound=rendre(base,audio,tmp/'rotation.sqlite',voix=voice if i==1 else None,piste='ABCD'[i],audition=True)
  snap=O/(c['id']+'-image.jpg');subprocess.run(['ffmpeg','-v','error','-nostdin','-ss','7','-i',str(base),'-frames:v','1','-q:v','4','-y',str(snap)],check=True)
  rows.append({'id':c['id'],'fiche_fictive':info['fiche'],'image':base.name,'image_sha256':sha(base),'avec_musique':audio.name,'audio_sha256':sha(audio),'piste':sound['piste'],'voix_synthetique_non_parlee':i==1,'image_et_audio_meme_flux':sound['video_flux_sha256']==__import__('son_t4').video_hash(base),'prise_synthetique':True,'capture':snap.name})
 assert len({r['image_sha256'] for r in rows})==4
report={'statut':'PASS technique','revision':'prototype visuel et audio local seulement','cas':rows,'limites':'Images de mires générées, sans produit ni service réel. Textes, durées et effets provisoires non validés. Ce n’est pas une publicité ; ces quatre cas testent le moteur séparément de l’interface. La capture simulée 12 écrans est testée à part, pas une vraie capture ; aucune narration humaine, comparaison visuelle à R2 et validation restent à faire.','production':False,'publication':False};(D/'Recette-quatre-cas-prototype.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('PASS quatre fiches et quatre fonds sur mires',flush=True)
