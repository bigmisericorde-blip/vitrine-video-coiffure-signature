#!/usr/bin/env python3
"""Téléchargement de préparation, uniquement depuis les sources officielles déjà vérifiées."""
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.commun import ROOT, TRACKS, Outils, lire, sha, exige


def source_sure(url):
    p=urlsplit(url);h=p.hostname or ''
    return p.scheme=='https' and p.port in (None,443) and not p.username and (h=='files.freemusicarchive.org' or h=='archive.org' or h.endswith('.archive.org'))


class Preparation(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        exige(source_sure(newurl),'SOURCE','Redirection hors source officielle.')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def main():
    c=ArgumentParser(description=__doc__);c.add_argument('--sortie',type=Path,required=True);c.add_argument('--ffmpeg');a=c.parse_args();o=Outils(a.ffmpeg)
    sources=lire(ROOT/'sources-musicales.json')['titres'];a.sortie.parent.mkdir(parents=True,exist_ok=True)
    exige(not a.sortie.exists(),'SOURCE','Indique un dossier de sortie neuf.')
    opener=build_opener(Preparation())
    with TemporaryDirectory(prefix='sources-t3-',dir=a.sortie.parent) as temp:
        out=Path(temp)/'originaux';out.mkdir()
        for i in TRACKS:
            t=sources[i];url=t['url_original'];n=t['octets_original'];p=out/(i+'.mp3')
            exige(source_sure(url),'SOURCE','Hôte officiel attendu.')
            with opener.open(Request(url,headers={'User-Agent':'Vitrine-Video-T3/1.0','Accept':'audio/mpeg,*/*'}),timeout=30) as r,p.open('xb') as f:
                exige(r.status==200,'SOURCE',f'Le fichier complet {i} est indisponible.')
                restent=n
                while restent:
                    b=r.read(min(262144,restent));exige(b,'SOURCE',f'Téléchargement {i} incomplet.');f.write(b);restent-=len(b)
                exige(not r.read(1),'SOURCE',f'Le fichier officiel {i} a changé de taille.')
            exige(sha(p)==t['sha256_original'],'SOURCE',f'Édition {i} modifiée : vérifier la provenance et les droits.')
            o.ffmpeg(['-protocol_whitelist','file,pipe','-f','mp3','-i',p,'-map','0:a:0','-f','null','-']);print(i,t['titre'],'HTTP 200, SHA exact, décodage complet',flush=True)
        out.rename(a.sortie)


if __name__=='__main__':main()
