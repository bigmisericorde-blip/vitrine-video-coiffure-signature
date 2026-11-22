#!/usr/bin/env python3
"""Adaptation provisoire des questions T4 validées au prototype ; pas une validation de production.
Ne formule aucune promesse, ne devine aucune destination et ne publie pas de prix non confirmé.
"""
from __future__ import annotations
from decimal import Decimal,InvalidOperation
from urllib.parse import urlsplit
import re

ACTIONS={'conseil':'Demandez conseil.','essai':'Demandez un essai.','commande':'Passez commande.','rendez_vous':'Prenez rendez-vous.','visite':'Passez nous voir.','devis':'Demandez un devis.','aucune':''}
FIELDS={'nom_offre','situation_conseillee','detail_visible','action','action_confirmee','moyen','destination','destination_autorisee','nom_affiche','lieu_affiche','prix','devise','type_prix','prix_confirme','accroche'}

class FicheInvalide(ValueError):pass

def texte(value,nom,maximum,required=False):
 if value is None:value=''
 if not isinstance(value,str):raise FicheInvalide(f'{nom} doit être du texte.')
 value=value.strip()
 if (required and not value) or len(value)>maximum or re.search(r'[<>\x00-\x1f]',value):raise FicheInvalide(f'{nom} est vide ou dépasse les limites du prototype.')
 return value

def verifier(raw):
 if not isinstance(raw,dict) or set(raw)-FIELDS:raise FicheInvalide('Champ de fiche inconnu.')
 y={k:texte(raw.get(k),k,limit,req) for k,limit,req in [('nom_offre',60,True),('situation_conseillee',100,True),('detail_visible',65,True),('accroche',65,False),('nom_affiche',60,False),('lieu_affiche',60,False),('moyen',40,False),('destination',180,False),('devise',12,False)]}
 if y['situation_conseillee'].casefold() in {'tout le monde','pour tout le monde','tous','toutes'}:raise FicheInvalide('Précise une situation ou un usage concret.')
 action=raw.get('action')
 if action not in ACTIONS:raise FicheInvalide('Choisis une action proposée, y compris aucune.')
 y['action']=action
 for key in ('action_confirmee','destination_autorisee'):
  val=raw.get(key,False)
  if type(val) is not bool:raise FicheInvalide('Confirmation incorrecte.')
  y[key]=val
 if action!='aucune' and not y['action_confirmee']:raise FicheInvalide('Confirme que l’action choisie est réellement possible.')
 if action=='aucune' and (y['moyen'] or y['destination']):raise FicheInvalide('Aucune action : aucun moyen ou destination ne doit être ajouté.')
 if y['destination'] and not y['moyen']:raise FicheInvalide('Indique le moyen associé à la destination.')
 if y['moyen'] and not y['destination']:raise FicheInvalide('Indique la destination associée au moyen ou laisse les deux vides.')
 # Une URL renseignée est contrôlée syntaxiquement, pas vérifiée accessible ou autorisée.
 if y['moyen'].casefold() in {'lien','site','url'} and y['destination']:
  u=urlsplit(y['destination'])
  if u.scheme!='https' or not u.hostname or u.username or u.password:raise FicheInvalide('Le lien doit être une URL HTTPS sans identifiant.')
 prix=raw.get('prix');type_prix=raw.get('type_prix');conf=raw.get('prix_confirme',False)
 if type(conf) is not bool:raise FicheInvalide('Confirmation de prix incorrecte.')
 if prix in ('',None):
  if y['devise'] or type_prix or conf:raise FicheInvalide('Sans prix, ne renseigne pas devise ni type ni confirmation.')
  y.update(prix=None,type_prix=None,prix_confirme=False)
 else:
  try:
   if isinstance(prix,bool):raise InvalidOperation
   p=Decimal(str(prix).replace(',','.'))
   if not p.is_finite() or p<0 or p>100_000_000 or p.as_tuple().exponent < -2:raise InvalidOperation
  except (InvalidOperation,ValueError):raise FicheInvalide('Prix invalide.')
  if not y['devise'] or type_prix not in ('exact','depart'):raise FicheInvalide('Précise monnaie et prix exact ou de départ.')
  y.update(prix=format(p,'f'),type_prix=type_prix,prix_confirme=conf)
 return y

def vers_image(raw):
 x=verifier(raw)
 # Pas de génération automatique de promesse. L'accroche est saisie ; si absente, seul le nom est repris.
 # Pas d’action => le nom de l’offre reste à l’écran, sans invitation inventée.
 v={'accroche':x['accroche'] or x['nom_offre'],'offre':x['nom_offre'],'detail_visible':x['detail_visible'],'invitation':ACTIONS[x['action']] or x['nom_offre']}
 parts=[x['nom_affiche'],x['lieu_affiche']]
 if x['prix'] is not None and x['prix_confirme']:
  parts.append(('À partir de ' if x['type_prix']=='depart' else '')+x['prix']+' '+x['devise'])
 # Seule une destination explicitement autorisée à la diffusion figure à l'écran ; son accès réel reste à vérifier par l'annonceur.
 if x['destination'] and x['destination_autorisee'] and x['action']!='aucune':parts.append(x['destination'])
 parts=[p for p in parts if p]
 if parts:v['signature']=' · '.join(parts)
 return v
