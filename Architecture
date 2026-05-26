# Architecture — Omninet

> Outil de supervision et d'analyse réseau orienté cybersécurité.

---

## 1. Objectif

Omninet est conçu pour mapper un réseau informatique, détecter les équipements connectés et scanner des plages d'adresses IP.

Le système permet :
- L'identification des ports ouverts et la récupération d'informations sur les services
- L'observation du trafic réseau en temps réel
- La détection d'événements suspects et la génération d'alertes
- L'export de rapports fiables et exploitables

---

## 2. Stack technique

| Couche | Technologie | Rôle |
|---|---|---|
| **Backend** | Python + FastAPI | API REST, logique métier, moteur d'analyse |
| **Frontend** | HTML / CSS / JavaScript | Interface web, tableau de bord |
| **UI Framework** | Bootstrap ou Tailwind CSS | Mise en page et composants visuels |
| **Persistance** | SQLite | Configuration, historique des scans, journal des alertes |
| **Export** | JSON / CSV | Formatage et export des résultats d'analyse |

---

## 3. Principes d'architecture

### Séparation des responsabilités
Le moteur d'analyse réseau (backend) est strictement découplé de l'interface d'affichage (frontend).

### Sécurité dès la conception
La sécurité est intégrée nativement dans l'architecture, dès la phase de conception et tout au long de la réalisation.

### Modularité et légèreté
La solution est pensée pour être déployée localement sur un réseau interne, de manière simple et sans dépendances lourdes.

### Exploitabilité des données
L'architecture garantit la production de résultats directement exploitables : logs structurés, alertes visuelles et rapports exportables.

---

## 4. Composants logiques

```
┌─────────────────────────────────────────────────────────┐
│                     Interface Web                       │
│              (Tableau de bord / Frontend)               │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / REST
┌────────────────────────▼────────────────────────────────┐
│                      API Core                           │
│              (FastAPI — endpoints sécurisés)            │
└───────┬──────────────┬───────────────────────┬──────────┘
        │              │                       │
┌───────▼──────┐ ┌─────▼──────────┐ ┌─────────▼────────┐
│  Module de   │ │ Sonde de       │ │ Moteur de        │
│  Découverte  │ │ Trafic         │ │ Détection        │
│  (scan IP/   │ │ (capture       │ │ (règles,         │
│   ports)     │ │  paquets)      │ │  alertes)        │
└──────────────┘ └────────────────┘ └──────────────────┘
                         │
              ┌──────────▼──────────┐
              │    Base SQLite      │
              │ (événements, scans, │
              │  configuration)     │
              └─────────────────────┘
```

| Composant | Description |
|---|---|
| **Module de Découverte** | Scan actif des adresses IP, identification des ports et services exposés |
| **Sonde de Trafic** | Écoute passive des interfaces réseau, extraction des métadonnées de paquets |
| **Moteur de Détection** | Analyse comportementale, identification des anomalies, génération d'alertes |
| **API Core** | Routeur FastAPI exposant les endpoints sécurisés au frontend |
| **Interface de Restitution** | Tableau de bord web — cartographie, alertes, export |

---

## 5. Flux de données

```
Réseau
  │
  ▼
[Acquisition] ──→ Capture de trames + requêtes de scan (bibliothèques Python)
  │
  ▼
[Traitement] ───→ Nettoyage, détection d'anomalies, structuration (backend)
  │
  ▼
[Stockage] ─────→ Sauvegarde des événements et de l'état réseau (SQLite)
  │
  ▼
[Restitution] ──→ Polling API → rafraîchissement du frontend → affichage alertes
```

---

## 6. Sécurité applicative

### Authentification
L'accès à l'interface web et aux endpoints de l'API est protégé par un système d'authentification, empêchant tout utilisateur non autorisé de lancer des scans réseau.

### Validation des entrées
Toutes les données saisies par l'utilisateur (notamment les plages IP) sont strictement validées par FastAPI pour prévenir les injections de commandes système.

### Gestion des privilèges
Le backend s'exécute avec les droits minimums nécessaires pour capturer le trafic et scanner les ports, limitant l'impact d'une éventuelle compromission.

---

## 7. Déploiement

### Conteneurisation (Docker)
L'application est packagée sous forme de conteneurs Docker, garantissant un comportement identique sur n'importe quel environnement (backend, frontend, dépendances réseau).

### On-premise
L'installation se fait localement ou sur un serveur interne, assurant que les données d'analyse réseau restent dans le périmètre de l'organisation.

```
┌────────────────────────────────────────┐
│           Hôte / Serveur interne       │
│                                        │
│  ┌──────────────┐  ┌────────────────┐  │
│  │  Container   │  │   Container    │  │
│  │   Backend    │  │   Frontend     │  │
│  │  (FastAPI)   │  │  (Nginx/HTTP)  │  │
│  └──────┬───────┘  └───────┬────────┘  │
│         │                  │           │
│  ┌──────▼──────────────────▼────────┐  │
│  │         Volume SQLite            │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```
