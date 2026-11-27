# T2 · Signature coiffure

**Quatre prises avant/après · douze écrans · un vrai MP4 de 30 s avec la fiche incrustée.**

[Remplir ta fiche](index.html) · [Ouvrir les 12 écrans](ecrans.html) · [Exemple avec musique](film.html?test=VV-COIF-01) · [Master muet](media/04-vitrine-video-signature-muette.mp4) · [Rapport de recette T2](livrables/08-recette-t2.md)

## Film final narré — Studio Vitrine

**T1 beauté :** cinq questions commerciales : nom, prestation, ville, contact et prix. Ville, contact et prix sont facultatifs. Avant, geste, détail et résultat sont des consignes de tournage, pas des questions. Le montage d’exemple validé montre un geste en cours et des finitions : il ne prouve pas un avant coupe. Pour un vrai avant/après, filmer la même personne ou zone avant et après. L’ancien film reste conservé.

[**Regarder et télécharger le film sur GitHub Pages**](https://bigmisericorde-blip.github.io/vitrine-video-coiffure-signature/final.html) · [MP4 de progression validé](media/t1-coiffure-progression-validee.mp4) · [Contrôle des textes, rushs et voix](livrables/09-film-final-t2.md)

Ce MP4 de 30 s, réalisé avec les quatre rushs d’exemple du T2, incruste **Studio Vitrine · Cotonou · Coupe + barbe · 1 500 FCFA** et l’action finale. Les cinq prises de voix française déjà préparées sont mixées sur *Harbor Lanterns*. Il est pré-rendu : le lecteur public ne dépend pas de l’atelier de voix.

## Essayer ou préparer un spot commercial

1. Saisir le nom du salon, le lieu, la prestation, le tarif éventuel, le résultat à montrer et l’action finale. N’indiquer qu’un contact à publier. **Relire la fiche dans les 12 écrans** ouvre des aperçus liés à cette fiche, sans validation.
2. Choisir **les quatre prises d’exemple** pour essayer ou **mes quatre prises** pour préparer une publicité. Importer les vidéos une par une ; le téléphone peut ouvrir sa caméra pour fournir un fichier. Filmer la même personne avant et après. Les fichiers de prise restent en mémoire dans le parcours : ne pas le recharger avant l’export.
3. À chaque prise : **consigne → chrono → relecture → validation**. Les prises et les exemples restent muets ; le chrono suit la lecture. Une vidéo trop courte ou illisible n’est pas validée.
4. Après la quatrième validation, le navigateur **encode** le MP4. Le nom ivoire calligraphié, la prestation en sérif, le prix s’il est saisi, le lieu, le résultat et le CTA sont peints dans l’image. Le texte se découvre progressivement. Le CTA final reste fixe pendant 3,60 s, avec l’image encore en mouvement au-dessus. Un contact web ou téléphonique valide devient aussi un lien **dans le lecteur**, pas dans le MP4.
5. **Voir ma publicité**, **Revoir** et **Télécharger le MP4** utilisent exactement le même fichier. Le bouton **Ajouter ma voix ou mon texte** ouvre le remix optionnel si le serveur de voix est en ligne.

| Prise | Durée minimum | À montrer | Dans le spot |
| :--- | :---: | :--- | :---: |
| S1 | 6 s | Le profil avant la prestation ; dans l’exemple, le pro et le client | 0–5 s |
| S2 | 7 s | Le geste de coiffure | 5–11 s |
| S3 | 7 s | Un détail de finition | 11–15,80 s |
| S4 | 7 s | Le résultat et le profil final | 15,80–30 s |

MP4/MOV/WebM, 24 Mo par prise, HD à Full HD, 240 px minimum par dimension. La compatibilité des fichiers dépend des codecs installés. L’exemple est un **test fictif** (`VV-COIF-01`) : les personnes filmées ne recommandent aucune offre. Aucune réservation ni aucun paiement n’est envoyé par l’application.

## Parcours et rendu

Le flux T2 est `cas-test.json` + fiche locale → quatre prises, trois états chacune → `ingenierie/plan.json` → encodage dans un worker → MP4. La fiche est gardée dans l’onglet, au plus 24 h, avec un identifiant aléatoire sans données personnelles dans l’URL. Les prises, la fiche et le MP4 ne sont pas envoyés pour le montage local. Si tu demandes un remix voix, seuls le MP4 et les entrées audio/texte nécessaires sont envoyés au serveur de montage.

Le plan canonique donne l’identité du secteur (`T2`), la version du **gabarit** (`1.0.0`) et le profil `coiffure-afrobeat-amapiano`. La bibliothèque des quatre fonds v1.2, leurs mesures et leurs droits sont séparés. Aucun code OTA ni Cloudflare n’a été ajouté.

Les douze plans du film utilisent les quatre sources existantes : recadrages, split, deux iris verts, raccord diagonal et rail final. La galerie sans fiche conserve les [douze captures d’exemple](livrables/12-ecrans.md) ; avec une fiche active, elle ouvre les douze véritables états avec les réponses de cet onglet. L’exemple fixe `film.html` est séparé du parcours qui fabrique le MP4.

### Hébergement statique

```bash
python ingenierie/serve.py --port 8080
```

Ouvrir `http://localhost:8080/` ou héberger le dossier en **HTTPS**. Ne pas ouvrir la fiche en `file://` pour encoder ; ne pas servir la racine de l’espace de travail. Le navigateur doit prendre en charge `VideoEncoder`/`VideoDecoder`, H.264 et le canevas hors écran. Chrome/Chromium a été testé ; la disponibilité de l’encodeur dépend du navigateur et de l’appareil. Un fichier manquant, un encodeur incompatible ou un échec de montage est signalé sans proposer la démo comme faux export personnalisé.

### Musique

Les quatre fonds retenus restent dans l’ordre **Afrobeat (Alex Morgan), Afro House (Alex Morgan), Hot Amapiano Beats (Alex Morgan), Amapiano (Elijah_K)**. Le moteur vérifie le fichier sélectionné et recopie son AAC, sans changer sa durée, son tempo ni son gain. Les nouveaux montages réussis ne reprennent pas le dernier fond ; relire ou télécharger ne tire rien. Un échec n’enregistre pas de tirage. `film.html?muet=1` lit le master historique ; `simulation.html?test=VV-COIF-01&muet=1` génère le montage dynamique sans son pour l’exemple. Si le son n’est pas disponible, le parcours permet de **réessayer sans musique** sans abandonner la fiche ni les prises.

[Licences, mesures et crédits](livrables/07-bandes-son-afrobeat.md) · [Crédits](CREDITS.md). La piste 1 conserve son départ original ; Afro House et Hot Amapiano Beats conservent leur tempo natif. Aucun des quatre essais de voix ne fait partie du catalogue. Pour reconstruire les rendus intégrés de l’exemple, utiliser les originaux licenciés hors dépôt :

```bash
python ingenierie/mixage.py --sources /dossier/prive --demo .
```

## Atelier voix et musique

Depuis le résultat T2, **Ajouter ma voix ou mon texte** reprend les images du MP4 et le fond déjà choisi : aucune nouvelle musique n’est tirée pour le remix. Depuis `atelier.html` directement, on peut aussi utiliser l’exemple ou importer un **montage déjà assemblé** (MP4, MOV ou WebM, 3–30 s).

| Mode | Ce que fait le moteur |
| :--- | :--- |
| Je parle | Micro, fichier voix ou piste de la vidéo importée. Le moteur traite le signal sans imposer de langue ni transcrire : fon, yoruba, français, anglais ou autre. La voix déjà dans la vidéo reste synchronisée. |
| J’écris | Le texte saisi est synthétisé localement en français ou en anglais si les modèles sont installés. Pour une autre langue, le texte reste accessible comme prompteur pour enregistrer ta voix. Le texte n’est jamais remplacé par celui des essais. |
| Sans voix | Musique seule ou export entièrement muet, au choix. |

Le mixage nettoie les graves inutiles, normalise la voix et repère les intervalles parlés. Le fond baisse d’environ **13 dB** sur ces intervalles, avec un retour progressif (environ 285 ms). La narration ne change ni de vitesse ni de langue. Une narration trop longue est refusée au lieu d’être coupée ou accélérée. Les quatre fonds tournent par cycle par atelier ; le dernier est exclu du nouveau tirage, même en début de cycle. Le choix n’est enregistré qu’après un rendu réussi et l’aperçu et l’export servent les mêmes octets. Les images du gabarit et du MP4 T2 lié sont copiées sans réencodage ; un montage externe importé dans l’atelier est mis au format vertical.

```bash
# Depuis le dossier du projet, dans un environnement Python isolé.
pip install -r requirements-atelier.txt
python ingenierie/voix_texte.py --installer fr en   # facultatif pour voix parlée
python ingenierie/serve_atelier.py --port 8080
# La racine ouvre la fiche ; /atelier.html ouvre l’atelier directement.

# Le même moteur sans navigateur : texte, audio ou piste de sa propre vidéo.
python ingenierie/postproduction.py --texte mon-texte.txt --langue fr --output mon-spot.mp4
python ingenierie/postproduction.py --video montage.mp4 --garder-son-video --output mon-spot.mp4
```

Les modèles et fichiers du client ne sont pas dans le dossier public. `VV_TTS_MODELS` change le dossier des modèles ; `VV_WORK_DIR` doit viser un dossier privé, accessible en écriture, idéalement persistant pour retenir la rotation. Les entrées client sont effacées après traitement. Le lien d’export est temporaire (45 min), non listé : télécharger pour conserver le film. Le micro demande l’accord de la personne et un contexte HTTPS ou localhost. Le texte et la voix ne sont pas envoyés à un fournisseur de synthèse.

**Déploiement** : le rendu T2 silencieux ou musical fonctionne sur un hébergement statique avec un navigateur compatible ; l’atelier voix demande `serve_atelier.py` derrière un hébergement HTTPS. Un push sur GitHub Pages ne déploie pas ce serveur. L’aperçu de l’atelier n’est pas une mise en ligne de production. Pour une ouverture publique, prévoir l’authentification, les quotas et la supervision du service. Voir [recette de l’atelier](ingenierie/recette-atelier.json).

## Reconstruire et vérifier

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
# FFmpeg et ffprobe doivent être disponibles ; FFMPEG peut remplacer le chemin de FFmpeg.
python ingenierie/build_ecrans.py                 # sans toucher aux clips, ni au T1
python ingenierie/qa.py
python -m pytest -q ingenierie
python ingenierie/build_manifest_t2.py --check
python ingenierie/qa_ui.py --local
python ingenierie/qa_audio_web.py --local
python ingenierie/qa_film_final.py --local          # film narré : fichier, lecteur, sous-titres, téléchargement
python ingenierie/qa_t2.py --importer --output /dossier/prive/recette
# Avec serve_atelier.py et le modèle FR installés :
python ingenierie/qa_t2.py --url http://localhost:8080 --voix --output /dossier/prive/recette
```

`rendu.py` reste le moteur du master muet témoin et lit le **même plan**. Utiliser `--output /dossier/prive/master.mp4` pour ne pas écraser le master publié lors d’un essai. `build_prises.py --ui-only` recompile les textes du cas. `build_ecrans.py` assemble le HTML T2 local ; en option, il vérifie l’empreinte de [`simulation/index.html` épinglé dans le T1](https://github.com/j9028379-hue/vitrine-video-t1-pilot/blob/ad4ff15a76dcba7bd08b7e8f56052e842b3e794f/simulation/index.html) si on lui passe ce fichier. Aucun rendu ni texte restaurant n’a été repris dans T2.

Sur GitHub Pages, déployer `main` et `/(root)` et contrôler les URL servies et un parcours dans un navigateur compatible. Dépôt public, Pages et serveur voix sont trois niveaux distincts. L’atelier est un banc de montage ; avant de l’ouvrir en production, prévoir une authentification, des quotas et la supervision des exports temporaires.

## Livrables

- [Rapport 360°](livrables/01-rapport-analyse-360.pdf) et [tableur des références, fusion et coupes](livrables/01-analyses-et-plans.xlsx) : 188 relevés d’image et de son sur les quatre films, comparaisons, rejets, points d’entrée et de sortie.
- [Architecture du 30 s](livrables/03-architecture-signature.pdf) et [déroulé à la seconde](livrables/03-architecture-30-secondes.csv), dont intentions sonores à valider **après** la revue muette.
- [Règles de gabarit et recette](livrables/05-regles-application-et-recette.pdf), [aperçu des 12 écrans à jour](ecrans.html), [captures de la première recette](livrables/05-preuves-test-ecrans.pdf), [grille des variantes H/F](livrables/05-adaptation-h-f.md).
- [Cas test](ingenierie/cas-test.json), [plan image](ingenierie/plan.json), [sources des quatre extraits](ingenierie/manifest-rushs.json), [contrôle du master](ingenierie/recette-video.json) et [recette navigateur](ingenierie/recette-parcours.json).

## Médias et provenance

Les quatre extraits d’exemple sont de **Pavel Danilyuk / Pexels**. Voir les [crédits et droits](CREDITS.md). La référence typographique jointe a servi à choisir le style du nom et du sous-titre ; son image, son texte et ses pistes ne sont pas distribués dans le gabarit.
