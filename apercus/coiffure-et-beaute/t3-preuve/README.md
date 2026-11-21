# Vitrine Vidéo · T3 — Apporter une preuve

**Revue des douze écrans · r1.** Ouvrir [la galerie autonome](index.html), puis un des 12 écrans ou le parcours complet. Exemple de soin du visage ; vocabulaire simple et questions générales applicables à d’autres métiers.

- [12 écrans individuels et navigation](capture/12-ecrans.md) · [Planche des 12](capture/planche-12-ecrans.jpg) · [Questions proposées](formulaire/Fiche-questions-T3.md).
- [Film muet P2-r3](media/T3-Essai-P2-r3-muet.mp4) · [Source et droits](recherche/Droits-et-perimetre.md).
- [Rapport de recette](rapports/Controle-12-ecrans.json) · [Intégration](INTEGRATION.md) · [Manifeste](manifest.json).

Le film et son écriture ont été validés comme essai. Le parcours et les durées de prise restent **à relire**. **Ni caméra réelle, ni nouveau montage calculé à partir des réponses, ni intégration d’application.** Aucun audio privé ou pack de production. T3 est ici un nom éditorial et non un identifiant catalogue affecté.

## Régénérer en local

Avec Python 3.11+, FFmpeg, Playwright + Chromium et Pillow :

```sh
python3 outils/fabriquer.py --master media/T3-Essai-P2-r3-muet.mp4 --sortie ../t3-revue-reconstruite
python3 outils/recette.py ../t3-revue-reconstruite
python3 outils/sceller.py ../t3-revue-reconstruite
(cd ../t3-revue-reconstruite && sha256sum -c SHA256SUMS)
```

La galerie n’utilise ni CDN ni requêtes de média externes. Le nom de dossier n’annonce pas une version de production.
