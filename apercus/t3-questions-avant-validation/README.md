# T3 — Apporter une preuve

Atelier navigateur : fiche, quatre prises, choix parmi les quatre musiques, voix personnelle facultative et export MP4 vertical. Ouvrir `index.html` via un serveur HTTPS ou localhost ; Chrome ou Edge récent, avec WebCodecs/H.264. Les médias personnels restent dans le navigateur : seules les ressources statiques sont téléchargées. L’utilisateur doit télécharger le MP4 avant de fermer l’onglet et vérifier les droits de diffusion des images et de la voix.

L’encodage et le mélange s’exécutent sur l’appareil ; leur vitesse et les formats acceptés dépendent du navigateur. Les résultats et le mix sont des adaptations du moteur Python/FFmpeg local : ils ne sont pas identiques octet par octet. Mires et caméra/microphone simulés ont servi aux recettes ; aucun appareil physique n’a été testé. Les crédits de la piste retenue sont affichés et téléchargeables.

Consulter `CREDITS.md`, `audio/catalogue.json` et `vendor/SOURCES.md` pour la provenance et les licences. Les mires sont graphiques et fictives. Aucun fichier client n’est stocké dans ce dépôt.

## Aperçu de travail pour validation
Les six libellés statiques sont décrits dans `formulaire/questions.json` ; `config.json` est la configuration lue par les scripts et contient une copie du contrat également exposé dans `contrat.json`. `ingenierie/plan.json` documente les segments existants de `render.worker.mjs` ; ce fichier n’est pas chargé par le moteur. Ces JSON ne sont pas le schéma ni le moteur Android du gabarit restaurant partenaire. Ne pas remplacer la version officielle avant validation. Les quatre prises sont de 8, 10, 10 et 8 secondes minimum, et sont montées en 30 secondes. Le numéro confirmé est du texte, sans lien actif. Le prix de départ et sa monnaie sont fournis par le client. L’outil n’est utilisé que dans le guide.
