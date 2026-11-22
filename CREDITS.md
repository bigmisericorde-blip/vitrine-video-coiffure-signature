# Crédits et périmètre

Les rushs et films d’exemple illustrent un test fictif, pas un établissement réel. Aucune recommandation des personnes filmées n’est alléguée.

| Prise | Original | Auteur | Utilisation |
| :--- | :--- | :--- | :--- |
| S1 | [4177803](https://www.pexels.com/video/a-man-styling-a-man-s-hair-4177803/) | Pavel Danilyuk / Pexels | Recadrage vertical, professionnel et profil |
| S2 | [4177957](https://www.pexels.com/video/beard-young-man-barber-barbershop-4177957/) | Pavel Danilyuk / Pexels | Recadrage vertical, tempe et outil |
| S3 | [4178110](https://www.pexels.com/video/a-man-having-a-facial-haircut-4178110/) | Pavel Danilyuk / Pexels | Recadrage vertical, détails de la barbe |
| S4 | [4177796](https://www.pexels.com/video/a-man-fixing-a-man-s-hair-after-haircut-4177796/) | Pavel Danilyuk / Pexels | Recadrage vertical, profil et finition |

[Licence Pexels](https://www.pexels.com/license/) · Les fichiers sont affectés aux scènes de la simulation. Ne pas redistribuer les originaux comme bibliothèque stock ni laisser entendre que les sujets avalisent une offre. Voir `ingenierie/manifest-rushs.json` pour les URLs, cadrages et SHA-256.

Polices : Manrope, IBM Plex Mono, Plus Jakarta Sans et Montserrat, licences SIL OFL jointes dans `assets/`. Le nouvel habillage utilise Pinyon Script (nom) et DM Serif Display (prestation), sous SIL OFL 1.1, avec licences dans [`assets/fonts-t2/`](assets/fonts-t2/). Interface de démonstration adaptée du [T1 public](https://github.com/j9028379-hue/vitrine-video-t1-pilot) au commit `ad4ff15a76dcba7bd08b7e8f56052e842b3e794f` ; pas de changement sur le projet d’origine. Les droits et éventuelles conditions du socle T1 restent distincts de ceux des polices et des rushs.

Great Clips, The Barber Lab, Maison Nafaya et La Barbera Salón sont cités comme références. Aucun MP4 de référence ni musique de référence dans ce kit.

## Musique intégrée

| Place | Œuvre et auteur | Licence | Film intégré |
| :---: | :--- | :--- | :--- |
| 1 | [Afrobeat — Alex Morgan](https://freemusicarchive.org/music/alex-morgan/pop-afro-party-instrumentals/afrobeat-1/) · Free Music Archive | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | [MP4](media/afrobeat/fma-279236.mp4) |
| 2 | [Afro House — Alex Morgan](https://freemusicarchive.org/music/alex-morgan/pop-afro-party-instrumentals/afro-house/) · Free Music Archive | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · IA déclarée par l’auteur · Content ID non vérifié | [MP4](media/afrobeat/fma-279237.mp4) |
| 3 | [Hot Amapiano Beats — Alex Morgan](https://freemusicarchive.org/music/alex-morgan/pop-afro-party-instrumentals/hot-amapiano-beats/) · Free Music Archive | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · IA déclarée par l’auteur · Content ID non vérifié | [MP4](media/afrobeat/fma-279239.mp4) |
| 4 | [Amapiano — Elijah_K](https://freemusicarchive.org/music/elijah-k/single/amapiano/) · Free Music Archive | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | [MP4](media/afrobeat/fma-265362.mp4) |

Modifications : extrait de 30 secondes, tempo calé pour les fonds 1/4 ; tempo d’origine pour les fonds 2/3, égalisation, ajustement de niveau et fondus ; aucune modification de l’image. La piste 1 est intégrée depuis son 0:00. Les crédits et les liens sont repris sous le lecteur et dans les métadonnées de chaque film. Les licences couvrent les pistes selon leurs conditions, pas les autres éléments du spot. Respecter l’attribution en rediffusion ; aucun MP3 original ou certificat dans le dépôt. Aucune garantie d’absence de réclamation Content ID.


## Rendu dans le navigateur

[Mediabunny](https://github.com/Vanilagy/mediabunny), Vanilagy, `1.66.1`, est distribué ici sans modification sous [MPL 2.0](assets/vendor/mediabunny-LICENSE.txt). [Version source exacte et intégrité](assets/vendor/SOURCES.md). Il sert au décodage, à l’encodage et à l’assemblage MP4 ; le dessin des textes et transitions appartient au T2.

## Film final narré

[Studio Vitrine — Signature coiffure T2](livrables/09-film-final-t2.md) réutilise les quatre rushs recadrés ci-dessus et *Harbor Lanterns* — FreeVibeVault, [fiche de la piste](https://freevibevault.com/track/ghj3du94kp45fclg9a9ofcqb), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Extrait depuis le début au tempo d’origine, égalisation, fondus, réduction du fond sous la voix. Cinq prises d’une voix synthétique française déjà préparée pour la démonstration ont été calées et mixées sans changer le débit. Pas de voix Piper dans ce film, pas de mention d’une adresse non confirmée. Seuls le film mixé et sa transcription sont publiés, pas les fichiers de voix isolés ni les essais.

## Synthèse optionnelle, à la demande

L’atelier peut lire le texte du client en français ou en anglais. [Piper](https://github.com/OHF-Voice/piper1-gpl) est un moteur séparé installé localement ; aucun modèle ni narration générée par Piper n’est publié dans ce dossier.

- Français : `fr_FR-siwis-medium`, [fiche du modèle](https://huggingface.co/rhasspy/piper-voices/tree/0ca208afc2a2ee102b1e961e72e0a7e4907be3d0/fr/fr_FR/siwis/medium), [SIWIS French Speech Synthesis Database](https://datashare.is.ed.ac.uk/handle/10283/2353), CC BY 4.0 pour le jeu de données.
- Anglais : `en_US-ljspeech-medium`, [fiche du modèle](https://huggingface.co/rhasspy/piper-voices/tree/bae641dcb5a608cff81ccaf7ff018baaca1a33e1/en/en_US/ljspeech/medium), [LJ Speech Dataset](https://keithito.com/LJ-Speech-Dataset/), domaine public.

Les crédits de synthèse sont inclus dans les métadonnées lorsqu’une voix est générée. Pour une prise personnelle, s’assurer d’avoir le droit d’utiliser l’image et la voix avant diffusion.
