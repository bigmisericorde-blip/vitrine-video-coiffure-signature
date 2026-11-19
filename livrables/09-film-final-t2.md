# Film final T2 · Studio Vitrine

[**Lire avec le son sur GitHub Pages**](https://bigmisericorde-blip.github.io/vitrine-video-coiffure-signature/final.html) · [MP4 dans le dépôt](../media/t2-signature-coiffure-narree.mp4) · [Recette et empreintes](t2-final/recette-film.json) · [Sous-titres FR](../media/t2-signature-voix.vtt)

Le lecteur et le bouton de téléchargement utilisent le **même MP4**. L’affichage de la fiche fait partie de l’image ; la voix et la musique font partie de la piste audio. La lecture n’appelle ni le moteur de montage ni le serveur de voix.

## Vérifier la fiche dans l’image

| Repère dans le film | Ce que l’on doit voir |
| :--- | :--- |
| [0,07 s](t2-final/00-avant.webp) → [0,48 s](t2-final/01-revelation.webp) | Le rush d’abord, puis la révélation du nom. |
| [1,24 s](t2-final/02-accroche.webp) | **Studio Vitrine** en Pinyon Script ivoire (`#fff5df`, avec dégradé), **Coupe + barbe** en DM Serif Display, **Cotonou**. |
| [3,42 s](t2-final/03-offre.webp) | **Coupe + barbe · 1 500 FCFA · Cotonou**. |
| [17,55 s](t2-final/04-resultat.webp) | **Contours nets, profil soigné.** Telle est la réponse saisie pour le résultat. |
| [27,56 s](t2-final/05-carton.webp) | Le profil après, le salon, la prestation, le lieu, le tarif et **Prendre rendez-vous / Réservation en ligne**. Le carton est lisible de 26,40 à 30,00 s. |

Les six photogrammes ont été extraits du fichier de livraison. Les [polices locales](../assets/fonts-t2/) sont les mêmes que celles du moteur T2. Le spot présente un cas fictif, sans adresse précise, numéro de téléphone ni lien de réservation réel.

## Les quatre rushs et les douze écrans

| Prise du montage | Rush utilisé | Fenêtre dans le film |
| :--- | :--- | :--- |
| S1 · Avant | [S1.mp4 · 6 s](../media/S1.mp4) | 0–5 s |
| S2 · Geste | [S2.mp4 · 7 s](../media/S2.mp4) | 5–11 s |
| S3 · Détail | [S3.mp4 · 7 s](../media/S3.mp4) | 11–15,80 s |
| S4 · Après | [S4.mp4 · 7 s](../media/S4.mp4) | 15,80–30 s |

La fiche a été saisie puis les quatre prises validées sur le T2 public avant export. [Le plan canonique](../ingenierie/plan.json) (`T2@1.0.0`) monte douze **plans** ; distincts de ces plans, les [douze **écrans** du parcours](12-ecrans.md) contrôlent les trois états de chacune des quatre prises. La [recette du gabarit](08-recette-t2.md) vérifie les états liés à la fiche et l’import de prises client. Le film narré ne remplace ni ce gabarit, ni le master muet, ni la rotation des musiques. Le dépôt T1 n’est pas modifié.

## Écouter et suivre la voix

| Début–fin | Voix de référence |
| :--- | :--- |
| 0,61–4,53 s · Accroche | Votre charme est naturel. Faites-en votre signature. |
| 5,28–7,89 s · Geste | Une coupe précise, une barbe dessinée. |
| 10,73–15,51 s · Offre | Chez Studio Vitrine, coupe et barbe, le tout à mille cinq cents francs CFA. |
| 16,27–20,82 s · Miroir | Face au miroir, comme une impression d’avoir rajeuni de plus de dix ans. |
| 24,64–28,68 s · Invitation | Venez découvrir la différence. Réservez votre créneau en ligne. |

La phrase d’offre commence juste avant le raccord vers le détail ; la réservation est dite pendant l’arrivée du carton final. Les prises FR préparées pour Studio Vitrine ont été calées sans accélération. Le fond amapiano **Harbor Lanterns — FreeVibeVault** part du début de la piste, tempo inchangé. Il est atténué sous la voix jusqu’à 13 dB. Mesure du MP4 livré : **−16,93 LUFS-I**, **−4,91 dBTP**. La reconnaissance vocale sur le mix confirme notamment le montant, la prestation et l’invitation ; le résultat automatique n’est pas une transcription mot à mot. La piste de sous-titres utilise le texte des prises.

## Intégrité et crédits

- **MP4 :** 30,000 s, 720 × 1280, 30 i/s, 900 images, H.264 + AAC-LC 48 kHz stéréo ; 14 599 394 octets. AVC copié depuis l’export navigateur : aucun réencodage d’image lors du mixage.
- **SHA-256 du MP4 :** `73f2d47496a26c6016e241925d749e75d55cab14835157a24a641cf430bc4725`. Après téléchargement, comparer avec `sha256sum t2-signature-coiffure-narree.mp4` ou `Get-FileHash t2-signature-coiffure-narree.mp4 -Algorithm SHA256`. Le [manifeste de livraison](../ingenierie/manifest-t2.json) et [`qa_film_final.py`](../ingenierie/qa_film_final.py) permettent de vérifier le fichier, le lecteur et le téléchargement.
- **Sources :** rushs recadrés de Pavel Danilyuk / Pexels ; voix synthétique FR déjà préparée, pas de génération Piper. [Harbor Lanterns](https://freevibevault.com/track/ghj3du94kp45fclg9a9ofcqb) — FreeVibeVault, sous [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), extrait avec égalisation, fondus et mixage avec la voix. [Détail des crédits](../CREDITS.md).
