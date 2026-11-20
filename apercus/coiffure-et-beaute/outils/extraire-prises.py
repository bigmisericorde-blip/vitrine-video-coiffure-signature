#!/usr/bin/env python3
"""Reconstruit les 8 prises de démonstration dirigées à partir des sources Pexels créditées."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess

BASE = Path(__file__).resolve().parents[1]
LICENSE = 'https://www.pexels.com/license/'
# identifiant, piste de téléchargement, page, début en secondes, recadrage, facteur de ralenti d’édition
TAKES = {
    'manucure': ('Artem Podrez', [
        (4783398, 'uhd_2560_1440_30fps', 'person-getting-her-nails-done', 0.96, (810,1440,800,0), 1),
        (4783390, 'uhd_2560_1440_30fps', 'woman-getting-red-nail-polish', 1.15, (810,1440,648,0), 1),
        (4783391, 'uhd_2560_1440_30fps', 'woman-getting-red-nail-polish', 1.18, (810,1440,1056,0), 1),
        (4783779, 'uhd_2560_1440_30fps', 'person-showing-her-manicured-nails', 5.00, (810,1440,344,0), 1.37),
    ]),
    'visage': ('olia danilevich', [
        (9335904, 'hd_1920_1080_25fps', 'a-person-applying-facial-mask-on-a-client', 0.05, (606,1080,286,0), 1),
        (9335905, 'hd_1080_1920_25fps', 'a-person-applying-a-face-mask-on-a-client-s-face', 4.60, None, 1),
        (9335918, 'hd_1080_1920_25fps', 'a-person-applying-a-face-mask-on-client-s-face', 2.28, None, 1),
        (9335919, 'hd_1920_1080_25fps', 'a-person-removing-the-face-mask-on-a-woman-s-face', 6.12, (606,1080,406,0), 1.62),
    ]),
}

def sha(path):
    return hashlib.file_digest(path.open('rb'),'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(); p.add_argument('sources',type=Path); p.add_argument('--ffmpeg',default=os.environ.get('FFMPEG','ffmpeg')); a=p.parse_args()
    root=BASE/'site'/'exemples'; out={}
    def ff(*args):
        subprocess.run([a.ffmpeg,'-hide_banner','-loglevel','error','-nostdin','-y','-threads','2','-filter_threads','1',*map(str,args)],check=True)
    for profile,(artist,rows) in TAKES.items():
        d=root/profile;d.mkdir(parents=True,exist_ok=True);out[profile]={'auteur':artist,'licence':LICENSE,'prises':[]}
        for i,(ident,suffix,slug,sec,crop,factor) in enumerate(rows,1):
            src=a.sources/f'{ident}.mp4'; dst=d/f'S{i}.mp4';dur=6 if i==1 else 7
            filters=[f'setpts={factor:.3f}*(PTS-STARTPTS)']
            if crop:filters.append('crop='+':'.join(map(str,crop)))
            filters+=['scale=720:1280:flags=lanczos','setsar=1','fps=30','tpad=stop_mode=clone:stop_duration=0.10']
            ff('-ss',sec,'-i',src,'-t',dur,'-vf',','.join(filters),'-map_metadata','-1','-an','-c:v','libx264','-threads','2','-preset','fast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',dst)
            out[profile]['prises'].append({'prise':f'S{i}','source':f'https://www.pexels.com/video/{slug}-{ident}/','cdn':f'https://videos.pexels.com/video-files/{ident}/{ident}-{suffix}.mp4','source_sha256':sha(src),'debut_s':sec,'facteur_duree':factor,'crop_source':crop,'export_s':dur,'extrait_sha256':sha(dst)})
        ff('-ss',5 if profile=='visage' else 2,'-i',d/'S4.mp4','-vf','scale=540:-2','-frames:v',1,'-q:v',3,'-threads',1,d/'affiche.jpg')
    # Image d’accueil : recadrage d’un moment de la même séance de soin, pas une publicité d’un autre établissement.
    ff('-ss',13,'-i',a.sources/'9335904.mp4','-vf','crop=1200:1080:280:0,scale=680:612','-frames:v',1,'-q:v',3,'-threads',1,root/'visage'/'accueil.jpg')
    ff('-ss',2.3,'-i',root/'coiffure-t1'/'S4.mp4','-vf','scale=540:-2','-frames:v',1,'-q:v',3,'-threads',1,root/'coiffure-t1'/'affiche.jpg')
    (BASE/'recette'/'Provenance-des-prises.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

if __name__=='__main__': main()
