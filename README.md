# VéloRouter Lausanne
Application de routing développée à partir du framework Flask. Il s'agit du code source de l'application, mais elle n'est pas disponible en ligne pour l'instant. 

Cette application a été réalisée dans le cadre de mon Mémoire de Master pour la Master en Géographie spécialisation Analyse Spatiale et Systèmes Complexes de l'Université de Lausanne. Le mémoire complet est mis en ligne ici.

L'application a pour but de proposer un itinéraire pour un déplacement à vélo qui favorise la sécurité et le confort.
Pour déterminer ces derniers, différentes variables sont prises en comptes :
<li> La pente
<li> Les infrastructures cyclables en lien avec la charge de trafic et la limite de vitesse
<li> La présence de trafic de poids lourds
<li> Le caractère agréable de l'environnement (zones vertes et étendues d'eau)

Pour représenter la qualité cyclable des rues, c'est le concept de distance perçue qui est utilisée. Les segements composants une route possèdent une distance originelle qui va être mulitpliée par un coût multiplicateur pour donner la distance perçue. Cette dernière est plus grande que la distance originelle dans le cas d'une mauvaise qualité cyclable ; les conditions de sécurité et de confort sont négatifs ce qui donne l'impression que la rue s'allonge. Au contraire, une rue avec une bonne qualité cyclable donnera l'impression d'être plus courte ; la distance perçue est plus courte que la distance originelle. 

Chacune des caractéristiques évoquées plus haut est donc associée à un coût multiplicateur. Ces coûts s'additionnent pour donner un coût total, la qualité cyclable, qui multiplie la longeur du segment associé. La composante associée aux infrastructures cyclables est la plus complète puisqu'elle prend en compte 3 variables à la fois. C'est elle qui sert de base et sa valeur de référence est 1. Les autres composantes ont comme valeur de référence 0, et peuvent augmenter plus ou moins au-dessus ou au-dessous de cette valeur.

Les différentes caractéristiques s'additionnent selon la formule :

$$ C_{Lien} = C_{T} + C_{IC} +C_{PL} - B_{AE} $$ 

T : Topographie ; IC : Infrastructures cyclables ; PL: poids lourds ; AE : attractivité environnement

Les détails de la définition des coûts sont disponibles dans le travail de mémoire.

# Données
Les données utilisées viennent de différentes sources :
<li> OpenStreetMap pour le réseau cyclable et les étendues d'eau et zones vertes
<li> SwissTopo pour le Modèle Numérique de Terrain 2017 pour calculer la pente 
<li> Guichet cartographique de la Ville de Lausanne pour les aménagements cyclables (rues et intersections) et les zones à vitesse modérée
<li> Le Modèle National du Trafic Voyageur 2017 par le DETEC pour la charge de trafic 
