# Vitrine Vidéo · COIFFURE‑T2

**Version candidate validée visuellement :** Le propriétaire a validé le rendu général présenté et choisi de conserver séparément le rendu Onglerie, sans voix pour l’instant. Les guides, les scènes, le plan et les quatre fonds sont conservés. Tests navigateur et caméra simulée : réussis ; aucun test sur appareil physique. Les exports réels dépendent de la compatibilité du navigateur et de l’appareil.

**Version candidate `2.0.3-rc.1` · 3 ou 4 prises → MP4 vertical avec lettrage et musique, sans voix off.** Le même parcours prépare les prises, compose le montage R04, incruste les réponses de la fiche et pose un des quatre fonds retenus. Aucun média client n’est téléversé.

## Essayer

1. Depuis le dossier du gabarit, lancer `python tools/preview.py --host 127.0.0.1 --port 8092`.
2. Dans Chrome ou Edge récent, ouvrir `http://127.0.0.1:8092/` : remplir la fiche ou choisir **Charger la fiche d’exemple** pour tester avec les quatre mires incluses. Les mires sont graphiques et ne montrent aucune prestation réelle.
3. Valider l’**avant**, le **geste**, le **détail** et le **résultat**. Avec trois vidéos, reprendre S2 pour S3 seulement si le détail recadré est lisible à la relecture. Le micro est facultatif ; le son original est écoutable en relecture, pas copié dans le film de production.
4. Le bouton **Télécharger le MP4** livre le même fichier que le lecteur : 720 × 1280, 30 s, 900 images, H.264 + AAC-LC 48 kHz stéréo. Une seule musique, aucune voix ajoutée. Télécharger avant de quitter l’onglet : les prises ne sont pas enregistrées ailleurs.

Le prix, l’accroche, le nom et le lieu sont facultatifs. La consigne de réservation peut paraître à l’image, **pas le numéro ni le lien de réservation**. Le lien de contact vérifié par le commerçant reste à côté du lecteur.

## Pour reprendre le travail

- [Guide d’intégration](INTEGRATION.md) : commandes, responsabilités, contrats, profil testé, limites et garde avant publication.
- [Douze écrans et règles de capture](docs/12-ecrans.md) · [Crédits et droits](CREDITS.md).
- `config/template.json` est le canonique du candidat. L’étalon R04 approuvé et les prises de revue restent à part : leur empreinte de référence est conservée, leurs fichiers ne sont pas dans le lot. Les essais parlés restent hors production.

Les résultats de recette figurent dans `conformance/`. Les mires ne sont pas des vidéos de clientèle ; les droits des images utilisées pour les aperçus séparés ne s’étendent pas automatiquement aux prises des utilisateurs.


## Deux finitions selon la prestation
Sur décision du propriétaire : `manucure` utilise les cadrages, transitions et l’habillage de la variante Onglerie `99003f2529839e6be3182b85a440cadeae363c82`. Les autres prestations gardent le rendu général R04. Les fonctions de recadrage, les cassures, le moteur de composition Onglerie et son habillage sont inclus séparément ; le plan source et les fonds ne sont pas modifiés. Le contexte métier accompagne l’appel au worker ; un appel direct qui l’omet prend la base générale historique. Les exemples fournis restent des mires graphiques : la démo Onglerie filmée de la branche historique n’est pas redistribuée ici. Le choix de continuer sans voix pour T2 a été confirmé par le propriétaire ; l’export ne contient aucune voix off. Une recette sur appareil physique reste à effectuer ; ne pas l’annoncer comme réalisée.
