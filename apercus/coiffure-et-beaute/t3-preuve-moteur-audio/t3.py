#!/usr/bin/env python3
"""Moteur de revue T3 : une fiche + S1–S4 → rendu muet ou MP4 avec une piste locale."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import re
import sys
from engine.commun import (ROOT, TRACKS, TAKES, Outils, Erreur, exige, lire, lire_fiche, loi, sha,
                           objsha, ecrire, verrou)
from engine.images import composer, FONT_NAMES, format_entree
from engine import musiques


def chemins_prises(d):
    out={}
    for s in TAKES:
        a=[d/(s+ext) for ext in ('.mp4','.mov','.webm') if (d/(s+ext)).is_file()]
        exige(len(a)==1,'PRISE',f'Indique un seul fichier MP4, MOV ou WebM pour {s}.',s);out[s]=a[0]
    return out


def etat(f, ident):
    x=lire(f) if f.exists() else {'schema':1,'pack_sha256':ident,'dernier_succes':None,'reserve':None}
    exige(x['schema']==1 and x['pack_sha256']==ident,'SESSION','Le catalogue a changé. Ouvre une autre session de rendu.')
    return x


def annuler(work, job):
    f=work/'rotation.json'
    with verrou(work/'rotation.lock'):
        if f.is_file():
            s=lire(f);r=s['reserve']
            if r and r['job']==job:
                exige(not (work/'exports'/job/'resultat.json').exists(),'SESSION','Ce rendu a déjà abouti. Relance pour confirmer le succès.')
                s['reserve']=None;ecrire(f,s)


def choisir(s, job, demande, empreinte):
    r=s['reserve']
    if r:
        exige((r['job'],r['requete'])==(job,empreinte),'EN_COURS','Relance ou abandonne le rendu réservé avant de passer au suivant.')
        return r['piste']
    dispo=[t for t in TRACKS if t!=s['dernier_succes']]
    exige(demande is None or demande in dispo,'ROTATION','Cette piste vient d’être utilisée. Choisis-en une autre ou passe en rotation.')
    i=int.from_bytes(sha256((job+':'+s['pack_sha256']).encode()).digest()[:8],'big')%len(dispo)
    choisi=demande or dispo[i];s['reserve']={'job':job,'requete':empreinte,'piste':choisi}
    return choisi


def image_neuve(o, x, p, hashes, work, fonts, progress):
    # Réemploi uniquement d’une image générée par ce moteur dans cette session,
    # pour exactement la même fiche, les mêmes S1–S4, le même code et les mêmes polices.
    for k in FONT_NAMES:exige((fonts/k).is_file(),'POLICES','Le lot ne contient pas ses polices.')
    ident=objsha({'fiche':x,'prises':hashes,'polices':{k:sha(fonts/k) for k in FONT_NAMES},
                  'module':sha(ROOT/'engine/images.py'),'contrat':sha(ROOT/'contrat.json')})
    folder=work/'images';folder.mkdir(exist_ok=True);d=folder/ident
    pmp4=d/'image.mp4';meta=d/'preuve.json'
    if d.exists():
        z=lire(meta)
        exige(z['sha256']==sha(pmp4),'IMAGE','Image intermédiaire modifiée. Utilise une nouvelle session.')
        return pmp4,z,True
    with TemporaryDirectory(prefix='compose-',dir=folder) as tmp:
        q=Path(tmp)/'image';q.mkdir();img=q/'image.mp4'
        sig, inputs=composer(o,x,p,img,fonts,progress)
        exige(all(sha(p[k])==hashes[k] for k in TAKES),'PRISE','Une prise a changé pendant l’export.')
        z={'sha256':sha(img),'signature':sig,'prises':inputs,
           'construction':'fiche + quatre fichiers de prise; jamais le master d’essai', 'cle':ident}
        ecrire(q/'preuve.json',z);q.rename(d)
    return pmp4,z,False


def rendre(o, fiche, prises, work, fonts, pack, job, mode='musique_seule', piste=None,
           audition=False, progression=lambda *args:None):
    exige(isinstance(job,str) and re.fullmatch(r'[0-9a-f]{32}',job),'JOB','Identifiant technique requis (UUID sans tirets).')
    exige(mode in loi()['audio_modes'] and piste in (*TRACKS,None), 'JOB','Mode audio ou piste inconnu.')
    exige((not audition or (mode=='musique_seule' and piste)) and (mode!='muet' or piste is None),'JOB','Choix incompatible avec ce mode.')
    x=lire_fiche(fiche);exige(set(prises)==set(TAKES),'PRISE','Quatre prises distinctement affectées à S1–S4 sont requises.')
    for s in TAKES:format_entree(prises[s],s)
    hashes={s:sha(prises[s]) for s in TAKES}
    work.mkdir(parents=True,exist_ok=True);rendus=work/'exports';rendus.mkdir(exist_ok=True);dest=rendus/job
    # Pas de réservation si une ressource manque. Pas de rendu « muet par défaut » en cas d’erreur audio.
    cat=musiques.verifier(pack) if mode=='musique_seule' else None
    ident=sha(pack/'catalogue.json') if cat else None
    cle=objsha({'id':job,'contrat':sha(ROOT/'contrat.json'),'fiche':x,'prises':hashes,'audio':ident,
                'mode':mode,'piste_souhaitee':piste,'audition':audition,
                'modules':{k:sha(ROOT/k) for k in ('t3.py','engine/commun.py','engine/images.py','engine/musiques.py')}})
    fd=work/'rotation.json';rot=bool(cat and not audition)
    with verrou(work/'rotation.lock'):
        s=etat(fd,ident) if rot else None
        if dest.exists():
            d=lire(dest/'resultat.json');r=s['reserve'] if rot else None
            exige(d['requete_sha256']==cle and sha(dest/'T3.mp4')==d['mp4_sha256'],'JOB','Cet ID correspond à un autre rendu, ou le fichier a changé.')
            if cat:
                exige((dest/'Credit-musique.txt').read_text(encoding='utf-8')==d['musique']['credit']+'\n',
                       'SORTIE','Le crédit associé a été modifié.')
            if r and r['job']==job:
                exige(r['requete']==cle and r['piste']==d['musique']['piste'],'SESSION','Réservation incohérente.')
                s.update(dernier_succes=r['piste'],reserve=None);ecrire(fd,s)
            return d
        choix=choisir(s,job,piste,cle) if rot else piste
        if rot:ecrire(fd,s)
        progression('controle',8)
        image,z,reprise=image_neuve(o,x,prises,hashes,work,fonts,progression)
        with TemporaryDirectory(prefix='rendu-',dir=rendus) as td:
            q=Path(td)/'lot';q.mkdir(); f=q/'T3.mp4'
            musique=None
            if cat:
                progression('musique',82)
                musique=musiques.joindre(o,image,z['signature'],pack,cat,choix,f)
                (q/'Credit-musique.txt').write_text(musique['credit']+'\n',encoding='utf-8')
            else:
                from shutil import copyfile
                copyfile(image,f)
            progression('verification',95)
            exige(all(sha(p)==hashes[k] for k,p in prises.items()),'PRISE','Une prise a changé pendant le traitement.')
            exige(sha(image)==z['sha256'],'IMAGE','Image intermédiaire modifiée pendant le traitement.')
            d={'schema':1,'job_id':job,'revision':loi()['revision'],'requete_sha256':cle,'format':loi()['media'],
               'audio_profile':loi()['audio_profile'],'mode':mode,'audition':audition,'musique':musique,
               'image':z,'image_reutilisee':reprise,'fiche_sha256':objsha(x),'prises_sha256':hashes,'mp4_sha256':sha(f),
               'octets':f.stat().st_size,'mp4':'T3.mp4','voix_ajoutee':False,'son_original_dans_export':False}
            ecrire(q/'resultat.json',d);q.rename(dest)
        if rot:
            s.update(dernier_succes=choix,reserve=None);ecrire(fd,s)
    progression('termine',100)
    return d


def main():
    c=ArgumentParser(description=__doc__);c.add_argument('--ffmpeg');c.add_argument('--ffprobe');cmd=c.add_subparsers(dest='commande',required=True)
    a=cmd.add_parser('preparer-pack');a.add_argument('--originaux',type=Path,required=True);a.add_argument('--sortie',type=Path,required=True)
    a=cmd.add_parser('rendre');a.add_argument('--fiche',type=Path,required=True);a.add_argument('--prises',type=Path,required=True)
    a.add_argument('--session',type=Path,required=True);a.add_argument('--id',required=True);a.add_argument('--mode',choices=loi()['audio_modes'],default='musique_seule')
    a.add_argument('--piste',choices=TRACKS);a.add_argument('--audition',action='store_true');a.add_argument('--pack',type=Path,default=ROOT/'audio')
    a.add_argument('--polices',type=Path,default=ROOT/'polices')
    a=cmd.add_parser('annuler');a.add_argument('--session',type=Path,required=True);a.add_argument('--id',required=True)
    opt=c.parse_args();o=Outils(opt.ffmpeg,opt.ffprobe)
    try:
        if opt.commande=='preparer-pack':musiques.couper(o,opt.originaux,opt.sortie)
        elif opt.commande=='annuler':
            exige(bool(re.fullmatch('[0-9a-f]{32}',opt.id)),'JOB','Identifiant inconnu.');annuler(opt.session,opt.id)
        else:
            result=rendre(o,lire(opt.fiche),chemins_prises(opt.prises),opt.session,opt.polices,opt.pack,opt.id,opt.mode,
                          opt.piste,opt.audition,lambda tag,n:print(f'{tag} {n}%',file=sys.stderr,flush=True))
            print(json.dumps({'statut':'ok','resultat':result},ensure_ascii=False,indent=2))
    except (Erreur,OSError) as e:
        problem=e.as_dict() if isinstance(e,Erreur) else {'code':'FICHIER','message':'Fichier manquant, inaccessible ou impossible à écrire.'}
        print(json.dumps({'statut':'echec','erreur':problem},ensure_ascii=False),file=sys.stderr);return 2
    return 0


if __name__=='__main__':sys.exit(main())
