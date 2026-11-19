#!/usr/bin/env python3
"""Finalise un spot de 30 s max avec la voix du client et un fond en rotation."""
from __future__ import annotations

import argparse
from functools import lru_cache
import json
from pathlib import Path
import re
import tempfile

from core import CASE, HERE, PLAN, ROOT, load, sha
from mixage import attribution, gain, image_hash, LICENCES, measure, source_officielle
from mix_voix import MediaError, command, demux, input_args, mix_to_wav
from rotation import next_track
from voix_texte import tts

DURATION = 30.0


@lru_cache(maxsize=20)
def verified(path,size,mtime,digest):
    return sha(path)==digest


def verify(path, digest):
    if not path.is_file(): raise MediaError('Un média du gabarit n’est pas disponible. Réessaie plus tard.')
    st=path.stat()
    if not verified(str(path),st.st_size,st.st_mtime_ns,digest):
        raise MediaError('Un média du gabarit n’a pas passé le contrôle d’intégrité.')
    return path


def catalogue():
    cfg=load(HERE/'afrobeat.json'); stats=load(HERE/'recette-sonore.json')
    if cfg.get('profile_id')!=load(PLAN)['audio_profile']:
        raise MediaError('Le profil sonore ne correspond pas au gabarit T2.')
    tracks=cfg['pistes']; ids=[t['id'] for t in tracks]
    if (stats['resultat']!='PASS' or len(set(ids))!=4 or
        ids!=[t['id'] for t in cfg['selection_finale']] or
        ids!=[t['id'] for t in stats['pistes']] or
        any(t.get('voix') is not False for t in stats['pistes'])):
        raise MediaError('Le catalogue musical de l’atelier est incomplet.')
    out=[]
    for t,r in zip(tracks,stats['pistes'],strict=True):
        if not source_officielle(t,cfg['candidats']): raise MediaError('Une licence du catalogue est invalide.')
        out.append({**t,'media':ROOT/'media/afrobeat'/(t['id']+'.mp4'),'media_sha256':r['video_sha256']})
    case=load(CASE)
    return out, ROOT/'media'/case['sortie']['file'], stats['master_sha256']


def normalize_video(src,dest):
    k=demux(src,True)
    probe=command(*input_args(src,k),check=False,timeout=8).stderr.decode(errors='replace')
    duration=re.search(r'Duration: (\d+):(\d+):(\d+(?:\.\d+)?)',probe)
    if not duration or ' Video:' not in probe: raise MediaError('Ce fichier ne contient pas de vidéo lisible.')
    h,m,s=map(float,duration.groups()); length=h*3600+m*60+s
    if not 3<=length<=30.10: raise MediaError('Importe une vidéo déjà montée de 3 à 30 secondes.')
    cmd=command('-v','error','-xerror','-y','-progress','pipe:1',*input_args(src,k),
        '-map','0:v:0','-map_metadata','-1','-an','-sn','-dn','-t','30',
        '-vf','fps=30,scale=720:1280:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1',
        '-c:v','libx264','-pix_fmt','yuv420p','-threads','2','-preset','veryfast','-crf','19','-movflags','+faststart',dest,timeout=32)
    frames=re.findall(rb'^frame=(\d+)',cmd.stdout,re.M)
    if not frames or not 90<=int(frames[-1])<=900:
        raise MediaError('La piste image doit durer de 3 à 30 secondes.')
    return int(frames[-1])/30


def preserve_t2_image(src,dest):
    """Contrôle le rendu Web T2 avant de copier son AVC sans le réencoder."""
    kind=demux(src,True)
    if kind!='mov': raise MediaError('Le montage lié doit être un MP4 T2.')
    args=input_args(src,kind)
    info=command('-hide_banner',*args,check=False,timeout=8).stderr.decode(errors='replace')
    if not re.search(r'Video: h264[^\n]*\b720x1280\b[^\n]*\b30 fps\b',info):
        raise MediaError('L’image du montage lié doit être en H.264 vertical à 30 i/s.')
    command('-v','error','-xerror','-y',*args,'-map','0:v:0','-map_metadata','-1','-an','-sn','-dn',
            '-c:v','copy','-movflags','+faststart',dest,timeout=8)
    scan=command('-v','error','-xerror','-progress','pipe:1','-i',dest,'-map','0:v:0','-f','null','-',timeout=20).stdout
    frames=re.findall(rb'^frame=(\d+)',scan,re.M); times=re.findall(rb'^out_time_us=(\d+)',scan,re.M)
    if not frames or int(frames[-1])!=900 or not times or abs(int(times[-1])-30_000_000)>17_000:
        raise MediaError('Le montage lié doit avoir 900 images et durer 30 s.')
    return DURATION


def finalize(output, *, video=None, mode='sans', voice=None, text='', lang='', music=True,
             atelier='cli-montage', previous=None, state=None, linked_t2=False, fixed_track=None):
    if mode not in {'sans','audio','texte','video'}: raise MediaError('Choisis un mode de narration valide.')
    if mode=='audio' and voice is None: raise MediaError('Enregistre ou importe une piste voix.')
    if mode=='video' and video is None: raise MediaError('Pour garder la voix de la vidéo, importe un montage parlé.')
    tracks, master, master_sha=catalogue()
    if linked_t2 and (video is None or mode=='video'):
        raise MediaError('Ajoute une narration séparée au montage T2 lié.')
    pinned=next((t for t in tracks if t['id']==fixed_track),None)
    if (fixed_track and not linked_t2) or (linked_t2 and music and not pinned):
        raise MediaError('Le fond du montage lié est inconnu.')
    output=Path(output)
    if output.suffix.lower()!='.mp4' or output.resolve() in {master.resolve(),*(t['media'].resolve() for t in tracks)}:
        raise MediaError('Choisis un nouveau fichier de sortie MP4.')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.son-',dir=output.parent) as folder:
        temp=Path(folder)
        image=verify(master,master_sha);duration=DURATION
        if video:
            image=temp/'image.mp4'
            duration=preserve_t2_image(video,image) if linked_t2 else normalize_video(video,image)
        synth=None
        if mode=='texte':
            voice=temp/'voix.wav';synth=tts(text,lang,voice)
        elif mode=='video': voice=video
        elif mode=='sans': voice=None

        def assemble(track):
            bed=verify(track['media'],track['media_sha256']) if track else None
            mixed=temp/'son.wav';result=temp/'montage.mp4'
            audio=mix_to_wav(bed,voice,duration,mixed,fixed=mode=='video')
            metadata=[];mixstats=None
            if bed or voice:
                comments=[]
                if track: comments.append(attribution(track)+' Extrait adapté au montage et atténué sous la voix si présente.')
                if synth: comments.append(synth['credit']+' '+synth['source'])
                if comments: metadata=['-metadata','comment='+' | '.join(comments)]
                line=gain(mixed,'anull',-16.7 if voice else -20.0,-1.55)
                command('-v','error','-y','-i',image,'-i',mixed,'-map','0:v:0','-map','1:a:0',
                        '-map_metadata','-1','-c:v','copy','-af',line,'-c:a','aac','-b:a','160k','-ar','48000',
                        '-t',f'{duration:.6f}',*metadata,'-movflags','+faststart',result)
                lu,pk=measure(result)
                if pk>-.98: raise MediaError('Le contrôle de crête n’a pas passé. Essaie une autre prise voix.')
                mixstats={'lufs_i':lu,'dbtp':pk}
            else:
                command('-v','error','-y','-i',image,'-map','0:v:0','-an','-map_metadata','-1','-c:v','copy',
                        '-movflags','+faststart',result)
            if image_hash(image)!=image_hash(result): raise MediaError('Le contrôle de l’image n’a pas passé.')
            digest=sha(result)
            result.replace(output)
            credits=({k:track[k] for k in ('id','titre','auteur','source','licence','plateforme')}
                     | {'licence_nom':LICENCES[track['plateforme']][1]}) if track else None
            return {'piste':credits,'voix':audio|{'type':mode,'synthese':synth},'duree_s':round(duration,3),
                    'image':'t2' if linked_t2 else 'personnelle' if video else 'demo','sha256':digest,'son':mixstats}

        if not music: return assemble(None)
        if pinned: return assemble(pinned)  # nouvelle version sonore du même montage, pas un nouveau tirage
        with next_track(tracks,atelier,state,previous) as track:
            return assemble(track)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--video',type=Path)
    voice=p.add_mutually_exclusive_group()
    voice.add_argument('--audio',type=Path);voice.add_argument('--texte',type=Path,help='Texte UTF-8 du client')
    voice.add_argument('--garder-son-video',action='store_true')
    p.add_argument('--langue',choices=['fr','en']);p.add_argument('--sans-musique',action='store_true')
    p.add_argument('--etat-rotation',type=Path);p.add_argument('--atelier',default='cli-montage')
    a=p.parse_args(); mode='texte' if a.texte else 'audio' if a.audio else 'video' if a.garder_son_video else 'sans'
    try:
        r=finalize(a.output,video=a.video,mode=mode,voice=a.audio,text=a.texte.read_text(encoding='utf-8') if a.texte else '',
                   lang=a.langue,music=not a.sans_musique,atelier=a.atelier,state=a.etat_rotation)
    except (MediaError,OSError) as e: p.exit(2,f'Erreur : {e}\n')
    print(json.dumps(r,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
