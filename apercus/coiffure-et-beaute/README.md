# Coiffure et beauté — candidat local 0.1 · T1 et T2

**État : version d’essai déposée dans Signature, sur la branche `feat/coiffure-et-beaute-t1-t2`. Ce n’est pas une nouvelle certification.** [Guide pour essayer](Commencer-ici.md).

## Voir les 12 écrans

Depuis l’aperçu du dossier `site/`, ouvre « Exemples filmés », puis T1 ou T2 pour Manucure ou Soin du visage. Chaque galerie montre quatre consignes, quatre chronos et quatre relectures, puis le MP4 terminé. Les galeries et les films se lisent sur un hébergement statique ; l’atelier voix T1 demande le serveur Python ci-dessous.

## Servir le site

Le dossier `site/` contient l’entrée commune et les deux applications. Avec Python 3.11+ :

```sh
python3 servir.py --port 8112
```

Ouvrir `http://127.0.0.1:8112/` dans Chrome ou Edge récent, pas en `file://`. Sur un hébergement d’essai, servir en HTTPS ; dans Arena le serveur écoute sur `0.0.0.0` et les pages, workers, médias et API ont des adresses relatives. Les exports vidéo ordinaires se font dans le navigateur. Le site ne demande ni compte ni envoi des rushs à une API. Les liens des crédits sont facultatifs.

T1 conserve un **atelier voix facultatif**, ouvert après un montage personnel. Seul le clic sur le bouton de mixage envoie le MP4 et, selon le choix, la voix au serveur. L’atelier requiert `ffmpeg` dans le PATH ou la variable `FFMPEG`. `--work` permet de choisir son dossier temporaire, hors du site. Aucun modèle de lecture automatique de texte n’est installé dans l’aperçu actuel ; le micro ou l’import d’une voix restent les entrées prévues. T2 conserve son fonctionnement local, avec musique seule dans l’export.

## Structure et garanties

| Élément | Version d’essai |
|---|---|
| `site/commun/metiers.js` | Les mêmes huit choix, exemples de réponses et consignes dans les deux ateliers. « Autre prestation » laisse le nom libre. Le métier aide à filmer, il ne bloque pas les mots de la fiche. |
| `site/commun/exemples.js` | Bibliothèque séparée du moteur : une séance par exemple. Sans exemple filmé pour un métier, l’interface l’indique et laisse accès aux propres prises et aux consignes. Aucun renvoi automatique sur des mires ou sur la coiffure. |
| `site/t1/` | Copie du parcours historique du dépôt Signature (`main`, `45048956…`, appelé T2 dans ses fichiers d’origine). Quatre slots distincts ; nom, lieu et prestation ; tarif/contact facultatifs. Plans d’origine conservés. Les fonds ne sont plus emballés avec quatre copies du film : mêmes échantillons AAC dans des conteneurs audio seuls, vérifiés. |
| `site/t2/` | Dérivé de l’extraction certifiée `2.0.0-rc.1`. Révision distincte `2.1.0-rc.1` / `beaute-fr-01`, même identifiant technique `COIFFURE-T2` et mêmes schémas. Fiche, habillage et capture adaptés ; 24 h de stockage de fiche dans l’onglet. Les coordonnées confirmées restent hors du MP4. |
| `site/commun/montage.mjs` | Cadrages centrés, zooms plus doux, même ordre, mêmes durées et mêmes fenêtres de prises. T1 montre la prise verticale entière dans les cartons larges. T2 conserve ses cadres et ses sept impacts, atténués pour garder les zones utiles dans l’image. Le détail recadré réemploie le plan adapté à la relecture et à l’export. |
| `site/exemples/` | Les deux films Coiffure d’origine, sans réencodage. Deux nouvelles séries filmées, chacune avec quatre extraits et ses propres films T1 et T2. Les crédits sont dans `site/CREDITS.html`; les sources et empreintes des nouveaux extraits, dans `recette/Provenance-des-prises.json`. Exemples préparés localement : aucune recommandation par les personnes filmées. |

La galerie T2 coiffure conserve le **film de démonstration avec cassures** publié en `1bede945…`. Cette finition de galerie n’est pas devenue le moteur universel ; le candidat dérive le plan livré, pas le script de retouche de la galerie.

## Recette exécutée

- **16 chemins de fiche** : huit métiers dans chaque atelier, de l’accueil à la première consigne. Les textes d’exemple et les champs obligatoires sont vérifiés ; les fiches utilisent un ticket dans l’URL, sans données personnelles dans la requête.
- **6 galeries filmées**, soit **72 écrans** et **48 lectures de prises** sur les écrans Chrono/Relecture, et lecture des six films. Pour un profil sans film, contrôle que la galerie annonce l’absence d’exemple et ne montre pas d’autre prestation.
- **4 films d’exemple** générés par les interfaces, manucure et soin du visage en T1 et T2, plus **2 exports sur import des vraies prises** : 4 fichiers en T1 et 3 en T2. Dans T2, refus d’un aperçu S3, retour à la consigne, nouvelle relecture puis validation du détail recadré.
- MP4 H.264 vertical 720 × 1280, 900 images à 30 i/s, 30 secondes ; fichiers entièrement décodés, paquets AAC identiques au fond sélectionné, même blob au lecteur et au téléchargement. Relecture visuelle des moments-clés dans les quatre films : ongle, outil, texture et résultat visibles, texte à distance des détails à montrer sur ces cas.
- **96 plans de lettrage T2** validés (8 profils × 3 exemples de prestation × 4 fonds). Tests dans Chromium, largeur 390 px ; contrôles de débordement supplémentaires à 320/360 px.
- **Caméra virtuelle T2** alimentée par une vraie prise de manucure : annulation, nouvelle prise, chrono, relecture et passage à la prise suivante. La caméra est libérée dans les deux cas. Ce test ne remplace pas un essai sur téléphone.
- **Atelier voix T1** : téléchargement après mixage *sans narration* et restitution de la piste image sans modification vérifiés. Le micro et le mixage avec une voix n’ont pas été qualifiés.

Cette recette ne couvre pas Safari ni un téléphone physique, et ne prétend pas garantir tous les cadrages possibles. Il manque encore des exemples filmés distincts pour pédicure, soin du corps, maquillage, cils/sourcils et autres prestations. Aucun film multiactivité d’accueil dans ce lot.

Pour rejouer les contrôles : après démarrage du serveur, Python avec `playwright` et Chromium installés, FFmpeg et FFprobe dans le PATH (ou variables `FFMPEG` et `FFPROBE`). `--phase films` régénère les films d’exemple ; `--phase imports` écrit les rendus de test dans `--work` ; `--phase galerie` vérifie la navigation et les lectures sur les films déjà fournis. Ne pas exécuter les scripts de régénération dans le lot Coiffure certifié.

```sh
python3 outils/recette.py --phase galerie --work /tmp/vv-beaute
```
