# T3 — Comparaison avec les gabarits publiés T1 et T2

**Objet :** reprendre exactement la présentation commune des douze écrans, sans les médias ni les réponses de T1/T2 et sans toucher au film muet T3 déjà validé. Cette r2 est un lot de revue, pas une mise en production ni un accord P3.

## Références et constat

[T1 · Coupe et barbe](https://rawcdn.githack.com/bigmisericorde-blip/vitrine-video-coiffure-signature/1c8128d701ef163b4fd7c37e4cb03911872f36e8/apercus/coiffure-et-beaute/site/t1/ecrans.html?metier=coiffure) · [T2 · Pose de vernis rouge](https://rawcdn.githack.com/bigmisericorde-blip/vitrine-video-coiffure-signature/1c8128d701ef163b4fd7c37e4cb03911872f36e8/apercus/coiffure-et-beaute/site/t2/ecrans.html?metier=manucure). Les deux références sont au commit `1c8128d701ef163b4fd7c37e4cb03911872f36e8`. Vérification des tailles et des identifiants Git des sources, puis lecture depuis une copie locale du même site dans Chromium. Aucun changement sur les pages publiques.

| Point | Présentation commune T1/T2 observée | T3 r1 : ce qui différait | T3 r2 : reprise |
|---|---|---|---|
| Galerie | Bandeau Vitrine Vidéo, titre « Les 12 écrans. », fond vert sombre, accent menthe. Sur bureau index à gauche et vue à droite ; sur mobile le cadre précède l’index. | Maquette crème et nouveau panneau d’inspection. | Même balisage et CSS de galerie, mêmes polices Manrope et IBM Plex Mono. |
| Navigation | 4 lignes × 3 liens, choix d’écran, précédent/suivant, ouverture de l’écran seul. | Boutons et repères différents, pas la galerie standard. | Même ordre, mêmes commandes. `#1`…`#12`, `#seul-1`…`#seul-12`. Les anciens `#ecran-01`…`#ecran-12` sont reconnus. |
| Consigne (A) | Image arrêtée derrière la feuille de tournage défilante, prise X/4, durée, À filmer/À éviter et son. | Petite image insérée dans une maquette différente. | Même cadre, panneau et typographie Jakarta/Montserrat. Seules les indications et les images sont spécifiques au soin. |
| Chrono (B) | Vidéo verticale dans le cadre, pastille de chrono et barre ; lecture en boucle en galerie. | Lecteur réduit et commandes de simulation dans l’aperçu. | Vidéo et progression dans le cadre du gabarit ; chrono piloté par le clip. |
| Relecture (C) | Même extrait de la prise, infos et question dans le panneau bas ; boutons non validants en consultation. | Bloc de lecteur/commandes d’une autre forme. | Même panneau. Réservé à la consultation en galerie et écran seul. L’essai séparé garde la reprise et la validation explicite, sans mémoire persistante. |
| Film d’exemple | Carte et lecteur distincts de la navigation des prises. Les repères de cassures sont propres à T2. | Fenêtre modale. | Carte distincte et accès direct sans valider une prise. Aucun repère T2 transporté au T3. |

## Mapping T3, sans changement du film

| Prise | Consigne → Chrono → Relecture | À filmer (proposé) | Extrait muet du montage P2-r3 (fin exclue, 24 i/s) |
|---|---|---:|---|
| S1 · Départ | 01 → 02 → 03 | 8 s | Images 27–109 · 3,417 s |
| S2 · Geste | 04 → 05 → 06 | 10 s | Images 109–274 · 6,875 s |
| S3 · Détail | 07 → 08 → 09 | 10 s | Images 274–344 · 2,917 s |
| S4 · Dernière vue | 10 → 11 → 12 | 8 s | Images 494–588 · 3,917 s |

Le lettrage apparaissant dans certains extraits est déjà présent dans le montage source. Le carton de fin « Réserver ce soin » reste sans destination. Aucun stock brut, fichier sonore privé ni média d’un autre gabarit dans ce lot. La question et l’exemple du geste sur la joue ne prétendent pas à un résultat clinique.

## Relecture et reconstruction

Ce dossier contient la galerie autonome avec le film et la planche intégrés, les douze vues individuelles, le guide, la fiche, l’export original, les droits, les rapports et les empreintes. Les sources dans `outils/`, le master dans `media/` et le commit de référence permettent de reconstituer la revue. Voir [Intégration](INTEGRATION.md). Le lien épinglé au commit r1 reste historique. Pour la correction, utiliser le lien épinglé au commit r2 donné après envoi.
