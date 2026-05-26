# BUSINESS PLAN – OMNINET

OmniNet est un outil de supervision et d’analyse réseau orienté cybersécurité, destiné à aider les petites et moyennes structures à visualiser leur réseau, détecter des comportements suspects, générer des alertes et exporter des rapports. Ce business plan présente une vision complète du projet, de son marché à son positionnement, en passant par le modèle économique, la stratégie et les perspectives d’évolution.

## 1. Résumé exécutif

OmniNet répond à un besoin simple mais essentiel : comprendre ce qui se passe sur un réseau informatique avant qu’un incident ne devienne critique. L’outil permet la découverte d’équipements, le scan d’adresses IP, l’identification de ports ouverts, l’observation du trafic et la génération de rapports exploitables.

Le projet a une forte dimension académique, mais il peut aussi constituer la base d’une solution crédible pour des PME, des laboratoires ou des établissements de formation. L’ambition est de proposer une solution légère, lisible et modulaire, développée en Python avec FastAPI et accompagnée d’une interface web.

## 2. Présentation du besoin

Les organisations utilisent aujourd’hui des réseaux de plus en plus complexes, souvent hybrides, étendus et exposés à des menaces variées. Elles ont besoin d’outils capables de leur donner une visibilité immédiate sur les équipements connectés, les flux réseau, les services exposés et les signaux faibles d’incidents potentiels.

OmniNet répond à ce besoin en rassemblant plusieurs fonctions clés dans une seule interface : reconnaissance réseau, surveillance, premières analyses de sécurité, alertes et export de données. Le projet s’adresse à des structures qui n’ont pas forcément besoin d’une solution SIEM lourde, mais qui veulent une première couche de contrôle efficace.

## 3. Étude du marché

Le marché visé est celui des outils de supervision réseau, de monitoring et de détection d’événements suspects. Il est soutenu par la croissance des menaces cyber, la multiplication des objets connectés, l’essor du cloud et le besoin de visibilité en temps réel.

Les tendances actuelles vont vers l’automatisation, l’analyse comportementale, les tableaux de bord unifiés et les alertes contextualisées. Les segments les plus pertinents sont les PME, les équipes IT de proximité, les établissements d’enseignement, les laboratoires et les petites équipes cybersécurité.

## 4. Analyse de la demande

La demande est principalement professionnelle et organisationnelle. Les utilisateurs attendent une solution claire, fiable, facile à prendre en main et capable de produire des alertes compréhensibles.

Les principaux freins à l’adoption sont le coût, la complexité technique, le temps de déploiement et les contraintes de sécurité. Les segments de clientèle de OmniNet peuvent être classés ainsi : administrateurs réseau, responsables cybersécurité, PME, établissements de formation et environnements de test.

## 5. Offre et concurrence

Le marché comporte de nombreux concurrents directs et indirects. Parmi les concurrents directs, on trouve Nmap, Zabbix, Nagios, PRTG, SolarWinds, Auvik ou LogicMonitor.

Ces solutions proposent des fonctions de scan, de supervision et de monitoring, mais elles sont souvent plus lourdes, plus riches ou plus coûteuses que ce qu’un petit projet ou une petite structure recherche. Les concurrents indirects incluent Wireshark pour l’analyse de trafic, Suricata et Snort pour la détection d’intrusion, ainsi que certains outils de gestion des logs et des événements.

## 6. Positionnement de OmniNet

OmniNet se positionne comme un outil de supervision réseau orienté cybersécurité, à la fois pédagogique, fonctionnel et léger. Son positionnement est intermédiaire : plus complet qu’un simple scanner, mais plus simple qu’une plateforme de supervision industrielle ou qu’un SIEM complet.

Ce positionnement est cohérent avec un usage dans des réseaux de petite ou moyenne taille, dans des environnements d’apprentissage ou dans des contextes de démonstration. Le nom OmniNet renforce l’idée de surveillance continue, de rythme réseau et de vigilance permanente.

## 7. Proposition de valeur

La proposition de valeur d’OmniNet repose sur cinq éléments : simplicité d’usage, lecture rapide des résultats, alertes exploitables, exports JSON/CSV et modularité technique. L’utilisateur obtient une vision consolidée du réseau sans avoir à jongler entre plusieurs outils spécialisés.

La valeur ajoutée du projet est donc double : d’un côté, il apporte une réponse technique utile ; de l’autre, il reste suffisamment clair pour être présenté, démontré et compris facilement en soutenance.

## 8. Modèle économique

Le modèle économique le plus crédible pour OmniNet est un modèle hybride. Une première version gratuite open source peut fournir les fonctions de base, tandis qu’une version premium pourrait intégrer des fonctionnalités avancées : tableaux de bord enrichis, historiques plus longs, règles de détection plus poussées, intégrations externes ou notifications avancées.

En complément, OmniNet peut générer des revenus par des services associés : installation, personnalisation, formation, accompagnement et support technique. Pour un projet académique, l’objectif premier n’est pas la rentabilité immédiate, mais la démonstration d’un modèle cohérent et potentiellement monétisable.

## 9. Stratégie de commercialisation

La stratégie de commercialisation peut être pensée en trois phases :

1. Diffusion du prototype via GitHub, documentation claire et démonstration.
2. Amélioration fonctionnelle et diffusion comme outil open source ou version communautaire.
3. Packaging d’une version plus professionnelle, avec options premium ou prestations de service.

Les canaux de diffusion les plus réalistes sont GitHub, une release téléchargeable, une démonstration en présentation, puis éventuellement une diffusion en entreprise ou en établissement de formation.

## 10. Plan opérationnel

Le développement d’OmniNet repose sur une architecture backend en Python/FastAPI et une interface web HTML/CSS/JavaScript. Les modules clés sont : détection des équipements, scan réseau, identification des ports, récupération d’informations sur les services, observation du trafic, détection de comportements suspects, gestion des alertes et export des rapports.

Le plan opérationnel suit plusieurs étapes : conception, développement des API, intégration de l’interface, ajout des mécanismes de sécurité et d’alerting, phase de tests, documentation puis publication finale. Cette progression permet de garder un projet cohérent et démontrable.

## 11. Ressources nécessaires

Les ressources indispensables sont les compétences en Python, FastAPI, JavaScript et réseau, ainsi que le temps de développement, l’environnement de test, les bibliothèques de supervision et la documentation.

Si le projet évolue vers une solution plus avancée, il faudra aussi prévoir de la maintenance et de la gestion de versions. Dans un cadre de diffusion plus large, les ressources humaines deviennent importantes : support, intégration, mise à jour et amélioration continue.

## 12. Prévisions financières simplifiées

Dans le cadre étudiant, les coûts restent faibles : principalement du temps de développement, du test et de la documentation. Si OmniNet devient un produit, les coûts incluront l’hébergement, la maintenance, le support et les éventuels développements spécifiques pour les clients.

Les revenus potentiels reposent sur la vente de services, d’une version premium ou d’une offre entreprise. La logique financière du projet doit être présentée avec prudence : il s’agit d’abord d’un prototype à forte valeur démonstrative, pas d’un produit immédiatement rentable.

## 13. SWOT

| Forces | Faiblesses |
|---|---|
| Solution utile, cohérente et démontrable. | Périmètre limité, dépendance au réseau de test. |

| Opportunités | Menaces |
|---|---|
| Marché en croissance et besoin des PME. | Concurrence importante et exigences élevées en sécurité. |

## 14. Facteurs de réussite

La réussite d’OmniNet dépendra de la clarté de l’interface, de la pertinence des alertes, de la robustesse technique, de la qualité de la documentation et de la capacité à montrer une valeur concrète lors de la démonstration.

Un outil simple mais bien présenté sera souvent mieux perçu qu’une solution plus ambitieuse mais mal stabilisée. La valeur du projet repose aussi sur sa cohérence globale : un besoin réel, une solution adaptée, une architecture claire et une présentation professionnelle.

## 15. Conclusion générale

OmniNet est un projet crédible, utile et bien positionné sur un marché réel. Son business plan montre qu’il répond à un besoin concret de supervision et de cybersécurité, qu’il peut être diffusé simplement et qu’il possède une logique d’évolution réaliste.

Le SWOT n’a pas besoin d’être supprimé de l’étude de marché : au contraire, il peut être repris dans le business plan comme synthèse stratégique. L’étude de marché sert à comprendre le terrain ; le business plan sert à structurer l’action et le modèle de développement. Les deux sont complémentaires, pas redondants.
