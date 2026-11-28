# Audit des liaisons des gabarits beauté T1–T4

## Périmètre et méthode

La base comparée est le commit `1afccb39ba160ee68591efb0950070e9fe6c00c9` ; les fichiers de chacun des quatre ZIP précédents correspondaient à ce commit. Les corrections de cette révision concernent le moteur Web et ont été testées dans Chromium automatisé. La saisie et les prises utilisées sont fictives. Demander les droits des images et des musiques avant diffusion.

## Liaison des réponses

| Gabarit | Champs de la fiche et destinations | Vérification sur film |
|---|---|---|
| T1 | Nom d'activité, service, ville/lieu, prix et contact sont reliés au moteur commercial. | Kofi Coiffure, Coupe homme, Cotonou Akpakpa, 4500 FCFA et le numéro fictif sont visibles. |
| T2 | Nom, service, outil, ville/lieu, contact confirmé et prix. L'outil, auparavant seulement utilisé dans la consigne, est maintenant transmis dans `RenderJob.answers.outil` et dessiné dans la scène du geste. | Awa Ongles, Pose de vernis, Pinceau fin, Cotonou Akpakpa, 2500 FCFA et le numéro fictif sont visibles. |
| T3 | Nom et service à l'ouverture ; outil dans la scène prévue ; nom, lieu, prix et numéro confirmé dans la signature. Le contrat de séquencement fournit les noms de champs au moteur. | Lina Regard, Pose de cils, Pince fine, Cotonou Akpakpa, 5000 FCFA et le numéro fictif sont visibles. |
| T4 | Nom, service, public visé, détail, lieu, numéro autorisé, prix confirmé et action confirmée. Le public visé, auparavant seulement dans le guide, est maintenant visible en S2 ; les textes métier restent visibles en bas quand des sous-titres occupent le haut. | Mina Beaute, Pose de vernis, Pour ongles soignes, Vernis rouge brillant, Cotonou Akpakpa, 3500 FCFA, numéro fictif et Écrivez-nous sont visibles. Un essai distinct couvre les sous-titres. |

Ville et quartier sont saisis dans le même champ, et non deux champs séparés. Les confirmations, choix techniques et cases de consentement ne sont pas des réponses commerciales à incruster. Un champ facultatif laissé vide n'est pas inventé. L'affichage du contact exige les confirmations prévues. Les intitulés WhatsApp ne sont pas harmonisés sur les quatre gabarits.

## Scènes, 12 écrans et JSON

Les 12 écrans désignent quatre prises S1–S4 avec trois états de guidage/capture/relecture chacune ; ce ne sont pas 12 prises finales. Les outils de validation inclus contrôlent les champs, les quatre scènes, les 12 états/transitions et les schémas/structures des plans respectifs : `tests/test-t1-contrat.py`, `gabarits/coiffure-t2/tools/verify-contracts.py`, `gabarits/coiffure-t3/ingenierie/verifier-contrat.py`, `gabarits/coiffure-t3/ingenierie/verifier-candidat.py`, `gabarits/coiffure-t4/ingenierie/verifier-t4.py`. Le test `gabarits/coiffure-t2/tools/test-liaison-outil.mjs` vérifie la propagation de l'outil dans les quatre variantes. Les contrats sont propres à chaque moteur Web ; ils ne sont pas interchangeables.

## Plafond et tests

T1 et T2 vérifient désormais le MP4 final (durée déclarée et durée mesurée, présence d'une piste audio) avant de le proposer ; tout dépassement de 30 secondes est refusé sans recoupe. Des MP4 de 5 s et 31 s ont été respectivement acceptés et refusés par les contrôles T1/T2/T3. T3 et T4 avaient déjà un contrôle final. Exports réalisés et décodés sans erreur FFmpeg : T1 30,000 s, T2 30,000 s, T3 29,952 s, T4 23,018667 s. Tous ont une piste audio. Ces tests ne remplacent pas l'écoute humaine de toutes les variantes ni les tests sur chaque appareil.

## Limites importantes

Le schéma strict restaurant du partenaire a précédemment rejeté les contrats T3 et T4 ; il ne faut pas présenter ces fichiers comme compatibles avec son moteur Android. Une adaptation de schéma, convenue et testée avec ce moteur, est encore nécessaire. Aucun appareil Android physique n'a été testé. Une durée inférieure à 30 s ne prouve pas qu'aucun geste ou phrase ait été tronqué ; l'utilisateur doit examiner ses prises. Les tests réalisés ne prouvent pas tous les choix, médias et navigateurs possibles. Les anciennes vidéos et références restent distinctes de ces nouvelles démonstrations.
