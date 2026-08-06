# Tourisme Europe comparatif — V3.1

Application Streamlit comparant la fréquentation et la compétitivité touristique de 15 pays européens, avec une analyse approfondie France–Espagne.

## Nouveautés V3

- ouverture directe sur les tarifs indicatifs en euros ;
- tableau des prix unitaires France–Espagne–Italie avant les indices statistiques ;
- budget de séjour de référence immédiatement visible ;
- comparateur détaillé France–Espagne–Italie sur six postes de prix ;
- bargraphes groupés, valeurs visibles et référence UE=100 ;
- simulateur de budget en euros avec quantités et prix français modifiables ;
- estimation par poste : hébergement, déjeuners, dîners, boissons alcoolisées et sans alcool, transport et loisirs ;
- séparation visible entre données officielles, proxys et hypothèses utilisateur.

## Fonctions conservées de la V2

- évolution des nuitées de 2019 à 2024, en volume et en indice 2019=100 ;
- saisonnalité mensuelle et poids des trois mois les plus forts ;
- part de juin à août et mois de pointe ;
- structure des nuitées entre hôtels, locations de courte durée et campings ;
- classement des régions NUTS 2 françaises et espagnoles ;
- enrichissement du duel France–Espagne avec la saisonnalité et les hébergements.

## Indicateurs

- nuitées totales et étrangères ;
- arrivées dans les hébergements touristiques ;
- part de la clientèle étrangère ;
- durée moyenne ;
- nuitées par habitant ;
- capacité en places-lits ;
- occupation des chambres d'hôtels ;
- indice de prix restaurants et hôtels, moyenne UE = 100 ;
- évolution annuelle des nuitées.

Les données statistiques proviennent de l'API officielle Eurostat. Les commentaires explicatifs sont séparés des mesures.

## Déploiement Streamlit

1. Copier tout le contenu dans le dépôt `tourisme-europe-comparatif`.
2. Envoyer les fichiers sur la branche `main`.
3. Dans Streamlit Community Cloud, sélectionner le dépôt, la branche `main` et `app.py`.

## Actualisation

Le workflow GitHub Actions est prévu le 5 janvier, avril, juillet et octobre. Il peut aussi être lancé manuellement depuis **Actions > Actualisation des données touristiques > Run workflow**.

La base annuelle 2024 est utilisée car elle est complète et homogène pour tous les indicateurs. La V3 conserve les séries annuelles depuis 2019 et les données mensuelles 2024 sans mélanger données consolidées et résultats provisoires.

## Limite assumée

Eurostat regroupe hôtels et restaurants dans une seule catégorie de prix. Il ne publie pas non plus de tarifs harmonisés pour les consommations servies au bar. La V3 utilise donc les boissons vendues au détail comme proxy clairement signalé et transforme les indices en euros uniquement à partir des hypothèses françaises saisies dans le simulateur.

La V3 ne classe toujours pas les pays sur « l'accueil ». Il n'existe pas de série annuelle européenne suffisamment homogène pour transformer ce sujet en note objective.
