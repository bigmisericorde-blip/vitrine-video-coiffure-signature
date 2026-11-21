#!/usr/bin/env python3
"""Recette moteur fondée sur la fiche et quatre prises ; lancer sur un dossier neuf."""
from argparse import ArgumentParser
from pathlib import Path
from shutil import copy2
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from engine.commun import ROOT, TAKES, TRACKS, Outils, Erreur, lire, lire_fiche, objsha, ecrire, sha
from engine import musiques
from t3 import rendre, chemins_prises, annuler
from creer_exemple import produire


def ok(good,s):
    if not good:raise RuntimeError('Contrôle échoué : '+s)


def negatif(code,call):
    try:call()
    except Erreur as e:ok(e.code==code,f'{code} attendu, {e.code} reçu');return e.as_dict()
    raise RuntimeError(f'{code} attendu, mais l’action a réussi')


def progress(p,n):
    if p in ('controle','musique','termine'):print(f'  · {p} {n} %',flush=True)


def decode(o,p,fmt):
    b=o.ffmpeg(['-protocol_whitelist','file,pipe','-f',fmt,'-i',p,'-map','0:a:0','-ar','48000','-ac','2','-f','f32le','pipe:1']).stdout
    return np.frombuffer(b,dtype='<f4').reshape((-1,2))


def frame(o,f,p):
    # Trame exacte de la sortie CFR, ramenée en RGB à une taille de contrôle.
    b=o.ffmpeg(['-threads','2','-f','mov','-i',p,'-vf',f"select=eq(n\\,{f}),scale=144:256",'-frames:v','1','-an','-pix_fmt','rgb24','-f','rawvideo','pipe:1']).stdout
    ok(len(b)==144*256*3,'trame décodée');return np.frombuffer(b,dtype='u1').reshape(256,144,3).astype('f4')


def cfr(o, dossier, p, fiche, pack, fonts, no=1):
    print('Master neuf, à partir des 4 prises',flush=True)
    muet=render(o,fiche,p,dossier,fonts,pack,no,mode='muet');j=muet['job_id']
    src=dossier/'exports'/j/'T3.mp4';sig=o.signature(src,True);check_decoded_video(o,src)
    ok(not (dossier/'rotation.json').exists(),'muet sans rotation')
    ok(not muet['image_reutilisee'] and sig==muet['image']['signature'],'nouveau master')
    ok(muet['prises_sha256']=={s:sha(p[s]) for s in TAKES} and muet['fiche_sha256']==objsha(lire_fiche(fiche)),'entrées réellement lues')
    src_tag={'sha256':sha(src),'octets':src.stat().st_size,'image':sig,'original_son':{k:muet['image']['prises'][k]['original_son'] for k in TAKES}}
    cat=musiques.verifier(pack); rows={}
    # Image recomposée une fois, jamais prémixée. Les pistes sont chacune muxées au moment du job.
    for k,track in enumerate(TRACKS,no+1):
        print('Piste '+track,flush=True);d=render(o,fiche,p,dossier,fonts,pack,k,piste=track);f=export(dossier,d)
        m=d['musique'];line=(f.parent/'Credit-musique.txt').read_text(encoding='utf-8').rstrip('\n')
        ok(d['image_reutilisee'] and m['piste']==track and o.signature(f,False)==sig,'image et cadence identiques')
        ok(m['credit']==line==o.sonde(f)['format']['tags']['comment']==cat['titres'][track]['credit'],'crédit lisible et métadonnées')
        ok(track!='01' or '1000Handz.com' in line,'crédit Copa en description')
        a=decode(o,pack/(track+'.flac'),'flac');b=decode(o,f,'mov')
        # Autre vérification que les tags : AAC doit correspondre au signal de la bonne piste.
        ok(a.shape==(1440000,2) and 1440000<=len(b)<1441024,'échantillons de la piste et padding AAC final borné')
        b=b[:len(a)];rho=float(np.corrcoef(a.ravel(),b.ravel())[0,1]);ok(rho>.99,f'signal audio de la bonne piste (r={rho:g})')
        ok(-24<=m['lufs_i']<=-16 and m['dbtp']<=-2,'plage musicale mesurée')
        ok(lire(dossier/'rotation.json')['dernier_succes']==track,'rotation avancée au succès')
        rows[track]=m|{'correlation_pcm_aac':round(rho,6),'mp4_sha256':sha(f),'octets':f.stat().st_size}
    return {'master_muet':src_tag,'exports':rows},src


def check_decoded_video(o,p):
    o.ffmpeg(['-protocol_whitelist','file,pipe','-f','mov','-i',p,'-map','0:v:0','-f','null','-'])


def render(o,fiche,p,dossier,fonts,pack,n,**kw):
    return rendre(o,fiche,p,dossier,fonts,pack,f'{n:032x}',progression=progress,**kw)


def export(dossier,d):return dossier/'exports'/d['job_id']/'T3.mp4'


def suite(o,report,src,base,p,fiche,pack,fonts,d):
    fd=base/'rotation.json';initial=lire(fd);ok(initial['dernier_succes']=='04','suite avec 04')
    ne={}
    ne['fiche_incomplete']=negatif('FICHE',lambda:render(o,fiche|{'geste':''},p,base,fonts,pack,6));
    ne['piste_inconnue']=negatif('JOB',lambda:render(o,fiche,p,base,fonts,pack,6,piste='99'))
    ne['pas_de_repetition']=negatif('ROTATION',lambda:render(o,fiche,p,base,fonts,pack,6,piste='04'))
    ne['pack_inexistant']=negatif('PACK',lambda:render(o,fiche,p,base,fonts,d/'absent',6));
    damaged=d/'pack-blesse';damaged.mkdir();copy2(pack/'catalogue.json',damaged);(damaged/'01.flac').write_bytes(b'pas un fond complet');
    ne['flac_invalide']=negatif('PACK',lambda:render(o,fiche,p,base,fonts,damaged,6));
    (damaged/'01.flac').unlink();ne['pack_incomplet']=negatif('PACK',lambda:render(o,fiche,p,base,fonts,damaged,6))
    ok(lire(fd)==initial,'négatifs sans changement de rotation')
    old=render(o,fiche,p,base,fonts,pack,3,piste='02');ok(sha(export(base,old))==report['exports']['02']['mp4_sha256'] and lire(fd)==initial,'relance d’un ancien job idempotente')
    ne['id_reutilise_avec_autre_fiche']=negatif('JOB',lambda:render(o,fiche|{'nom':'Autre nom'},p,base,fonts,pack,3,piste='02'))
    control=d/'prise-courte.mp4';o.ffmpeg(['-f','mov','-i',p['S1'],'-an','-map','0:v:0','-c:v','copy','-t','2',control]);
    short=p|{'S1':control}
    ne['prise_trop_courte']=negatif('PRISE',lambda:render(o,fiche,short,base,fonts,pack,6));res=lire(fd);choice=res['reserve']['piste']
    ok(res['dernier_succes']=='04' and choice!='04' and not (base/'exports'/f'{6:032x}').exists(),'erreur non publiée, aucune rotation')
    ne['relance_conserve_piste']=negatif('PRISE',lambda:render(o,fiche,short,base,fonts,pack,6))
    ok(lire(fd)==res,'échec reproductible avec réservation conservée')
    ne['job_suivant_en_attente']=negatif('EN_COURS',lambda:render(o,fiche,p,base,fonts,pack,7));annuler(base,f'{6:032x}');ok(lire(fd)==initial,'abandon ne fait pas avancer')
    # Simule une interruption de processus après la publication atomique du MP4, avant l’état de rotation.
    last=render(o,fiche,p,base,fonts,pack,7);chosen=last['musique']['piste'];ok(chosen!='04','rotation auto différente');
    ecrire(fd,initial|{'reserve':{'job':last['job_id'],'piste':chosen,'requete':last['requete_sha256']}})
    again=render(o,fiche,p,base,fonts,pack,7);now=lire(fd)
    ok(again==last and now['dernier_succes']==chosen and now['reserve'] is None,'reprise après publication réussie')
    print('Deuxième fiche et prise modifiée',flush=True)
    variation=d/'variante';produire(o,variation,fonts,teinte=1);x=fiche|{'service':'Soin hydratant en cabine','action':'venir','cible':'Sur place · exemple fictif'}
    var=render(o,x,p|{'S3':variation/'S3.mp4'},base,fonts,pack,8,mode='muet');v=export(base,var)
    ok(not var['image_reutilisee'] and var['image']['signature']!=report['master_muet']['image'],'nouveau rendu de la variante')
    changements={k:float(np.mean(np.abs(frame(o,n,src)-frame(o,n,v)))) for k,n in [('titre',22),('detail',386),('carton',780)]}
    ok(all(j>1.0 for j in changements.values()),'variantes visibles dans titre, preuve et carton')
    return {'rejets':ne,'rotation':{'dernier_avant':'04','automatique_apres':chosen,'succes_seul':True,'relance_idempotente':True,'reprise_apres_ecriture_mp4':True,'annulation_sans_avancer':True},
            'variante':{'empreinte':sha(v),'changes_visibles_pixels_mae':{k:round(j,3) for k,j in changements.items()}}}


def main():
    c=ArgumentParser(description=__doc__);c.add_argument('--sortie',type=Path,required=True);c.add_argument('--pack',type=Path,default=ROOT/'audio');c.add_argument('--polices',type=Path,default=ROOT/'polices');c.add_argument('--prises',type=Path,default=ROOT/'exemple');c.add_argument('--fiche',type=Path,default=ROOT/'exemple/fiche.json');c.add_argument('--ffmpeg');c.add_argument('--ffprobe');c.add_argument('--prive',action='store_true',help='Sonder quatre prises privées ; garder ce rapport en local.');a=c.parse_args()
    o=Outils(a.ffmpeg,a.ffprobe);a.sortie.mkdir(parents=True);p=chemins_prises(a.prises);x=lire(a.fiche);base=a.sortie/'session'
    r,mp4=cfr(o,base,p,x,a.pack,a.polices);rep={'schema':1,'statut':'PASS','revision':lire(ROOT/'contrat.json')['revision'],'test':'privé hors paquet' if a.prive else 'mires synthétiques reproductibles',
                       'outils':{k:o.run(v,['-version']).stdout.decode().splitlines()[0] for k,v in [('ffmpeg',o.ff),('ffprobe',o.fp)]},
                       'master_de_revue_utilise':False,'voix_ajoutee':False,'identite_h264_et_pts_dts':True,'bornes_images':lire(ROOT/'contrat.json')['bornes_images'],**r}
    if not a.prive:
        ok(r['master_muet']['original_son']['S2'],'la mire S2 contenait le témoin audio')
        rep.update(suite(o,r,mp4,base,p,x,a.pack,a.polices,a.sortie))
    ecrire(a.sortie/'Controle-moteur-T3.json',rep);print(json.dumps({'statut':'PASS','exports':4,'master':r['master_muet']['sha256']},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
