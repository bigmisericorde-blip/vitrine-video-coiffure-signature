# T4 · prototype de revue sur mires

**Candidat expérimental de revue : pas un gabarit final, pas de publication de production, pas de déploiement ni validation visuelle.** Il sert à vérifier les raccordements, pas à réaliser des publicités. Ne pas y saisir de données personnelles ni de véritables prises.

## Portée

- La disposition des 12 états est dérivée de T4-P3-R2, validée séparément. Pour ce lot de revue, les aperçus de consignes ont été remplacés par **quatre films de mires fictives**. Ils ne représentent pas le film R2 et ne constituent pas une nouvelle validation de sa mise en scène.
- Les quatre scènes et durées de tournage 6 / 13 / 8 / 7 s, ainsi que la fiche TXT-R1, sont validées séparément. **Les bornes de montage 152/369/206/173 images sont provisoires**, et les effets du prototype ne sont pas fidèles à R2. Le master approuvé est gelé, non inclus et interdit en entrée du moteur ; son empreinte est utilisée pour le refuser.
- L’atelier relie fiche, quatre captures simulées/normalisation, image, musique, voix séparée facultative et sous-titres manuels. Le son d'origine des prises n'est pas utilisé. L'atelier n'est utilisable que localement. Ce n'est pas un service durci et il ne faut pas contourner les validations, notamment par `python -O`.
- Les quatre fonds A–D sont consommés réellement par le module sonore, et ne sont pas dans les clés d'identité. Licences, sources, crédits, adaptations, empreintes et limites Content ID figurent dans `prototype-moteur/audio/catalogue.json` et `preparation-envoi/Controle-audio-candidat-T4.json`. Attribution indispensable ; Content ID non vérifié.
- Les sous-titres sont écrits manuellement, avec début/fin ; ni reconnaissance vocale ni alignement automatique. Il faut relire texte, synchronisation et lisibilité sur vraie voix et images réelles.

## Essai local

Prérequis : Python 3, Pillow avec support des polices variables, FFmpeg/ffprobe ; un navigateur récent. Depuis `prototype-moteur/` :

```sh
python3 atelier_local.py --port 8094
```

Ouvrir `http://127.0.0.1:8094/` sur **la même machine** : ce serveur est volontairement lié à localhost, sans réseau public. Arrêter avec Ctrl+C. Les prises et vidéos de l'atelier sont temporaires et effacées à l'arrêt normal ; une interruption brutale peut laisser des fichiers temporaires dans le système, à supprimer manuellement. Ne pas utiliser la configuration en production.

## Recettes et limites

- `Recette-capture-simulee.json` : 12 états et quatre vidéos réellement capturées avec MediaRecorder, **caméra/micro simulés**, voix synthétique et texte fictif. CSP désactivée dans cette seule recette pour l'instrumentation ; `Recette-csp-refus.json` teste séparément la CSP active, refus caméra et origine étrangère. Pas de garantie de sécurité complète.
- `Recette-quatre-cas-prototype.json` : quatre cas fictifs produit/service sur mires, quatre fonds distincts consommés, une voix synthétique. Ce test de moteur est distinct de celui du parcours 12 écrans.
- `Recette-fiche-prototype.json` et `Recette-sous-titres-prototype.json` : validations techniques locales uniquement. Les fichiers d'exemple et captures ne montrent ni activité ni annonceur réel.
- Pour rejouer les tests Playwright : installer la bibliothèque Python Playwright et disposer de `/usr/bin/chromium`. `python3 test_fiche_t4.py`, `python3 recette_capture.py`, `python3 recette_csp_et_refus.py`. Les scripts écrivent leurs reçus et captures : lancer sur une **copie de travail**. `recette_4_cas.py` et `recette_sous_titres.py` refusent d’écraser leurs sorties déjà présentes ; retirer uniquement les copies des sorties correspondantes avant relance.

**Ouverts :** fidélité des transitions à R2, bornes de montage, vrais cas produit et service, tests sur appareils physiques, voix humaine, sous-titres et synchronisation, architecture et sécurité, canonique T4, version et ZIP de production, qualification et validation finales. Pas de preuve Cloudflare, pas de release ni de fusion. T5 hors périmètre.
