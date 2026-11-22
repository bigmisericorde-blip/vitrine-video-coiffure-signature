#!/usr/bin/env python3
"""Recette négative de l'identité T3 de revue. N'altère que des copies temporaires."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json, shutil, sys

ROOT=Path(__file__).resolve().parents[1]/'t3-preuve-moteur-audio'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'outils'))
import engine.commun as commun
import engine.musiques as musiques
import lot

def enregistrer(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def refuse(code,f,label):
 try:f()
 except commun.Erreur as e:
  assert e.code==code,(label,e.code,e);print('PASS refus',label);return
 raise AssertionError('Accepté à tort : '+label)

with TemporaryDirectory(prefix='t3-ota-negatifs-') as tmp:
 d=Path(tmp)/'t3';shutil.copytree(ROOT,d,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 commun.ROOT=d; c=d/'contrat.json';m=d/'manifest.json'; cat=d/'audio/catalogue.json'
 original=commun.lire(c);manifest=commun.lire(m);catalogue=commun.lire(cat)
 original_bytes,manifest_bytes,catalogue_bytes=c.read_bytes(),m.read_bytes(),cat.read_bytes()
 lot.verifier(d);print('PASS lot nominal et manifeste égal au canonique')
 for key,value in [('template_id',None),('template_id','T3'),('version','1.0.0'),('version','0.1'),('audio_profile','musique.mp3'),('audio_profile',None)]:
  x=dict(original);x[key]=value;enregistrer(c,x);refuse('CONTRAT',commun.loi,f'{key}={value}')
 c.write_text(c.read_text().replace('"schema": 1,','"schema": 1, "schema": 1,',1));refuse('JSON',commun.loi,'doublon JSON')
 c.write_bytes(original_bytes)
 for key,value in [('template_id','AUTRE'),('version',None),('audio_profile','autre-profil'),('statut','production'),('publication_autorisee',True)]:
  x=dict(manifest);x[key]=value;enregistrer(m,x);refuse('LOT',lambda:lot.verifier(d),f'manifeste {key}={value}')
 m.write_bytes(manifest_bytes)
 x=dict(catalogue);x['audio_profile']='autre-profil';enregistrer(cat,x);refuse('PACK',lambda:musiques.verifier(d/'audio'),'profil du catalogue incompatible')
 cat.write_bytes(catalogue_bytes);lot.verifier(d)
 print('PASS : 13 contrôles négatifs ; aucune source modifiée.')
