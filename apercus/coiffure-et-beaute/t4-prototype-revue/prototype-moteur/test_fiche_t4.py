#!/usr/bin/env python3
"""Tests du premier adaptateur de fiche T4, sans présumer d'une validation de l'implémentation."""
from pathlib import Path
import json,hashlib
from fiche_t4 import verifier,vers_image,FicheInvalide,ACTIONS
base={'nom_offre':'Gloss transparent','situation_conseillee':'Pour un peu de brillance sans couleur','detail_visible':'Le reflet à la lumière','action':'commande','action_confirmee':True,'accroche':'Envie de brillance ?'}
y=verifier(base);assert y['prix'] is None and y['destination']=='' and y['prix_confirme'] is False
v=vers_image(base);assert v=={'accroche':'Envie de brillance ?','offre':'Gloss transparent','detail_visible':'Le reflet à la lumière','invitation':'Passez commande.'}
assert vers_image(base|{'action':'aucune','accroche':''})=={'accroche':'Gloss transparent','offre':'Gloss transparent','detail_visible':'Le reflet à la lumière','invitation':'Gloss transparent'}
for action,text in ACTIONS.items():assert vers_image(base|{'action':action})['invitation']==(text or 'Gloss transparent')
for price in [('2500','FCFA','exact'),('50.25','EUR','depart')]:
 x=verifier(base|{'prix':price[0],'devise':price[1],'type_prix':price[2],'prix_confirme':True});assert x['prix_confirme'] is True
 assert price[0] not in vers_image(base|{'prix':price[0],'devise':price[1],'type_prix':price[2],'prix_confirme':False}).get('signature','')
 assert price[0] in vers_image(base|{'prix':price[0],'devise':price[1],'type_prix':price[2],'prix_confirme':True})['signature']
contact=base|{'moyen':'message','destination':'CONTACT FICTIF'}
assert 'CONTACT FICTIF' not in vers_image(contact).get('signature','')
assert 'CONTACT FICTIF' in vers_image(contact|{'destination_autorisee':True})['signature']
assert vers_image(base|{'nom_affiche':'Activité fictive','lieu_affiche':'Ville fictive'})['signature']=='Activité fictive · Ville fictive'
reject=[{'action_confirmee':False},{'nom_offre':''},{'detail_visible':''},{'situation_conseillee':'pour tout le monde'},{'action':'inventee'},{'action':'aucune','moyen':'message','destination':'numero'}, {'destination':'test'},{'moyen':'message'}, {'moyen':'lien','destination':'javascript:alert(1)'},{'prix':'5'},{'prix':'NaN','devise':'FCFA','type_prix':'exact'},{'prix':'3.456','devise':'FCFA','type_prix':'exact'},{'devise':'FCFA'}, {'nom_offre':'<script>'},{'imprevu':'x'},{'prix_confirme':'oui'}]
for value in reject:
 try:verifier(base|value)
 except FicheInvalide:pass
 else:raise AssertionError('Fiche invalide acceptée : '+str(value))
r={'resultat':'PASS','portee':'adaptateur expérimental ; ne couvre ni l’interface validée, ni la réalité des détails, l’accessibilité d’une destination, la promesse, les prix réels, ni l’envoi','actions_verifiees':len(ACTIONS),'rejets_verifies':len(reject),'cas_produit_et_service':'les mêmes champs acceptent produit ou service ; une identité fictive ci-dessus','sha_fiche_module':hashlib.sha256((Path(__file__).parent/'fiche_t4.py').read_bytes()).hexdigest()};(Path(__file__).parent/'Recette-fiche-prototype.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('PASS',len(ACTIONS),'actions et',len(reject),'rejets')
