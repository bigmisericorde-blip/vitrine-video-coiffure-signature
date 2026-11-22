#!/usr/bin/env python3
"""Prototype local de sortie sonore T4 : quatre extraits choisis, master fourni, pas de réseau.
Ne constitue ni le moteur visuel ni le gabarit final. Rotation locale, modes muet/musique/voix.
"""
from __future__ import annotations
import argparse,hashlib,json,math,os,secrets,sqlite3,subprocess,tempfile
from pathlib import Path
from mix_voix import mix_to_wav
HERE=Path(__file__).resolve().parent
PROOF=HERE.parent/'preparation-envoi/Controle-audio-candidat-T4.json'
CAT=HERE/'audio/catalogue.json'
DEMO=HERE.parent/'essais/parfum-r2/T4-Essai-Parfum-R2-Muet.mp4'
DEMO_SHA256='518bf2de161d85c6273ea1a9f4242e3c8454f3146e2c1497217856e67ca0c041'

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(*args,timeout=120):
 return subprocess.run([str(x) for x in args],check=True,capture_output=True,timeout=timeout)
def probe(p):return json.loads(run('ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',p).stdout)
def video_hash(p):return run('ffmpeg','-v','error','-nostdin','-i',p,'-map','0:v:0','-c','copy','-f','hash','-hash','sha256','-').stdout.decode().strip()
def loudness(p):
 import re
 z=run('ffmpeg','-hide_banner','-nostdin','-i',p,'-map','0:a:0','-af','loudnorm=I=-20:TP=-2:LRA=11:print_format=json','-f','null','-').stderr.decode();x=json.loads(re.search(r'\{\s*"input_i".*?\}',z,re.S)[0]);return float(x['input_i']),float(x['input_tp'])
def catalogue():
 c=json.loads(CAT.read_text()); assert c['sources_sha256']==sha(PROOF),'Preuve source modifiée';p=json.loads(PROOF.read_text());r={x['place_proposee']:x for x in p['pistes']};assert set(c['pistes'])==set(r)==set('ABCD')
 for i,t in c['pistes'].items():
  x=r[i];bed=HERE/'audio'/t['fichier'];assert bed.parent.resolve()==(HERE/'audio').resolve() and bed.is_file() and not bed.is_symlink()
  assert t['sha256']==x['extrait_revue']['sha256']==sha(bed);assert (t['titre'],t['auteur'],t['source'],t['licence'])==(x['titre'],x['auteur'],x['fiche_source'],x['licence_url'])
  assert t['credit']==x['notice_attribution'].replace(' ; démonstration privée Parfum R2.',' ; synchronisation au film, avec adaptation du niveau en présence de voix.')
 return c

def image_ok(master):
 assert master.is_file() and master.resolve()!=DEMO.resolve() and sha(master)!=DEMO_SHA256,'Le master Parfum R2 est une référence gelée, pas un master de production.'
 q=probe(master);v=[x for x in q['streams'] if x['codec_type']=='video'];a=[x for x in q['streams'] if x['codec_type']=='audio'];assert len(v)==1 and not a,'Image muette exigée'
 v=v[0];assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],int(v['nb_read_frames']))==('h264',720,1280,'30/1',900);assert abs(float(q['format']['duration'])-30)<.04
 return video_hash(master)

def rendre(master,out,db,mode='musique',voix=None,piste=None,audition=False):
 assert mode in ('muet','musique') and (piste is None or piste in 'ABCD')
 assert not (mode=='muet' and (voix is not None or piste is not None or audition))
 assert not audition or piste is not None
 assert not (piste and not audition),'La piste imposée est réservée à une audition, sans consommer la rotation.'
 master=Path(master);out=Path(out);db=Path(db);assert out.suffix.lower()=='.mp4' and not out.exists() and not out.with_suffix('.json').exists(),'Sortie neuve requise'
 assert out.resolve()!=master.resolve();sig=image_ok(master);master_hash=sha(master);voice_hash=sha(Path(voix)) if voix is not None else None;cat=catalogue() if mode=='musique' else None;catalogue_hash=sha(CAT) if cat else None
 out.parent.mkdir(parents=True,exist_ok=True);db.parent.mkdir(parents=True,exist_ok=True);con=None;created=[]
 try:
  if mode=='musique' and not audition:
   con=sqlite3.connect(db,timeout=45);con.execute('CREATE TABLE IF NOT EXISTS rotation (id INTEGER PRIMARY KEY CHECK(id=1), catalogue TEXT, dernier TEXT, jouees TEXT)');con.execute('BEGIN IMMEDIATE')
   state=con.execute('SELECT catalogue,dernier,jouees FROM rotation WHERE id=1').fetchone();cid=sha(CAT);assert not state or state[0]==cid,'Catalogue modifié : nouvelle session requise.'
   last=state[1] if state else None;played=set(json.loads(state[2])) if state else set();allowed=[i for i in 'ABCD' if i!=last];pool=[i for i in allowed if i not in played]
   if not pool:played=set();pool=allowed
   piste=secrets.choice(pool)
  with tempfile.TemporaryDirectory(prefix='.t4-audio-',dir=out.parent) as td:
   td=Path(td);part=td/'export.mp4';result={'schema':1,'statut':'prototype local non validé, non publié','mode':mode,'master_sha256':sha(master),'piste':piste,'audition':audition,'voix':None}
   if mode=='muet':
    run('ffmpeg','-v','error','-nostdin','-y','-i',master,'-map','0:v:0','-an','-map_metadata','-1','-c:v','copy','-movflags','+faststart',part)
   else:
    t=cat['pistes'][piste];bed=HERE/'audio'/t['fichier'];wav=td/'mix.wav';vm=mix_to_wav(bed,Path(voix) if voix else None,30,wav);result['voix']=vm
    run('ffmpeg','-v','error','-nostdin','-y','-i',master,'-i',wav,'-map','0:v:0','-map','1:a:0','-map_metadata','-1','-c:v','copy','-af','loudnorm=I=-20:TP=-2:LRA=11','-c:a','aac','-profile:a','aac_low','-b:a','160k','-ar','48000','-ac','2','-t','30','-metadata','comment='+t['credit'],'-metadata','artist='+t['auteur'],'-movflags','+faststart',part)
    z=probe(part);aa=[s for s in z['streams'] if s['codec_type']=='audio'];assert len(aa)==1 and (aa[0]['codec_name'],aa[0]['profile'],aa[0]['sample_rate'],aa[0]['channels'])==('aac','LC','48000',2);assert z['format']['tags']['comment']==t['credit'];lu,tp=loudness(part);assert math.isfinite(lu) and math.isfinite(tp) and -25<=lu<=-15 and tp<=-1
    result.update({'credit':t['credit'],'source':t['source'],'licence':t['licence'],'audio_extrait_sha256':t['sha256'],'lufs_i':lu,'dbtp':tp})
   assert video_hash(part)==sig,'Flux vidéo modifié';assert abs(float(probe(part)['format']['duration'])-30)<.04
   assert sha(master)==master_hash and (voix is None or sha(Path(voix))==voice_hash),'Une entrée a changé pendant le rendu'
   if cat: assert sha(CAT)==catalogue_hash and sha(bed)==t['sha256'],'Catalogue ou musique modifiés pendant le rendu'
   run('ffmpeg','-v','error','-xerror','-nostdin','-i',part,'-f','null','-');result['mp4_sha256']=sha(part);result['video_flux_sha256']=sig
   report=td/'recu.json';report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');os.link(part,out);created.append(out);os.link(report,out.with_suffix('.json'));created.append(out.with_suffix('.json'))
   if con:
    played.add(piste);con.execute('INSERT INTO rotation VALUES (1,?,?,?) ON CONFLICT(id) DO UPDATE SET catalogue=excluded.catalogue,dernier=excluded.dernier,jouees=excluded.jouees',(sha(CAT),piste,json.dumps(sorted(played))));con.commit()
   return result
 except BaseException:
  if con:con.rollback()
  for f in created:f.unlink(missing_ok=True)
  raise
 finally:
  if con:con.close()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--master',type=Path,required=True);p.add_argument('--sortie',type=Path,required=True);p.add_argument('--rotation',type=Path,required=True);p.add_argument('--mode',choices=['muet','musique'],default='musique');p.add_argument('--voix',type=Path);p.add_argument('--piste',choices=list('ABCD'));p.add_argument('--audition',action='store_true');a=p.parse_args();print(json.dumps(rendre(a.master,a.sortie,a.rotation,a.mode,a.voix,a.piste,a.audition),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
