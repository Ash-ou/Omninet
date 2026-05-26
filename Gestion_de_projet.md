# Document de gestion de projet – OmniNet

## 1. Objet du document

Ce document structure la réalisation technique et l’organisation de l’équipe pour concevoir l’outil de supervision et d’analyse réseau OmniNet. L’objectif principal est de démontrer la capacité des membres à organiser un projet de manière professionnelle et à travailler en équipe.

Ce livrable sert de référentiel unique pour l’ensemble de l’équipe concernant les processus de développement, les standards de qualité et les modalités de livraison.

## 2. Position dans la chronologie projet

La phase de planification intervient pour valider le bloc de compétences lié à la gestion de projet. Elle succède au cadrage initial qui a permis de comprendre le besoin et de définir le périmètre fonctionnel.

Elle couvre l’intégralité du cycle de vie de la réalisation applicative jusqu’au déploiement final et à la préparation de la soutenance.

## 3. Méthode de travail retenue

La méthodologie s’appuie sur un calendrier prévisionnel de type diagramme de Gantt ou l’utilisation d’un tableau Kanban. Le travail collaboratif est centralisé sur un dépôt GitHub propre et structuré.

La gestion des versions impose un découpage strict par fonctionnalité avec des branches dédiées et un versioning clair. L’approche intègre les principes du framework Scrum pour assurer un développement itératif, incrémental et adaptable en continu.

## 4. Équipe projet et rôles

L’organisation interne, la répartition des tâches et les rôles attribués à chacun doivent être présentés formellement lors de la soutenance. Le cadre Scrum implique de définir :

- Un **Product Owner** garant de la vision fonctionnelle.
- Un **Scrum Master** facilitant les processus.
- Une **Équipe de développement** concentrée sur la réalisation technique.

## 5. Artefacts Scrum

Les livrables techniques exigés incluent :

- Le dépôt GitHub.
- Des messages de commit explicites.
- Un fichier README détaillé.
- Une release applicative testable.

Le pilotage quotidien nécessite :

- Un **Product Backlog** listant l’intégralité des fonctionnalités à développer.
- Un **Sprint Backlog** constitué à chaque itération pour regrouper les tâches engagées.
- Un **Incrément logiciel fonctionnel** validé à la fin de chaque cycle de développement.

## 6. Cérémonies agiles

L’événement de restitution final attendu est la soutenance accompagnée d’une démonstration fluide et maîtrisée de l’outil.

L’organisation prévoit :

- Un **Sprint Planning** en début d’itération pour définir les objectifs à court terme.
- Un **Daily Scrum asynchrone** pour la synchronisation technique régulière de l’équipe.
- Une **Sprint Review** pour valider l’incrément produit.
- Une **Sprint Retrospective** pour identifier les axes d’amélioration sur les méthodes de travail.

## 7. Story points et estimation

L’évaluation de l’effort s’effectue via le **Planning Poker** en utilisant la suite de Fibonacci. Les critères de pondération incluent la complexité technique du code, le temps de réalisation estimé et l’incertitude liée aux bibliothèques externes.

L’équipe respecte une **Definition of Done** stipulant qu’une tâche est terminée uniquement lorsque le code est testé, documenté, revu par un pair et fusionné sur la branche principale.

## 8. Product backlog structuré

Le périmètre impose :

- La détection des équipements connectés.
- Le scan d’adresses IP.
- L’identification des ports.
- La récupération d’informations sur les services.

L’outil intègre :

- L’observation du trafic réseau.
- La détection de comportements malveillants.
- La génération d’alertes.
- L’export de rapports en JSON ou CSV.

Les éléments de ce backlog sont hiérarchisés selon la valeur apportée à l’utilisateur final et la criticité technique.

## 9. Features par epic

- **Epic Architecture** : Concevoir une solution technique cohérente justifiée par des schémas clairs.
- **Epic Réseau** : Implémenter toutes les fonctionnalités fondamentales de supervision.
- **Epic Cybersécurité** : Intégrer les mécanismes d’analyse, générer des alertes et produire des logs.
- **Epic Interface** : Développer une interface web cohérente avec l’ensemble du système.
- **Epic DevOps** : Automatiser la validation du code et structurer le processus de publication.

## 10. User stories et tasks MVP

Les développements backend s’effectuent en Python avec le framework FastAPI. La réalisation du frontend s’appuie sur HTML, CSS, JavaScript, avec l’intégration possible de Bootstrap ou Tailwind CSS.

La sécurité de l’application est prise en compte dès sa conception technique. Les exigences sont traduites sous forme de **User Stories** pour clarifier les attentes fonctionnelles du Minimum Viable Product.

## 11. Découpage prévisionnel par sprint

Le plan opérationnel séquence le développement :

- Conception des API.
- Intégration de l’interface.
- Mise en place des mécanismes de sécurité.
- Phase de tests et de documentation.

- **Sprint 1** : Socle technique et infrastructure backend.
- **Sprint 2** : Interface utilisateur et fonctionnalités de supervision de base.
- **Sprint 3** : Module de cybersécurité et système d’alertes.
- **Sprint 4** : Stabilisation, recette finale et préparation de la release.

## 12. Jalons projet

- **Jalon 1** : Validation de l’architecture de la solution et justification des choix techniques.
- **Jalon 2** : Livraison d’une base applicative fonctionnelle démontrant la démarche qualité.
- **Jalon 3** : Réalisation des tests avant le déploiement.
- **Jalon final** : Livraison de la release sur GitHub et du support de présentation pour la soutenance.

## 13. Risques projet

L’équipe doit identifier tous les risques du projet et documenter la manière dont ils sont gérés. Les risques principaux incluent :

- La dépendance à un réseau de test fonctionnel.
- Les exigences strictes en sécurité logicielle.
- Un périmètre volontairement limité.

L’équipe anticipe également les contraintes de temps et prévoit des solutions techniques de contournement pour sécuriser la production du Minimum Viable Product.

## 14. Indicateurs de suivi Scrum

La traçabilité de l’évolution du projet s’effectue via GitHub, avec la rédaction de messages de commits réguliers, clairs et compréhensibles.

La qualité d’organisation est mesurée par :

- Le maintien de branches propres avec un découpage par fonctionnalité.
- La tenue d’un **Burndown Chart** pour visualiser l’avancement.
- La surveillance de la **vélocité** de l’équipe à chaque itération.

## 15. Livrables de pilotage

- Un dépôt GitHub intégral contenant le code source structuré.
- Un fichier README précisant les modalités d’installation et d’utilisation de la solution.
- Une release GitHub correspondant à la version finale et facilement testable.
- Un support de présentation au format PPT ou PDF, clair et paginé, pour accompagner la démonstration finale.

## 16. Outils de collaboration et communication

- Une plateforme de messagerie instantanée centralise les échanges techniques quotidiens et les alertes.
- Un outil de maquettage UI est utilisé pour concevoir et valider l’interface avant la phase de développement web.
- Une pipeline d’intégration continue est configurée sur GitHub Actions pour valider automatiquement la compilation du code Python à chaque modification.
