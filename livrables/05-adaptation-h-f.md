# Adapter le même gabarit homme / femme

**Les quatre scènes sont quatre rôles, pas quatre prestations.** `plan.json` associe les rôles aux plans rendus ; `cas-test.json` fournit les consignes, les fichiers et la copie. La colonne balayage est un exemple de contenu, pas un deuxième test exécuté ni une commande de tournage pour cette livraison.

| Scène | Rôle éditorial | Coupe + barbe — test livré | Balayage — exemple de transposition |
| :--- | :--- | :--- | :--- |
| S1 · 6 s | Montrer qui travaille et sur qui | Professionnel et profil au fauteuil | Professionnelle et cliente en 3/4, salon identifiable, longueurs visibles |
| S2 · 7 s | Montrer la prestation en cours | Tondeuse et tempe dans le même cadre | Pinceau et mèche ; passage complet en lumière neutre |
| S3 · 7 s | Montrer le détail qui justifie le bénéfice | Outil et trait de barbe | Placement de lumière sur les mèches qui encadrent le visage ; montrer la main et le détail réel |
| S4 · 7 s | Montrer le résultat et porter le CTA | Profil net en fin de prestation | Même cliente, balayage final, une rotation lente qui laisse voir longueur et reflet |

**Le même ordre commercial** : prestation et prix → preuve → détail → résultat → réservation. Même vert, fonds secondaires, Manrope et Plex, split, badge, iris, raccord d’outil ou de direction, push du CTA et rail final. Les tons de cheveux et de peau restent fidèles aux rushs. Aucun effet rose ou bleu ajouté en fonction du genre.

Dans le cas balayage, remplacer par exemple « Coupe + barbe » par « Balayage lumière » et « Un seul rendez-vous » par « Des reflets sur mesure ». N’écrire « Sans couper la longueur » que si la prestation et le résultat le démontrent. Adapter **le même champ** de service, prix et CTA dans le ticket, le badge, le lecteur et sa destination. Ne pas ajouter un prix ou une disponibilité non vérifiés.

### Checklist de génération

1. Vérifier les quatre scènes et les autorisations ; identifier le geste principal, le point d’intérêt et le sujet. Une source-source qui ne permet pas d’établir la continuité ne justifie pas une promesse de transformation « avant/après ».
2. Normaliser les quatre sources à 720×1280/30, S1 à S4. Pour une autre résolution/orientation d’entrée, adapter le cadrage de normalisation à la source : l’ingeste Pexels du test suppose quatre originaux 1920×1080. Ne pas réutiliser automatiquement ses coordonnées de recadrage sur un clip du client.
3. Éditer le cas, aligner les fenêtres `src`, `speed`, `zoom` et `anchor`. Les types de transitions et l’ordre des douze plans restent les mêmes ; les durées et les positions en images se règlent dans les bornes du plan. Les iris marquent un changement de contexte, pas chaque coupe.
4. Éviter de confondre fluidité et vitesse ; regarder réellement les deux raccords sensibles : outil/objet et résultat. Les prises doivent soutenir les recadrages, sans visage ni main coupés. Vérifier le coût des ralentis courts et répétitions de source sur S4 : si le mouvement saccade, déplacer la fenêtre utile et recontrôler.
5. Contrôler sur téléphone les libellés, les devises, la stabilité du prix, du rail et le CTA. Valider la destination hors session, à la manière d’un client. Ajouter voix et mix dans un export séparé **seulement après validation du master muet**.

### À brancher côté application native

La démo valide le parcours et les paramètres de rendu hors navigateur. En production, relier les quatre validations aux quatre URI capturées, préparer des fichiers normalisés avec leurs empreintes, lancer le plan dans le moteur de rendu et remonter l’état réel. Brancher le CTA à une URL vérifiée et à la même prestation. Les permissions caméra/micro, les erreurs d’upload, la reprise de session, la lecture finale et le partage Android exigent leur propre recette ; ils ne sont pas simulés comme des fonctions déjà livrées.
