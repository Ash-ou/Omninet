# Spécifications projet OmniNet

## 1. Contexte et objectif

Le projet consiste à concevoir et réaliser un outil de supervision et d’analyse réseau. L’outil a pour objectif d’observer et de mapper un réseau informatique, en détectant les équipements connectés, les flux de trafic et les services actifs.

Le système vise à détecter des événements suspects et à générer des alertes exploitables. Le nom choisi pour cet outil est **OmniNet**.

## 2. Périmètre fonctionnel

- L’outil doit détecter les équipements connectés au réseau.
- La solution doit pouvoir scanner une plage d’adresses IP.
- L’application doit identifier les ports ouverts et récupérer des informations sur les services réseau.
- Le système doit observer le trafic réseau pour détecter des comportements suspects ou malveillants.
- L’application doit générer des alertes.
- L’outil doit produire des rapports exportables aux formats JSON ou CSV.

## 3. Contraintes techniques

- Le backend doit être développé en **Python** en utilisant **FastAPI** et les bibliothèques nécessaires.
- Le frontend doit être réalisé en **HTML**, **CSS** et **JavaScript**.
- L’utilisation de **Bootstrap** ou de **Tailwind CSS** est autorisée pour le développement de l’interface.
- Les choix techniques devront être justifiés et l’architecture globale devra être documentée par des schémas lisibles.

## 4. Livrables attendus

- Un dépôt **GitHub propre et structuré** contenant l’intégralité du code source.
- Un fichier **README** présentant l’outil et précisant son installation et son utilisation.
- Une **release GitHub** correspondant à la version finale fonctionnelle et testable.
- Un **support de présentation** au format PPT ou PDF, clair, structuré et paginé, pour la soutenance.

## 5. Organisation et gestion de projet

- L’équipe doit mettre en place une méthode de travail organisationnelle de type calendrier prévisionnel **Gantt** ou **Kanban**.
- L’organisation de l’équipe, les rôles attribués et la répartition des tâches doivent être clairement définis.
- L’équipe doit assurer le suivi de l’avancement et le pilotage du projet.
- Les risques du projet doivent être identifiés et leur mode de gestion doit être expliqué.
- Le travail nécessite un **versioning clair** avec des **commits réguliers et explicites**, ainsi qu’une organisation en branches découpées par fonctionnalité.

## 6. Qualité, sécurité et déploiement

- La sécurité de l’application doit être prise en compte dès sa conception et durant sa réalisation.
- Le développement doit démontrer une **démarche qualité** (tests, revues de code, documentation, etc.).
- La solution doit être **testée de manière cohérente** avant son déploiement.
- L’équipe devra expliquer la **faisabilité du déploiement** de la solution technique (locale, serveur interne, environnement de test, etc.).
