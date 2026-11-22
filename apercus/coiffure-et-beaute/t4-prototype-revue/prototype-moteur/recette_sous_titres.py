#!/usr/bin/env python3
"""Vérifie les sous-titres saisis, sur un film de mires, jamais une transcription automatique."""
from pathlib import Path
import subprocess,json
from sous_titres import valider,appliquer,SousTitresInvalides
from son_t4 import sha
D=Path(__file__).resolve().parent;base=D/'tests-sur-mires/EX01-produit-mires-muet.mp4';out=D/'tests-sur-mires/EX01-sous-titres-fictifs.mp4';assert not out.exists()
cues=[{'debut':.5,'fin':3.2,'texte':'Un parfum pour tous les jours ?'},{'debut':18,'fin':20.9,'texte':'Regardez le détail de près.'},{'debut':25,'fin':28,'texte':'Demandez un essai.'}]
invalid=[[{'debut':3,'fin':2,'texte':'Erreur'}],[{'debut':0,'fin':31,'texte':'Erreur'}],[{'debut':0,'fin':2,'texte':'A'},{'debut':1,'fin':3,'texte':'B'}],[{'debut':0,'fin':3,'texte':'<script>'}],[{'debut':24,'fin':25,'texte':'Zone de transition'}]]
for x in invalid:
 try:valider(x)
 except SousTitresInvalides:pass
 else:raise AssertionError('Mauvais sous-titre accepté')
r=appliquer(base,cues,out);assert not r['voix_ou_texte_verify'] and r['source_sha256']==sha(base)
for n,s in enumerate([1.5,19,26]):subprocess.run(['ffmpeg','-v','error','-ss',str(s),'-i',str(out),'-frames:v','1','-y',str(D/f'Sous-titre-mire-{n+1}.png')],check=True)
report={'resultat':'PASS technique','portee':'Trois sous-titres fictifs saisis manuellement, incrustés en DM Sans 600 sur mires. Aucun test de correspondance avec une voix ni validation visuelle ; le texte et les temps exigent une relecture humaine.','module_sha256':sha(D/'sous_titres.py'),'video_sha256':sha(out),'source_inchangee':r['source_sha256'],'rejets':len(invalid),'cues':cues};(D/'Recette-sous-titres-prototype.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('PASS sous-titres manuels sur mires')
