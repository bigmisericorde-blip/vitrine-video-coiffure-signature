# T3 r2 — Revue des 12 écrans

## À ouvrir dans cet ordre

1. `index.html` : même galerie que T1/T2 (bandeau, index en quatre lignes, sélecteur, précédent/suivant, écran seul, film à part). Ouvert directement dans un navigateur, il fonctionne sans réseau. L’aperçu est en lecture seule ; ouvrir l’écran seul pour faire défiler toute la consigne.
2. `capture/12-ecrans.md`, `capture/ecrans/01.jpg` à `12.jpg` et `capture/planche-12-ecrans.jpg` : accès individuel, 12 numéros et planche dans l’ordre. `capture/guide.json` donne les consignes, IDs de revue, bornes de lecture et durées proposées. Aucun ID catalogue n’est attribué.
3. « Essayer avec ces prises » ouvre un parcours distinct. « Lire la prise d’exemple » lance le même extrait qu’en galerie. L’arrivée en relecture ne valide rien. « Annuler » / « Refaire » ramènent à la consigne de cette prise ; « Garder… » requiert une relecture et passe à la suivante. Après quatre gardes explicites, retour à la carte du film déjà monté, pas de nouveau rendu. Aucun état d’essai ne survit à sa fermeture. Le film reste aussi accessible directement, sans validation, par « Voir le film ».
4. « Ma fiche » montre les questions courtes et les exemples T3. Aucun formulaire n’est soumis. Revoir `formulaire/Fiche-questions-T3.md`, `recherche/Droits-et-perimetre.md`, les avis OFL et `recherche/Ecriture-et-audio.md` avant toute extension.

## Entrées, sorties et limites

| Vue | Entrée | Sortie (essai uniquement) |
|---|---|---|
| Consigne | Prise S1–S4, arrêt sur image, durée proposée et indications | Lecture du clip de cette prise |
| Chrono | Même clip sans son, sans caméra ; temps écoulé calculé sur la vidéo | Fin → clip candidat pour relecture. Annulation ou erreur → ne rien garder. |
| Relecture | Clip identique, en boucle, muet ; durée et question concrète | Refaire → même consigne. Garder → prise suivante ou accès au film d’exemple après S1–S4. |

En galerie et en écran seul, les commandes de démarrage, reprise et validation des prises sont désactivées. Le chrono et la relecture tournent en boucle pour permettre la comparaison. Les 8/10/10/8 s sont des durées de tournage proposées ; ce ne sont pas les durées du matériau déjà monté. La garde dans l’essai est en mémoire et n’est pas une validation P3.

Aucun accès caméra/micro, import, compte, collecte, moteur, CTA réel, CI, APK, OTA ou donnée à envoyer. La recette Chromium sur fenêtres mobile et bureau ne remplace pas un test physique iOS/Android ni un test avec prise parlée. Le master P2-r3 et l’écriture validée sont inchangés. La fiche et les durées restent proposées. Pour une captation réelle, il faudra notamment gérer l’accord de la personne filmée, les permissions, les prises trop courtes ou illisibles et la relecture du fichier avec son original.

## Reconstruction locale

`python3 outils/fabriquer-r2.py --film media/T3-Essai-P2-r3-muet.mp4 --sortie /chemin/lot-r2 --ffmpeg ffmpeg --ffprobe ffprobe` depuis le lot. Dépendances : Python 3.11+ avec `markdown-it-py`, FFmpeg/libx264 et ffprobe. `--reference` prend les composants Signature épinglés déjà téléchargés ; les fichiers manquants sont récupérés en lecture seule depuis leur commit avec contrôle de l’identifiant Git du blob. Aucun `git` ni accès à un compte n’est utilisé.

`outils/recette-r2.py` teste le lot et produit les captures (Playwright/Chromium et Pillow). Les rapports sont dans `rapports/`. Vérifier avec `sha256sum -c SHA256SUMS`. Le lien épinglé au commit r1 reste historique et n’est pas un lien vers cette correction.
