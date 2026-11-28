# COIFFURE‑T2 · intégration du candidat `2.0.3-rc.1`

**Référence onglerie validée :** le film de démonstration intègre une voix synthétique. L’import d’une voix personnelle dans le moteur est facultatif ; la démonstration est un montage distinct. Les guides, le plan et les quatre fonds sont conservés. Les essais sur navigateur utilisent des prises factices ; aucun appareil physique n’a été testé.

**Vérifier les SHA‑256 → lire `manifest.json` → charger `config/template.json` → valider les contrats et prises → rejouer `tools/qa-production.py` → contrôler le fichier téléchargé et mapper les 12 états.** Ce paquet est autonome sur son **profil navigateur**, pas une intégration Android native ou serveur. La présence du paquet ne démontre pas à elle seule un déploiement.

## Démarrage depuis le ZIP

Vérifier le SHA‑256 de l’archive avec le fichier `.sha256` livré à côté. Décompresser dans un dossier neuf. Depuis ce dossier :

```sh
python tools/packager.py verify-dir .
python tools/preview.py --host 127.0.0.1 --port 8092
```

Ouvrir `http://127.0.0.1:8092/` dans Chrome/Edge récent, avec WebCodecs H.264, `OffscreenCanvas`, Web Locks et stockage local. Pas d’ouverture directe en `file://`. Pour un hébergement, utiliser HTTPS et servir toutes les ressources sous le même chemin, sans CDN. Les regex et les URL du moteur sont relatives à son dossier, y compris s’il est placé sous `gabarits/coiffure-t2/`. La seule activité HTTP nécessaire est la lecture des ressources statiques du gabarit. Les liens de réservation et de crédit ne sont pas suivis automatiquement.

## Flux effectivement utilisé

| Couche | Point d’entrée / responsabilités |
|---|---|
| Fiche | `index.html` → `assets/fiche-production.mjs` présente les six questions générales et les consignes de tournage séparément ; les règles éditoriales restent dans `formulaire/questions.json`. `assets/engine/fiche.mjs` protège la fiche dans le stockage de l’onglet et n’inscrit qu’un identifiant opaque dans l’URL. Le numéro fourni et confirmé est transmis au moteur local pour son affichage en fin de MP4 ; l’accord et la destination restent côté interface. Aucune de ces données n’est téléversée par le moteur. |
| Capture | `simulation.html` → `assets/capture.mjs` suit `capture/guide.json`. Minima S1–S4 6/7/7/7 s ; fichier ≤ 40 Mio, portrait, MP4/MOV/WebM selon décodage du navigateur. Refaire ne valide pas d’office une prise. S3 ← S2 signifie relecture explicite du **détail recadré** ; le moteur ne reçoit alors que S1, S2 et S4. |
| Job | `assets/engine/contract.mjs` crée et valide `RenderJob`. Les réponses envoyées au worker sont uniquement celles nécessaires au texte à incruster : le numéro confirmé y est inclus lorsque fourni ; l’URL et la destination restent dans l’interface. Une indication booléenne signale la voix facultative ; les échantillons audio sont transmis au worker séparément et restent dans le navigateur. Cadrage et lettres A–D sont des valeurs de contrat, pas des chemins libres. Les `Blob` sont transmis à côté du job, indexés par slot, pas dans le JSON. |
| Image | `assets/render.worker.mjs` vérifie le plan R04, le montage et les deux polices chargées par empreinte. Le texte est peint sur l’image avant encodage via `assets/texte/modele-visuel.mjs` et `assets/texte/lettrage.mjs`. La base temporelle R04 est conservée. |
| Musique | `assets/engine/rotation.mjs` sérialise les succès sous Web Locks, par origine et catalogue, avec état local. Une erreur n’avance pas le tour ; la relance du même job garde sa piste. La simulation utilise A sans modifier l’historique du commerçant. En cas de fermeture brutale, la réservation bloquante peut être reprise/abandonnée dans l’onglet ; sinon elle expire après 15 min. Les 128 derniers succès sont mémorisés. Pas de synchronisation entre appareils. |
| Fichier | Sans voix, le worker copie en l’état les paquets AAC‑LC du fond vérifié. Avec voix importée, la voix est mixée localement avec ce fond puis le mix est encodé AAC‑LC (48 kHz stéréo). La vidéo reste H.264 **720 × 1280/30 i/s, 900 images/30 s**. Aucun son original des prises ni sous-titrage automatique. Il transmet un `RenderResult` validé et les octets du MP4 ou un `RenderError`. Lecture et téléchargement partagent la même URL `blob:`. |

`config/template.json` est lu par le runtime ; ses clés `template_id = COIFFURE-T2`, `version = 2.0.3-rc.1` et `audio_profile = coiffure-en-etapes` n’écrasent aucun alias T1. Le dossier contient les quatre schémas JSON Schema 2020‑12 et des exemples de job à 3/4 prises, de résultat et d’erreur dans `fixtures/contracts/`. `resultat-exemple.json` illustre le format, ce n’est pas le manifeste d’un MP4 téléchargeable. `INVALID_JOB` et `PLATFORM` demandent une correction plutôt qu’une nouvelle relance identique ; `AUDIO_INVALID` n’est jamais dégradé silencieusement en vidéo muette. Les erreurs n’effacent pas les prises déjà validées.

## Recette reproductible

```sh
# Test rapide : Node 20 ; aucun paquet npm ni accès réseau requis.
node tools/test-production.mjs

# Installation des outils de QA uniquement si absents (pas nécessaire au runtime).
python -m pip install -r tools/qa-requirements.txt
python -m playwright install chromium
python tools/verify-contracts.py
# Avec ffmpeg et ffprobe dans le PATH (ou variables FFMPEG/FFPROBE) :
python tools/qa-production.py --out /tmp/coiffure-t2-recette
```

Le navigateur du test bloque les requêtes hors origine et vérifie que le téléchargement est le même fichier que le lecteur. Il sonde le MP4 et ses horodatages, décode l’ensemble, compare le flux AAC au fond du catalogue et compare des pixels du lettrage aux calques attendus. Il essaie deux fiches, 3 et 4 imports, une mire, le refus d’une prise courte, une erreur de musique suivie d’une relance, et deux onglets avec stockage commun. La caméra est simulée. `conformance/` fournit les contrôles et 12 captures sur mires, sans image tierce ni données de client.

La recette vérifie les caractéristiques et le contenu, **pas l’identité octet pour octet de deux encodages depuis des versions ou accélérations matérielles différentes**. Le master muet R04 approuvé est un étalon de revue local, pas un composant du runtime. Aucune modification de ce master. Ne pas tester par substitution d’un MP4 préexistant au résultat dynamique.

## Passage au dépôt / limites

Comparer d’abord les conventions du moteur cible à ce contrat ; aucune compatibilité binaire ou API commune n’est présumée. N’ajouter que le dossier de ce gabarit, depuis la bonne branche de base et avec autorisation. Ne pas pousser l’historique de la revue locale. L’APK, l’iPhone/Safari, les appareils physiques, un profil Android/serveur, l’intégration au catalogue central et la CI distante restent à qualifier. **Pas de déploiement OTA.** Le ZIP contient des mires originales pour être autonome ; les rushs de coiffure de la revue et leurs dérivés restent en local tant que leurs droits pour l’usage prévu ne sont pas documentés. La référence onglerie validée et l’encodeur facultatif sont inclus ; aucun autre gabarit n’entre dans le paquet.


## Deux finitions selon la prestation
Sur décision du propriétaire : `manucure` utilise les cadrages, transitions et l’habillage de la variante Onglerie `99003f2529839e6be3182b85a440cadeae363c82`. Les autres prestations gardent le rendu général R04. Les fonctions de recadrage, les cassures, le moteur de composition Onglerie et son habillage sont inclus séparément ; le plan source et les fonds ne sont pas modifiés. Le contexte métier accompagne l’appel au worker ; un appel direct qui l’omet prend la base générale historique. Le parcours de test utilise toujours des mires. Le film onglerie validé est fourni séparément à titre d’illustration, et ses images sont utilisées pour les 12 aperçus onglerie ; consulter ses crédits et droits. Le client peut importer sa propre voix ou ne pas en ajouter ; la transcription automatique n’est pas disponible. Une recette sur appareil physique reste à effectuer.

**Révision des six questions :** la recette de `conformance/Recette-six-questions.json` a été rejouée sur mires ; les autres preuves sous `conformance/` sont historiques et ne constituent pas une validation de cette révision. Le parcours avec voix facultative et l’essai illustratif ont été vérifiés séparément. Aucun appareil physique testé.

## Contrat des questions et des prises — six questions

Les six questions générales, leurs obligations et leurs destinations sont dans `formulaire/questions.json`. Le nom et le service sont obligatoires ; outil, ville, contact et prix sont facultatifs. La réponse sur ce qui est utilisé accompagne la consigne S2 et est transmise au moteur vidéo pour affichage. Les champs internes conservés pour compatibilité ne sont pas des questions supplémentaires. `capture/guide.json` définit les quatre prises, les consignes, le contexte de prestation et les douze états ; le profil beauté ajoute des exemples métier. La fiche, les consignes, la galerie et les transitions après relecture utilisent ces JSON. Le worker charge le même contrat et utilise les destinations des six champs commerciaux pour produire les textes. Le plan `ingenierie/plan.json` reste la source de vérité des coupes et du minutage et est vérifié par empreinte. Les schémas `schemas/questions.schema.json` et `schemas/guide.schema.json` documentent les deux structures. Ce contrat Web est inspiré de la structure questions/scènes du partenaire, sans prétendre implémenter son moteur Android.

Les essais ci-dessus ont été refaits en navigateur sur mires, y compris trois et quatre imports, voix facultative et les douze états ; pas de test sur caméra physique. Les preuves historiques sous `conformance/` demeurent historiques.
