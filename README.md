# Le passage vert · Vitrine Vidéo

**Test `VV-COIF-01` · 4 prises · spot vertical de 30,00 s · aucune piste audio.**

[▶ MP4 muet](media/04-vitrine-video-signature-muette.mp4) · [Voir le film avec son bouton de test](film.html?test=VV-COIF-01) · [Remplir ta fiche](index.html) · [Ouvrir les 12 écrans](ecrans.html)

Studio Vitrine, Coupe + barbe, 7 500 FCFA, Cotonou. Le salon, le tarif et les créneaux sont fictifs. Aucun paiement, aucune demande de caméra, aucun envoi vers une réservation réelle. Le bouton du lecteur web n’est pas un lien incorporé au MP4.

## Parcours à essayer

1. Ouvrir `index.html`, changer les réponses ou garder le cas prérempli, puis lancer le test **VV-COIF-01**. Les réponses restent dans l’onglet et donnent les repères à montrer, mais ne régénèrent pas le film.
2. Pour chacune des quatre scènes, lire la consigne, appuyer sur **Commencer à filmer**, attendre la fin du chrono et revoir la prise avec une courte question de contrôle. **Refaire** recommence la scène ; **Scène suivante** la valide.
3. À la quatrième validation, **Voir mon montage** prépare la lecture du rendu déjà calculé. **Voir ma publicité** lance le master muet. À la fin du film, **Recommencer** remet les validations à zéro.
4. **Réserver coupe + barbe** affiche la prestation et propose le choix d’un horaire fictif. Ce bouton est disponible aussi sur l’écran de fin.

| Scène client | Prise jouée | Ce qu’elle montre | Fenêtre dans le spot |
| :--- | :---: | :--- | :---: |
| S1 — Le pro et le profil | 6 s | Fauteuil, professionnel et client | 0–5 s |
| S2 — Le geste de coupe | 7 s | Tondeuse et tempe | 5–11 s |
| S3 — Le détail de finition | 7 s | Trajet de l’outil sur la barbe | 11–15,80 s |
| S4 — Le résultat | 7 s | Finition, profil, support du CTA | 15,80–30 s |

Les douze plans rendus sont des fenêtres dans les **quatre mêmes** sources, des recadrages et du graphisme. Le mouvement du téléphone et le rail CTA ne demandent pas de nouvelle capture. Le badge prix reste ancré de la preuve à l’action ; deux iris verts ponctuent les bascules et le prix/CTA final reste immobile 3,60 s, avec le profil toujours animé au-dessus.

## Voir les 12 écrans directement

`ecrans.html` ouvre, au choix, Consigne / Enregistrement / Après lecture pour chacune des quatre prises. La fiche et les consignes ne séparent pas homme et femme. L’aperçu ne valide pas les prises : pour suivre le parcours, démarrer par `index.html`. On peut aussi [voir les 12 captures sur GitHub](livrables/12-ecrans.md).

## Livrables

- [Rapport 360°](livrables/01-rapport-analyse-360.pdf) et [tableur des références, fusion et coupes](livrables/01-analyses-et-plans.xlsx) : 188 relevés d’image et de son sur les quatre films, comparaisons, rejets, points d’entrée et de sortie.
- [Architecture du 30 s](livrables/03-architecture-signature.pdf) et [déroulé à la seconde](livrables/03-architecture-30-secondes.csv), dont intentions sonores à valider **après** la revue muette.
- [Règles de gabarit et recette](livrables/05-regles-application-et-recette.pdf), [aperçu des 12 écrans à jour](ecrans.html), [captures de la première recette](livrables/05-preuves-test-ecrans.pdf), [grille des variantes H/F](livrables/05-adaptation-h-f.md).
- [Cas test](ingenierie/cas-test.json), [plan image](ingenierie/plan.json), [sources des quatre extraits](ingenierie/manifest-rushs.json), [contrôle du master](ingenierie/recette-video.json) et [recette navigateur](ingenierie/recette-parcours.json).

## Lire la démo sans compilation

Depuis le dossier extrait, `python ingenierie/serve.py --port 8080`, puis ouvrir `http://localhost:8080/` (ou ouvrir directement `index.html` après extraction ; selon le navigateur, servir les fichiers localement peut être nécessaire). La version statique peut aussi vivre à la racine d’un dossier GitHub Pages. Toutes les URL internes sont relatives. Ne pas lancer ce serveur à la racine de l’espace de travail complet.

## Reconstruire ou adapter le gabarit

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
# Optionnel : FFMPEG=/chemin/vers/ffmpeg ; les sources Pexels sont vérifiées par SHA-256.
python ingenierie/build_prises.py
python ingenierie/rendu.py
python ingenierie/qa.py
python -m pytest -q ingenierie/test_contrat.py
# Serveur local démarré dans un autre terminal pour la recette complète :
playwright install chromium
python ingenierie/qa_ui.py  # --captures dossier/ au besoin
```

`build_prises.py --ui-only` recompile les textes de test sans toucher aux rushs. Les fichiers fournis sont prêts à lire : la reconstruction est facultative. `rendu.py` lit les points de montage, types et longueurs de transitions, zooms et ancrages dans `plan.json`. Adapter les paramètres dans leurs bornes, pas les images de sortie à la main. Un encodage avec d’autres versions de FFmpeg/FreeType peut donner une autre empreinte : comparer aussi horloge, décodage, transitions et lisibilité.

Les composants A/B/C et leur ordre viennent de [`simulation/index.html` au commit `ad4ff15`](https://github.com/j9028379-hue/vitrine-video-t1-pilot/blob/ad4ff15a76dcba7bd08b7e8f56052e842b3e794f/simulation/index.html). `build_ecrans.py /chemin/vers/simulation/index.html` reconstruit la variante coiffure depuis cette révision, sans écrire dans le T1. Le gabarit restaurant n’est pas modifié. Les écrans du pilote sont une **simulation web** ; ils ne testent pas la caméra, l’encodeur ou la génération native Android.

## Mise en ligne du test

Publier **ce dossier** dans un dépôt public distinct, puis dans *Settings → Pages → Deploy from a branch*, sélectionner `main` et `/(root)`. Vérifier hors session le dépôt, la page d’entrée, les cinq MP4, les quatre validations et le CTA. Une prévisualisation Arena, un dossier local ou un dépôt sans site publié ne constitue pas une URL publique du test.

## Médias et provenance

Quatre vidéos de **Pavel Danilyuk / Pexels**, des extraits recadrés et intégrés à cette maquette. Voir [crédits et droits](CREDITS.md). Aucun extrait, logo, enregistrement vocal, titre musical ou visage des films publicitaires audités n’a été importé. L’analyse des références ne mesure pas des ventes.
