# Tourisme Europe comparatif — V1

Application Streamlit comparant la fréquentation et la compétitivité touristique de 15 pays européens, avec une analyse approfondie France–Espagne.

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

La base annuelle 2024 est utilisée car elle est complète et homogène pour tous les indicateurs de la V1. Les données mensuelles 2025-2026 pourront être intégrées dans une version suivante sans les mélanger aux résultats annuels consolidés.

## Limite assumée

La V1 ne classe pas les pays sur « l'accueil ». Il n'existe pas de série annuelle européenne suffisamment homogène pour transformer ce sujet en note objective. Une future version pourra intégrer des enquêtes de satisfaction comparables en indiquant précisément leur date et leur méthode.
