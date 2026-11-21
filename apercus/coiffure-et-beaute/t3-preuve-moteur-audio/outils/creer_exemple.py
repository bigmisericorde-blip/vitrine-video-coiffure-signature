#!/usr/bin/env python3
"""Quatre mires animées originales. Aucune personne, offre ou prise de client."""
from pathlib import Path
from argparse import ArgumentParser
import math
import subprocess as sp
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.commun import Outils, TAKES, loi
from PIL import Image, ImageDraw, ImageFont


def produire(o,dest,fonts,son=False,teinte=0):
    dest.mkdir(parents=True,exist_ok=True)
    a=ImageFont.truetype(fonts/'DejaVuSans.ttf',15); b=ImageFont.truetype(fonts/'DejaVuSerif.ttf',30)
    themes=[('#f3ead7','#6e9b7c','#193d37'),('#e7c3a9','#dda261','#693920'),('#e5ebe2','#967faf','#403054'),('#d0e0db','#65a79f','#203c48')]
    for i,s in enumerate(TAKES):
        sec=loi()['prises'][s]['secondes']; color,accent,dark=themes[(i+teinte)%4];destfile=dest/(s+'.mp4')
        cap=[o.ff,'-nostdin','-v','error','-n','-f','rawvideo','-pix_fmt','rgb24','-video_size','360x640','-framerate','30','-i','pipe:0']
        if son and s=='S2':cap+=['-f','lavfi','-i',f'sine=frequency=613:sample_rate=48000:duration={sec}','-map','0:v:0','-map','1:a:0','-c:a','aac','-b:a','96k','-t',str(sec)]
        else:cap+=['-an']
        cap+=['-c:v','libx264','-threads:v','2','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-movflags','+faststart',str(destfile)]
        with sp.Popen(cap,stdin=sp.PIPE) as p:
            for f in range(sec*30):
                t=f/30;dx=round(math.sin(t*.92)*29);dy=round(math.cos(t*.8)*12)
                im=Image.new('RGB',(360,640),color);d=ImageDraw.Draw(im)
                for j in range(5):d.ellipse((9+j*11,137+j*17,351-j*11,534-j*5),outline=accent,width=1)
                d.rounded_rectangle((28,27,118,58),14,fill=dark)
                d.text((73,42),s,font=a,anchor='mm',fill='#ffffff')
                d.text((180,97),loi()['prises'][s]['titre'],font=b,anchor='mm',fill=dark)
                if i in (0,3):
                    d.rounded_rectangle((70,250,292,474),52,fill=accent);d.ellipse((103,310,257,469),fill=dark)
                    d.rounded_rectangle((119+dx,185+dy,243+dx,330+dy),28,fill='#f5e7d0');d.line((150+dx,236+dy,211+dx,236+dy),fill=dark,width=3)
                else:
                    d.ellipse((69,184,292,448),fill='#f0d6bd');d.arc((102,226,167,284),193,351,fill=dark,width=3)
                    d.arc((199,226,259,284),185,339,fill=dark,width=3);d.arc((142,310,220,360),44,140,fill=dark,width=3)
                    x=208+dx; y=304+dy
                    d.ellipse((x-41,y-11,x+12,y+17),fill=color);d.line((x,y,x+94,y+80),fill=dark,width=14);d.line((x-16,y-14,x+15,y+11),fill=accent,width=24)
                d.rounded_rectangle((25,544,335,600),8,fill=dark)
                d.text((44,564),'PRISE SYNTHÉTIQUE',font=a,anchor='lm',fill='#fff5e8');d.text((317,564),f'{t:04.1f}s',font=a,anchor='rm',fill='#fff5e8')
                d.rectangle((43,579,317,583),fill=color);d.rectangle((43,579,43+round(274*f/(sec*30-1)),583),fill=accent)
                p.stdin.write(im.tobytes())
            p.stdin.close()
            if p.wait(timeout=45):raise RuntimeError('Échec de la mire '+s)


if __name__=='__main__':
    c=ArgumentParser(description=__doc__);c.add_argument('--sortie',type=Path,required=True);c.add_argument('--polices',type=Path,required=True);c.add_argument('--son-test',action='store_true');c.add_argument('--ffmpeg');c.add_argument('--variation',type=int,default=0);a=c.parse_args();produire(Outils(a.ffmpeg),a.sortie,a.polices,a.son_test,a.variation)
