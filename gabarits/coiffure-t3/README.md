# T3 beauté — version navigateur 30 secondes maximum

Quatre scènes et 12 états. La durée s’adapte aux prises ; elles sont lues à vitesse normale. La fiche, les guides et le plan de texte sont reliés aux JSON. Le son des prises ou une voix séparée sont facultatifs. La vidéo de soin de référence et les autres gabarits ne sont pas remplacés.

Le MP4 final est contrôlé après encodage ; au-delà de 30 secondes le téléchargement est refusé, sans couper une prise. Une prise ou une voix qui atteint sa limite est refusée si sa fin risque d’être coupée. Le contrôle de niveau ne comprend pas le sens d’une phrase.

Les sous-titres éventuels sont saisis manuellement avec leurs temps et doivent reproduire les paroles réelles ; le moteur ne les transcrit ni ne les vérifie. Les prises et la fiche peuvent être sauvegardées volontairement sur cet appareil de confiance ; ni la prise en cours, ni la voix séparée, ni les sous-titres, ni les choix son ne sont sauvegardés. Le navigateur peut effacer ses données ; ne pas utiliser le même travail simultanément dans plusieurs onglets.

Ce gabarit fonctionne dans un navigateur compatible avec les technologies utilisées, pas comme un paquet Android autonome. Il n’est pas directement conforme au schéma du JSON restaurant de l’ami. Les tests sont documentés dans `ingenierie/contrat-t3.json` ; aucun téléphone physique ni intégration au moteur de l’ami n’ont été testés. Exécuter `python3 ingenierie/verifier-contrat.py`.
