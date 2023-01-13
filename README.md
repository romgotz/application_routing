# VéloRouter Lausanne
Application de routing développée à partir du framework Flask. Il s'agit du code source de l'application, mais elle n'est pas disponible en ligne pour l'instant.

L'application a pour but de proposer un itinéraire pour un déplacement à vélo qui favorise la sécurité et le confort.
Pour déterminer ces derniers, différentes variables sont prises en comptes :
<li> La pente
<li> Les infrastructures cyclables en lien avec la charge de trafic et la limite de vitesse
<li> La présence de trafic de poids lourds
<li> Le caractère agréabéle de l'environnement (zones vertes et étendues d'eau)


Cette application a été réalisée dans le cadre de mon Mémoire de Master pour la Master en Géographie spécialisation Analyse Spatiale et Systèmes Complexes de l'Université de Lausanne. Le mémoire complet est mis en ligne ici.

# Données
Les données utilisées viennent de différentes sources :
<li> OpenStreetMap pour le réseau cyclable et les étendues d'eau et zones vertes
<li> SwissTopo pour le Modèle Numérique de Terrain 2017 pour calculer la pente 
<li> Guichet cartographique de la Ville de Lausanne pour les aménagements cyclables (rues et intersections) et les zones à vitesse modérée
<li> Le Modèle National du trafic voyageur 2017 par le DETEC pour la charge de trafic 
