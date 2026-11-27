# Contrat T1 beauté — révision structurée

Le T1 beauté est distinct du T1 restaurant. Le nom historique `T2` subsiste dans le code et le plan du moteur coiffure ; il ne désigne pas ici le gabarit T2 onglerie.

## Fichiers

- `config/t1-beaute.json` : contrat versionné des cinq questions, quatre prises, douze états et liaisons du rendu.
- `schemas/t1-beaute.schema.json` : structure du contrat ; `schemas/t1-reponses.schema.json` : structure des cinq réponses commerciales, avant normalisation du prix.
- `assets/t1-bootstrap.js` et `assets/t1-contract.mjs` : chargement et contrôles utilisés par les interfaces et le moteur.
- `ingenierie/plan.json` : plan de montage existant, que le contrat référence ; le moteur continue à l’exécuter comme source de vérité des plans et coupes.

## Ce qui est réellement relié

La fiche construit ses champs à partir du JSON. Les guides des quatre prises reprennent les consignes et paramètres du contrat. La galerie utilise les libellés d’étapes et les guides du contrat. La transition après validation de chaque prise utilise la destination de l’état de relecture. Le worker valide le contrat, associe les réponses normalisées au moteur et contrôle la cohérence des prises avec le plan existant. Le moteur ne dessine plus de badges de numéro ou de nom de scène dans la vidéo ; un prix demandé par le client peut toujours être affiché.

Le JSON décrit aussi des informations explicatives (par exemple les destinations commerciales des champs, les limites et les étapes générales) : elles documentent le fonctionnement, mais ne pilotent pas toutes individuellement le moteur. Il ne prétend pas reproduire l’exécution Android Media3 ni toutes les fonctions du contrat restaurant.

## Validation locale

- `python tests/test-t1-contrat.py` : structure des schémas, réponses, plan et plages sources ; nécessite le paquet Python `jsonschema`.
- `node tests/test-t1-runtime.mjs` : validation du contrat et cas invalides.
- Deux parcours Web ont été testés en navigateur : prise d’exemple et import de quatre fichiers, export de deux MP4 H.264/AAC de 30 s, en minimal et avec cinq réponses. Les 12 écrans et le blocage en cas de contrat invalide ont été vérifiés. La caméra physique et l’atelier voix n’ont pas été testés pendant cette révision.

La vidéo coiffure sans repères a été validée séparément. La mise à jour du site ne modifie pas automatiquement les fichiers ou ZIP sur Drive. L’essai MAKE UP avec voix reste à corriger dès que son fichier source est accessible. Les images de démonstration coiffure montrent une prestation déjà commencée ; elles ne constituent pas un véritable avant.
