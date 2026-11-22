# T3 — Apporter une preuve · moteur musical de revue

**Vérifier les SHA-256 → lire `manifest.json` → charger `contrat.json` → valider la fiche et S1–S4 → rendre le master muet → contrôler le MP4, le crédit et la rotation.**

Le lot rend un film **neuf à partir de la fiche et des quatre prises**. Ni le master P2-r3 ni les MP4 des auditions ne sont des entrées. Les essais précédents et la galerie des douze vues r2 restent inchangés. Cette révision technique n’est ni un ID/version de production, ni un accord P4, P5 ou P6. Les métadonnées `COIFFURE-T3` / `0.1.0-rc.1` sont une identité et une version de revue, égales dans le contrat et le manifeste ; `publication_autorisee: false` reste obligatoire. Le profil `beaute-soin-du-visage-instrumental` est vérifié contre le catalogue local.

## Démarrer hors ligne

Le ZIP de revue contient le code, les quatre extraits FLAC, les polices et quatre prises synthétiques. Pré-requis installés **une fois** : Linux/macOS avec Python 3.11–3.13 et FFmpeg/ffprobe 7 avec libx264, `ebur128` et AAC-LC. La recette de référence a utilisé Python 3.13 et FFmpeg 7.0.2. Installer les dépendances dans un environnement virtuel (`python3 -m pip install -r requirements.txt`), puis les commandes ci-dessous ne contactent aucun service distant.

```sh
python3 outils/lot.py verifier .
python3 service.py --host 127.0.0.1 --port 8094
```

Ouvrir `http://127.0.0.1:8094/` dans un navigateur récent qui lit le MP4 H.264. Remplir la fiche et importer quatre prises, ou charger l’exemple. Relire et garder chaque prise. À l’export, choisir un morceau ou la rotation. Le film relu et le MP4 téléchargé ont les mêmes octets. Un `Credit-musique.txt` est proposé avec le film : **copier ce crédit dans la description lors d’une publication**, en particulier `1000Handz.com` pour *Copa*. L’export **ne publie rien**. Sur l’aperçu Arena, `--demo` limite le parcours aux mires originales ; les imports réels sont réservés à l’atelier sur la boucle locale.

### Ligne de commande et recette

```sh
# Session de démonstration, dossier de sortie local. Ne mets pas de prises client dans le lot.
python3 t3.py rendre --fiche exemple/fiche.json --prises exemple \
  --session ./sessions/demo --id "$(python3 -c 'import uuid; print(uuid.uuid4().hex)')" --piste 03
python3 outils/recette.py --sortie ./sessions/recette-neuve
```

Les quatre fichiers sous `--prises` s’appellent `S1`…`S4` avec l’extension `.mp4`, `.mov` ou `.webm`. `--mode muet` produit un fichier de contrôle sans piste audio et ne change pas la rotation. `--audition --piste 03` fige une piste pour une revue indépendante de la rotation. Pour une session réelle, garder le même `--id` et les mêmes entrées pour relancer ; si tu modifies les entrées, utiliser `t3.py annuler --session … --id …` pour libérer la réservation, puis attribuer un nouvel ID. Le dossier `exports/<id>/` contient `T3.mp4`, `resultat.json` et, si applicable, `Credit-musique.txt`.

`outils/recette_web.py` est le contrôle navigateur optionnel (Playwright + Chromium installés à part). Les empreintes du rapport ancrent les fichiers testés ; elles ne promettent pas que deux encodeurs ou environnements OS distincts généreront les mêmes octets. L’empreinte **image d’un même rendu** doit en revanche rester strictement égale entre le master muet et tous ses exports musicaux.

## Contrat pour l’intégrateur

| Étape | Entrée et résultat |
|---|---|
| Fiche | `lire_fiche()` applique les longueurs, énumérations et profils de caractères du contrat. `service`, `geste`, `detail`, `action` requis ; les champs facultatifs restent vides si non saisis. Aucun CTA cliquable ni coordonnées non fournies. |
| Prises | `S1 8 s`, `S2 10 s`, `S3 10 s`, `S4 8 s` minimum. SDR, ≤ 48 Mio par fichier, recadrage centré en portrait, normalisation CFR. Relecture sur l’original, y compris son éventuel ; les imports ne sont pas édités. Selon le décodeur, un MOV/WebM peut nécessiter une conversion MP4 SDR pour la **relecture navigateur**. |
| Création | `t3.rendre(outils, fiche, prises, session, polices, pack, id, mode, piste)` compose la fiche et les clips indexés. Cache d’image seulement si la fiche, les prises, le code d’image, le contrat et les polices correspondent. Une fiche ou prise modifiée déclenche un nouveau rendu. La prise S3 à 1× occupe les images `[343,430)`, soit **11,433–14,333 s**. Carton `[735,900)`, soit **24,500–30,000 s**. |
| Catalogue | `audio/catalogue.json` lie les quatre IDs aux ressources et à `sources-musicales.json`. Tout est local ; ressource absente, altérée, ou profil différent → erreur (pas de remplacement ni d’export muet automatique). |
| Mise en musique | Image H.264 720×1280, BT.709/30 i/s/900 images, avec PTS et DTS inchangés au mux. Export AAC-LC stéréo 48 kHz/30 s. Contrôle de la piste décodée : −24 à −16 LUFS-I, ≤ −2 dBTP. Aucun son des prises ni voix ajouté au MP4 ; les prises restent intactes. |
| Rotation | La dernière piste réussie est exclue ; une sélection explicite ne peut pas la rejouer immédiatement dans la même session. Écriture atomique, réservation sous verrou, succès après vérification. Un échec ne change pas `dernier_succes`. Le même ID reprend sa réservation ; un ancien succès est idempotent. La rotation Web est limitée à l’onglet/session de l’atelier, pas à un compte ou à plusieurs appareils. |
| Sortie | `resultat.json` reporte signatures H.264/horodatages, mode, empreintes des entrées, piste, licence et crédit à transférer à l’interface de partage. Le même crédit est dans le MP4 et le TXT. |

Dans l’écran de revue r2, les états 1–2 correspondent à la fiche, 3–10 à la consigne et la relecture des quatre prises, 11 au montage (progression réelle) et 12 à la relecture et à l’export. **Ce lot fournit un parcours d’intégration séparé**, il ne modifie pas les douze écrans validés. L’application cible doit encore mapper ses états, brancher la capture native et conserver le ticket de rendu jusqu’à la relance. Adapter sur appareil les permissions, les erreurs et la persistance. Aucun APK, mise à jour OTA, mixage voix ou déploiement n’est livré ici.

### Échecs récupérables

- `FICHE`, `PRISE` : corriger le champ ou remplacer la prise indiquée. Les autres entrées sont conservées en relecture. Si un job est réservé, l’abandonner pour changer ses entrées.
- `PACK`, `AUDIO`, `SORTIE` : restaurer les actifs du lot et vérifier `SHA256SUMS`, puis relancer le même job ; ne pas substituer un morceau.
- `EN_COURS`, `ROTATION`, `JOB`, `SESSION` : reprendre/abandonner le job en attente, choisir une autre piste ou un nouveau job. Si le catalogue change, ouvrir une nouvelle session. Une relance après un succès ne rejoue pas le tour.

Dans l’atelier local, les fichiers importés et calculés restent dans un répertoire temporaire de session. Il n’y a ni télémétrie ni accès HTTP de partage. Exporter ce qui doit être conservé avant de fermer l’atelier ; une fermeture brutale peut laisser des temporaires OS à effacer. Ne pas exposer en réseau le mode d’import. Les seules prises redistribuées ici sont les quatre mires créées dans `outils/creer_exemple.py`.

## Reconstruction, droits et statut

Les quatre MP3 officiels **ne sont pas redistribués dans le lot**. Pour reconstruire les ressources à partir d’un dossier de code avant assemblage, `outils/approvisionner.py --sortie …` retélécharge les éditions exactes, les vérifie et les décode, puis `t3.py preparer-pack --originaux … --sortie …` extrait les FLAC. `CREDITS.md` précise les droits de partage, les modifications et les crédits. Si un fichier officiel change, arrêter et revérifier l’édition et ses droits au lieu de mettre à jour automatiquement une empreinte. Les polices DejaVu sont livrées avec leur notice et ne valent pas approbation typographique P4.

Lot de branche de **revue séparée**. Pas de rushs Mixkit ni de dérivé Mixkit dans le lot, ni musiques précédentes de banc, ni données cliente, ni voix, ni ancien master. L’accord P3 ne porte que sur la revue r2. L’envoi éventuel d’une branche de revue (publique si le dépôt est public) est distinct d’une fusion, d’une Release et de la mise en production.
