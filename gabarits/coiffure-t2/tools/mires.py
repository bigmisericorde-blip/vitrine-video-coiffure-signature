#!/usr/bin/env python3
"""Regénère les quatre clips de recette originaux, sans modèle ni média tiers."""
import argparse
import math
import os
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont

W,H,FPS=360,640,30
PALETTES=(('#10262e','#308774'),('#25223e','#855ac4'),('#301e23','#b76c4c'),('#1d3339','#3e96a6'))

def make(folder, ffmpeg):
    folder.mkdir(parents=True,exist_ok=True)
    for stage,(base,ink) in enumerate(PALETTES,1):
        secs=6 if stage==1 else 7
        output=folder/f'S{stage}.mp4'
        command=[ffmpeg,'-y','-v','error','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart','-map_metadata','-1',str(output)]
        p=subprocess.Popen(command,stdin=subprocess.PIPE)
        head=ImageFont.load_default(size=25); small=ImageFont.load_default(size=13)
        try:
            for f in range(secs*FPS):
                im=Image.new('RGB',(W,H),base);d=ImageDraw.Draw(im)
                for x in range(24,W,24):d.line((x,28,x,H-28),fill='#334048',width=1)
                for y in range(28,H,24):d.line((24,y,W-24,y),fill='#334048',width=1)
                d.rounded_rectangle((24,56,336,535),radius=26,outline=ink,width=2)
                for line in range(7+stage):
                    pts=[]
                    for x in range(50,311,2):
                        y=235+13*line+10*math.sin(x*.045+line*.22+f*.057)*math.cos(line*.25)
                        pts.append((x,y))
                    d.line(pts,fill=ink,width=3)
                d.ellipse((152+42*math.sin(f*.06)-14,353,152+42*math.sin(f*.06)+14,381),fill=ink)
                d.text((45,100),'MIRE DE TEST',font=small,fill='#96b4b5')
                d.text((43,125),f'S{stage} / '+('AVANT','GESTE','DETAIL','RESULTAT')[stage-1],font=head,fill='#c5d9d8')
                d.rectangle((45,506,315,510),fill='#465759');d.rectangle((45,506,45+270*(f+1)/(secs*FPS),510),fill=ink)
                p.stdin.write(im.tobytes())
        finally:
            p.stdin.close()
            if p.wait()!=0:raise RuntimeError(f'Encodage de S{stage} échoué')
        print(output.name, output.stat().st_size, 'octets', flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1]/'fixtures/media');args=a.parse_args()
    make(args.out,os.getenv('FFMPEG','ffmpeg'))
