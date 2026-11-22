"""Compose réellement S1–S4 et la fiche. Aucun MP4 de revue n’est une entrée."""
from pathlib import Path
from tempfile import TemporaryDirectory
import math
import subprocess as sp
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .commun import Erreur, exige, sha, lire, loi, TAKES, W, H, FPS, N, MAX_TAKE

cv2.setNumThreads(1)
TITRE, FENETRE, S2, FRISE, PULSE, PREUVE, S4, RAPPEL, DIP, CTA = (34,106,136,260,332,343,430,526,617,735)
IVORY='#f6f0df'; PINE='#1e382f'; SAGE='#d7e6ca'; MOSS='#456053'; GOLD='#c7a471'
FONT_NAMES=('DejaVuSans.ttf','DejaVuSerif.ttf')


def format_entree(path, s):
    exige(path.is_file() and not path.is_symlink() and 0<path.stat().st_size<=MAX_TAKE,'PRISE',f'{s} : fichier absent ou supérieur à 48 Mio.',s)
    with path.open('rb') as f: b=f.read(16)
    if b.startswith(b'\x1a\x45\xdf\xa3'): return 'matroska'
    if b[4:8] in (b'ftyp',b'moov',b'wide',b'free',b'mdat'): return 'mov'
    raise Erreur('PRISE',f'{s} : utilise une vidéo MP4, MOV ou WebM.',s)


def normaliser(o, src, dest, s, secondes):
    fmt=format_entree(src,s)
    try: d=o.sonde(src,fmt=fmt)
    except Erreur as e: raise Erreur('PRISE', f'{s} : le fichier ne peut pas être lu.', s) from e
    vs=[i for i in d['streams'] if i['codec_type']=='video' and not i.get('disposition',{}).get('attached_pic')]
    exige(len(vs)==1,'PRISE',f'{s} : une seule vidéo est attendue.',s); v=vs[0]
    w,h=v.get('width',0),v.get('height',0)
    exige(min(w,h)>=320 and max(w,h)<=4096 and w*h<=4096*2160,'PRISE',f'{s} : définition non prise en charge.',s)
    exige(v['codec_name'] in ('h264','hevc','vp8','vp9','av1') and v.get('color_transfer') not in ('smpte2084','arib-std-b67')
           and v.get('color_primaries')!='bt2020','PRISE',f'{s} : format non pris en charge ou HDR. Exporte en SDR.',s)
    dur=v.get('duration') or d['format'].get('duration')
    if dur and dur!='N/A':
        exige(secondes-.001<=float(dur)<=90,'PRISE',f'{s} : filme au moins {secondes} s (90 s max).',s)
    afd='setpts=PTS-STARTPTS,fps=30:start_time=0,scale=720:1280:force_original_aspect_ratio=increase:force_divisible_by=2:flags=bicubic,crop=720:1280,setsar=1'
    try:
        o.ffmpeg(['-threads','2','-filter_threads','1','-protocol_whitelist','file,pipe','-f',fmt,
                 '-i',src,'-map',f'0:{v["index"]}','-an','-sn','-dn','-map_metadata','-1','-map_chapters','-1','-vf',afd,
                 '-frames:v',secondes*FPS,'-c:v','libx264','-threads:v','2','-preset','ultrafast','-g','30','-crf','15','-pix_fmt','yuv420p',
                 '-metadata:s:v','rotate=0','-movflags','+faststart',dest])
        n=o.sonde(dest)['streams'][0]
    except Erreur as e: raise Erreur('PRISE',f'{s} : la vidéo ne se décode pas.',s) from e
    exige(int(n.get('nb_frames',0))==secondes*FPS and n.get('avg_frame_rate')=='30/1', 'PRISE', f'{s} : il manque des images pour atteindre {secondes} s.',s)
    return {'dimensions_entree':[w,h], 'images_utilisables':secondes*FPS, 'original_son':any(x['codec_type']=='audio' for x in d['streams']), 'normalisation':'SDR, rotation FFmpeg, cadre centré, 30 i/s'}


class Source:
    def __init__(self,p):
        self.c=cv2.VideoCapture(str(p),cv2.CAP_FFMPEG,[cv2.CAP_PROP_N_THREADS,1]); self.i=-1; self.frame=None
        exige(self.c.isOpened(),'IMAGE','Le flux normalisé ne s’ouvre pas.')

    def at(self,f):
        if f<self.i or f>self.i+16:
            exige(self.c.set(cv2.CAP_PROP_POS_FRAMES,f),'IMAGE','Accès à une image impossible.'); self.i=f-1
        while self.i<f:
            ok,self.frame=self.c.read();exige(ok,'IMAGE','Une prise se termine avant le raccord.');self.i+=1
        return self.frame


def clamp(t): return max(0.,min(1.,t))
def ease(t): return 1-(1-clamp(t))**2
def smooth(t): t=clamp(t);return t*t*(3-2*t)
def mix(a,b,t): return a+(b-a)*t
def bgr(im): return cv2.cvtColor(np.array(im),cv2.COLOR_RGB2BGR)


def papier(sombre=False):
    y=np.linspace(0,1,H,dtype=np.float32)[:,None,None]; u=np.linspace(0,1,W,dtype=np.float32)[None,:,None]
    low,high=(np.array((55,79,63)),np.array((23,43,36))) if sombre else (np.array((245,239,224)),np.array((225,235,223)))
    a=np.clip(y*.76+u*.22,0,1); im=Image.fromarray(np.uint8(low*(1-a)+high*a));d=ImageDraw.Draw(im)
    color='#64836d' if sombre else '#c8d7bd'
    for j in range(5):
        d.ellipse((389+j*14,-530+j*29,1113-j*12,464+j*22),outline=color,width=1)
        d.ellipse((-555-j*14,658+j*31,334+j*15,1620+j*20),outline=color,width=1)
    return im


def lines(d,text,font,limit):
    out=[]; line=''
    for word in text.split():
        if d.textlength(word,font=font)>limit:return None
        s=(line+' '+word).strip()
        if line and d.textlength(s,font=font)>limit:out.append(line);line=word
        else:line=s
    return out+[line] if line else out


class Lettrage:
    def __init__(self,fonts): self.fonts=fonts;self.cache={}
    def font(self,sz,serif=False):
        key=sz,serif
        if key not in self.cache:self.cache[key]=ImageFont.truetype(self.fonts/FONT_NAMES[serif],sz)
        return self.cache[key]

    def bloc(self, d, texte, y, taille, couleur, nmax=2, serif=False, width=590):
        if not texte:return
        for size in range(taille,13,-2):
            f=self.font(size,serif); ls=lines(d,texte,f,width)
            if ls and len(ls)<=nmax:break
        else:raise Erreur('FICHE','Un texte dépasse la zone disponible. Raccourcis-le dans la fiche.')
        for j,ligne in enumerate(ls):d.text((W//2,round(y+(j-(len(ls)-1)/2)*size*1.18)),ligne,font=f,fill=couleur,anchor='mm')

    def base(self,dark,titre,detail=None):
        a=papier(dark);d=ImageDraw.Draw(a);ink=SAGE if dark else MOSS
        d.text((360,116),'T3    /    APPORTER UNE PREUVE',font=self.font(24),fill=ink,anchor='mm')
        d.line((55,163,665,163),fill=ink,width=1)
        if titre:self.bloc(d,titre,219,30,ink)
        if detail:self.bloc(d,detail,1062,36,ink,3,True)
        return a

    def cartons(self,x):
        intro=self.base(True,None);d=ImageDraw.Draw(intro);d.polygon([(360,344),(368,352),(360,360),(352,352)],outline=GOLD)
        self.bloc(d,x['geste'],898,30,SAGE,2)
        title=Image.new('L',(W,H));self.bloc(ImageDraw.Draw(title),x['service'],546,103,255,3,True)
        s1=self.base(False,x['service'],'À découvrir');s2=self.base(False,x['service'],x['geste']);fr=self.base(False,x['service'],'Le geste en détail')
        dip=papier();d=ImageDraw.Draw(dip);self.bloc(d,'Deux angles',176,65,PINE,1,True);self.bloc(d,x['detail'],1110,32,MOSS,2)
        end=self.base(True,x['nom'] or x['service']);d=ImageDraw.Draw(end)
        self.bloc(d,loi()['fiche']['action']['choix'][x['action']] or x['service'],540,87,IVORY,2,True)
        d.line((153,687,567,687),fill=GOLD,width=2)
        self.bloc(d,x['cible'],756,34,SAGE,2);self.bloc(d,x['prix'],887,40,IVORY,2);self.bloc(d,x['lieu'],1004,31,SAGE,2)
        return bgr(intro), np.array(title), bgr(s1), bgr(s2), bgr(fr), bgr(dip), bgr(end),bgr(papier())


def crop(img,w,h,cy=.5,zoom=1.):
    sh,sw=img.shape[:2];k=max(w/sw,h/sh)*zoom
    dx=(w-sw*k)*.5; dy=min(0,max(h-sh*k,h*.5-sh*cy*k))
    m=np.float32([[k,0,dx],[0,k,dy]])
    return cv2.warpAffine(img,m,(w,h),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)


def paste(a,b,x,y):
    h,w=b.shape[:2];l=max(x,0);r=min(x+w,W);t=max(y,0);u=min(y+h,H)
    if l<r and t<u:a[t:u,l:r]=b[t-y:u-y,l-x:r-x]


def panneau(a,img,x,y,w,h,cy=.5,zoom=1.,cadre=True):
    x,y,w,h=map(round,(x,y,w,h));
    if x>=W or y>=H or x+w<=0 or y+h<=0:return
    if cadre:cv2.rectangle(a,(x-3,y-3),(x+w+2,y+h+2),(177,202,184),-1)
    paste(a,crop(img,w,h,cy,zoom),x,y)


class Montage:
    def __init__(self,t,fiche,fonts):
        self.layers=Lettrage(fonts).cartons(fiche);self.s=[Source(p) for p in t]
    def close(self):
        for src in self.s:src.c.release()
    def frame(self,f):
        a,m,s1,s2,fr,dip,end,pap=self.layers; s=self.s
        if f<TITRE:
            q=ease(f/15);mask=m if f>=15 else cv2.GaussianBlur(m,(0,0),max(.4,13*(1-q)))
            blend=mask.astype(np.float32)[...,None]*(.68+.32*q)/255
            return np.uint8(a+blend*(np.array((223,240,246),dtype=np.float32)-a))
        if f<S2:
            z=s[0].at(11+f-TITRE)
            if f<FENETRE:return z
            q=smooth((f-FENETRE)/(S2-FENETRE-1)); b=s1.copy()
            panneau(b,z,56*q,239*q,mix(W,608,q),mix(H,720,q),cadre=q>.12);return b
        if f<FRISE:
            b=s2.copy();panneau(b,s[1].at(13+f-S2),56,239,608,720);return b
        if f<PREUVE:
            u=smooth((f-FRISE)/44);v=clamp((f-PULSE)/(PREUVE-PULSE));q=v*v; y=f-FRISE
            b=fr.copy() if not v else cv2.addWeighted(fr,max(0.,1.-3*v),pap,min(1.,3*v),0.)
            x=mix(56,-113,u);w=mix(608,240,u);pw=mix(425,672,q);ph=mix(759,1100,q)
            panneau(b,s[1].at(13+FRISE-S2+y+round(5*q)),x-138*q,mix(239,330,u),w,mix(720,570,u))
            panneau(b,s[3].at(12+y+round(5*q)),x+w+457+171*q,343,259,549)
            # Accélération sur le panneau sortant ; le plan suivant repart exactement à 1×.
            px=mix(x+w+16,360-pw/2,min(1.,1.12*q));z=s[2].at(108-(PREUVE-FRISE)-8+y+round(8*q))
            panneau(b,z,px,mix(222,91,q),pw,ph,zoom=1+.022*q)
            if f>=PREUVE-4:b=cv2.addWeighted(b,.8,crop(b,W,H,zoom=1.034),.2,0.)
            return b
        if f<S4:return s[2].at(108+f-PREUVE)
        if f<RAPPEL:return s[3].at(8+f-S4)
        if f<DIP:return s[2].at(199+f-RAPPEL)
        if f<CTA:
            j=f-DIP; b=dip.copy();q=.29+.71*ease(j/13)
            up=crop(s[0].at(115+j),608,352); dn=crop(s[3].at(115+j),608,395)
            p=round(352*q);r=round(395*q);paste(b,up[352-p:],56,254+352-p);paste(b,dn[:r],56,627)
            return b
        return end


def preparer_polices(dest, chemin):
    import shutil
    dest.mkdir(parents=True,exist_ok=True)
    for name in FONT_NAMES:shutil.copyfile(chemin/name,dest/name)


def composer(o, fiche, prises, out, fonts, progression):
    req=loi(); exige(all((fonts/k).is_file() for k in FONT_NAMES),'POLICES','Les polices du lot manquent.')
    with TemporaryDirectory(prefix='image-t3-',dir=out.parent) as tmp:
        q=Path(tmp); clips=[]; preuves={}
        for i,s in enumerate(TAKES):
            p=q/(s+'.mp4');progression('prises',12+i*6)
            preuves[s]=normaliser(o,prises[s],p,s,req['prises'][s]['secondes']); clips.append(p)
        m=Montage(clips,fiche,fonts); dest=q/'image.mp4';stderr=q/'encodage.log'
        args=[o.ff,'-nostdin','-hide_banner','-v','error','-xerror','-filter_threads','1','-f','rawvideo','-pix_fmt','bgr24',
              '-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','pipe:0','-an','-map_metadata','-1',
              '-vf','scale=in_range=pc:out_range=tv:out_color_matrix=bt709','-c:v','libx264','-preset','veryfast','-threads:v','2','-crf','20',
              '-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-movflags','+faststart',str(dest)]
        try:
            with stderr.open('wb') as log, sp.Popen(args,stdin=sp.PIPE,stderr=log) as proc:
                try:
                    for f in range(N):
                        a=m.frame(f);proc.stdin.write(np.ascontiguousarray(a).data)
                        if f%90==0:progression('image',38+(f//90)*4)
                    proc.stdin.close()
                    exige(proc.wait(timeout=80)==0,'IMAGE','Échec de l’encodage image.')
                except BaseException:
                    proc.kill();proc.wait();raise
        except (OSError,sp.SubprocessError) as e:
            raise Erreur('IMAGE','Échec de l’encodage image.') from e
        finally:m.close()
        sig=o.signature(dest,muet=True);o.ffmpeg(['-protocol_whitelist','file,pipe','-f','mov','-i',dest,'-map','0:v:0','-f','null','-'])
        dest.replace(out)
    return sig,preuves
