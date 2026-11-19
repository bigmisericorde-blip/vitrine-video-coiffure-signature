"""Traitement audio de l'atelier : calage non destructif et ducking piloté par la voix."""
from __future__ import annotations

import math
from pathlib import Path
import subprocess
import wave

import numpy as np

from core import ffmpeg

SR = 48000
STEP = SR//100
VOICE_FILTER = ('highpass=f=75,acompressor=threshold=0.125:ratio=2:attack=8:release=95:knee=2.5,'
                'equalizer=f=2300:t=q:w=0.9:g=1.0')
REDUCTION = 13.0


class MediaError(ValueError):
    """Erreur que l'on peut montrer sans exposer les chemins ni le texte du client."""


def command(*args, timeout=35, check=True):
    try:
        r = subprocess.run([ffmpeg(),'-hide_banner','-nostdin','-filter_threads','1',*map(str,args)],
                           capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise MediaError('Le traitement est trop lent. Essaie un fichier plus léger.') from e
    if check and r.returncode:
        raise MediaError('Impossible de lire ou d’encoder ce média. Essaie un autre fichier.')
    return r


def demux(path, video=False):
    with Path(path).open('rb') as f: h=f.read(32)
    if h[4:8] in (b'ftyp',b'moov',b'wide',b'free',b'mdat'): return 'mov'
    if h.startswith(b'\x1aE\xdf\xa3'): return 'matroska'
    if not video:
        if h[:4] in (b'RIFF',b'RF64') and h[8:12]==b'WAVE': return 'wav'
        if h.startswith(b'OggS'): return 'ogg'
        if h.startswith(b'fLaC'): return 'flac'
        if h.startswith(b'ID3') or (len(h)>2 and h[0]==0xff and h[1]&0xe0==0xe0 and h[1]&6): return 'mp3'
        if len(h)>2 and h[0]==0xff and h[1]&0xf6==0xf0: return 'aac'
    raise MediaError('Choisis une vidéo MP4, MOV ou WebM.' if video else
                     'Choisis une voix WAV, MP3, M4A, AAC, OGG, FLAC ou WebM.')


def input_args(path, kind):
    return ['-protocol_whitelist','file,pipe','-threads','2','-f',kind,'-i',path]


def decode(path, kind, *, channels, limit, filters='anull'):
    r=command('-v','error','-xerror',*input_args(path,kind),'-map','0:a:0',
              '-af',filters,'-t',f'{limit:.6f}','-ac',channels,'-ar',SR,'-f','f32le','pipe:1',check=False)
    if r.returncode or not r.stdout:
        raise MediaError('Aucune piste audio lisible. Enregistre ta voix séparément ou choisis Sans voix.')
    a=np.frombuffer(r.stdout,dtype='<f4').reshape(-1,channels).copy()
    if not np.all(np.isfinite(a)): raise MediaError('Ce fichier contient un signal audio illisible.')
    return a


def frame_rms(x):
    x=np.pad(x,(0,-len(x)%STEP))
    return np.sqrt(np.mean(x.reshape(-1,STEP)**2,axis=1))


def activity(x):
    """Fenêtres sonores indépendantes de la langue ; aucun mot ni pitch n'est modifié."""
    rms=frame_rms(x)
    if not len(rms): return []
    strong=float(np.quantile(rms,.93)); noise=float(np.quantile(rms,.24))
    if strong<.003 and float(rms.max())<.008: return []
    gate=max(.00105,strong*.055,min(2.65*noise,strong*.18))
    on=np.flatnonzero(rms>=gate)
    if not len(on): return []
    groups=np.split(on,np.flatnonzero(np.diff(on)>19)+1)
    return [(max(0,int(g[0]-5)*STEP),min(len(x),int(g[-1]+8)*STEP))
            for g in groups if len(g)>=5 and g[-1]-g[0]+1>=7]


def taper(x, duration=.008):
    q=min(round(duration*SR),len(x)//2)
    if q:
        x[:q]*=np.linspace(0,1,q,dtype=np.float32)
        x[-q:]*=np.linspace(1,0,q,dtype=np.float32)


def entrance(bed, room):
    # Cherche une respiration après une attaque du fond, sans modifier la voix.
    hi=min(room,1.3)
    if hi<=.20: return max(0,round(hi*SR*.8))
    mono=bed[:round((hi+.2)*SR)].mean(axis=1)
    rms=frame_rms(mono)
    delta=np.maximum(0,np.diff(rms,prepend=0)); ref=max(.00001,float(np.quantile(delta,.9)))
    candidates=range(max(0,round(min(.34,hi)*100)),round(hi*100)+1,2)
    def score(k):
        attack=min(2.,float(np.max(delta[max(0,k-19):max(1,k-7)]))/ref)
        mask=min(2.,float(np.max(delta[k-4:k+5]))/ref)
        now=float(np.mean(rms[k:k+9]))
        return .26*attack-.21*mask-1.75*now-.34*abs(k/100-.78)
    return min(round(hi*SR),max(candidates,key=score)*STEP)


def envelope(n, windows, db=REDUCTION):
    out=np.ones(n,dtype=np.float32); level=10**(-db/20)
    attack=round(.125*SR); release=round(.285*SR)
    def easing(q):
        u=np.linspace(0,1,q,dtype=np.float32);return u*u*(3-2*u)
    for start,end in windows:
        a,b=max(0,start-attack),min(n,end+release)
        out[a:start]=np.minimum(out[a:start],1-(1-level)*easing(start-a))
        out[start:end]=np.minimum(out[start:end],level)
        out[end:b]=np.minimum(out[end:b],level+(1-level)*easing(b-end))
    return out


def wav(path, data):
    with wave.open(str(path),'wb') as f:
        f.setnchannels(data.shape[1]);f.setsampwidth(2);f.setframerate(SR)
        f.writeframes(np.round(np.clip(data,-1,1)*32767).astype('<i2').tobytes())


def mix_to_wav(bed, voice, duration, out, *, voice_kind=None, fixed=False):
    """bed : AAC intégré ou WAV de travail. fixed garde la synchro des prises parlées."""
    n=round(duration*SR)
    music=np.zeros((n,2),dtype=np.float32)
    if bed:
        m=decode(bed,demux(bed),channels=2,limit=duration)
        if len(m)<n-round(.028*SR): raise MediaError('Le fond n’est pas assez long pour ce montage.')
        music[:min(len(m),n)]=m[:n]
        q=min(n//3,round(.51*SR));music[-q:]*=np.linspace(1,0,q,dtype=np.float32)[:,None]
    meta={'presente':False,'debit_modifie':False,'ducking_db':0,'fenetres_voix_s':[]}
    if voice:
        scan_limit=duration+.045 if fixed else max(44,duration+12)
        raw=decode(voice,voice_kind or demux(voice),channels=1,limit=scan_limit,
                   filters=('aresample=48000:async=1:first_pts=0,' if fixed else '')+VOICE_FILTER)[:,0]
        if not fixed and len(raw)>=round((scan_limit-.025)*SR):
            raise MediaError('Cet enregistrement est trop long. Importe ou enregistre un extrait : le moteur ne coupe pas et n’accélère pas la voix.')
        wins=activity(raw)
        if not wins: raise MediaError('Aucune voix audible. Vérifie ton micro ou importe une nouvelle prise.')
        if fixed:
            # Seule la piste sonore alignée à l'image est utilisée ; pas de décalage.
            take=raw[:n].copy(); placed=0
        else:
            a,b=wins[0][0],wins[-1][1];take=raw[a:b].copy()
            usable=n-round(.20*SR)
            if len(take)>usable:
                msg=f'Ta narration dure {len(take)/SR:.1f} s. Pour cette vidéo, vise {usable/SR:.1f} s maximum : le moteur ne coupe pas et n’accélère pas la voix.'
                raise MediaError(msg)
            placed=entrance(music,(usable-len(take))/SR) if bed else min(round(.44*SR),usable-len(take))
        taper(take)
        active=activity(take)
        if not active: raise MediaError('Aucune voix audible dans la durée de ce montage.')
        levels=frame_rms(take)
        use=np.concatenate([levels[a//STEP:max(a//STEP+1,b//STEP)] for a,b in active]); typical=float(np.quantile(use,.75))
        crest=float(np.max(np.abs(take)))
        gain=min(8.,10**(-20.5/20)/max(typical,1e-6),10**(-3.0/20)/max(crest,1e-6))
        intervals=[(a+placed,b+placed) for a,b in active]
        if bed: music*=envelope(n,intervals)[:,None]
        music[placed:placed+len(take)]+=take[:,None]*np.float32(gain)
        meta={'presente':True,'debit_modifie':False,'position_s':round(placed/SR,3),
              'ducking_db':REDUCTION if bed else 0,
              'fenetres_voix_s':[[round(a/SR,3),round(b/SR,3)] for a,b in intervals]}
    peak=max(1e-9,float(np.max(np.abs(music))))
    if peak>.88: music*=np.float32(.88/peak)
    wav(out,music)
    return meta
