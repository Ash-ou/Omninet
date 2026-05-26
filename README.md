# Omninet

**Plateforme de cybersurveillance réseau orientée SOC.**

Omninet est un laboratoire SOC (Security Operations Center) complet permettant la détection, la corrélation et le suivi d'événements de sécurité. Déployable en quelques secondes via Docker, il simule un environnement de supervision avec endpoints, attaquants et console d'analyse.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 Réseau: omninet-lab             │
│                                                 │
│  ┌──────────────┐   ┌──────────┐  ┌──────────┐  │
│  │     soc      │   │ endpoint │  │ attacker │  │
│  │  (FastAPI)   │   │ (alpine) │  │ (alpine) │  │
│  │   :8000      │   │heartbeat │  │  attaque │  │
│  │              │   │ 15-30s   │  │  cycle   │  │
│  └──────┬───────┘   └──────────┘  └──────────┘  │
│         │                                       │
└─────────┼───────────────────────────────────────┘
          │
          ▼
     localhost:8000
          │
     ┌────┴────┐
     │   UI    │   http://localhost:8000/ui
     │   API   │   http://localhost:8000/docs
     └─────────┘
```

### Services

| Service    | Rôle                            | Technologie       |
|------------|---------------------------------|-------------------|
| `soc`      | Backend API REST + UI           | FastAPI (Python)  |
| `endpoint` | Simulation heartbeats (3 hosts) | Alpine + curl     |
| `attacker` | Simulation d'attaques (4 types) | Alpine + curl     |

---

## Fonctionnalités

- **Authentification** JWT (admin/analyst) + Agent Token
- **Dashboard** avec KPI et graphiques Canvas
- **Alertes** avec cycle de vie (new → acknowledged → resolved)
- **Événements** avec tri, recherche, pagination, auto-refresh
- **Détection** : 4 règles (sévérité critique, flood, intrusion, ports sensibles)
- **Corrélation** d'événements répétitifs
- **Heartbeats** temps réel des endpoints
- **Scan simulateur** (ping, port, service)
- **Discovery** non destructif avec inventaire d'actifs
- **Exports** CSV/JSON
- **Audit trail** sécurisé (sanitization des secrets)
- **Rate limiting** sur l'authentification
- **Simulation d'attaques** automatique (4 scénarios)

---

## Prérequis

- Docker >= 24.0
- Docker Compose >= 2.20
- Make (optionnel)

---

## Installation rapide

```bash
# 1. Cloner le dépôt
git clone <url-du-repo> && cd omninet

# 2. Configurer l'environnement
cd product/
cp .env.example .env

# 3. Lancer le lab
make up
```

Le SOC est accessible sur `http://localhost:8000`.

---

## Premier pas

| Rôle     | Identifiants            |
|----------|-------------------------|
| Admin    | `admin` / `admin`       |
| Analyste | `analyst` / `analyst`   |

1. Ouvrir `http://localhost:8000/ui` → login admin
2. Dashboard → KPI en direct
3. Après 30-60s : événements + alertes apparaissent automatiquement
4. Explorer les pages : Alertes, Événements, Endpoints, Scans

---

## Interfaces

| Interface | URL                                   |
|-----------|---------------------------------------|
| Dashboard | `http://localhost:8000/ui`            |
| Alertes   | `http://localhost:8000/ui/alerts`     |
| Événements| `http://localhost:8000/ui/events`     |
| Endpoints | `http://localhost:8000/ui/endpoints`  |
| Scans     | `http://localhost:8000/ui/scans`      |
| API docs  | `http://localhost:8000/docs`          |

---

## Simulation automatique

Les containers `endpoint` et `attacker` génèrent du trafic automatiquement :

| Container  | Action                              | Fréquence          |
|------------|-------------------------------------|--------------------|
| `endpoint` | Heartbeats CPU/RAM/DISK (3 hosts)   | Toutes les 30s     |
| `attacker` | Port scan + Brute force + Flood + Intrusion | Cycle 60s  |

---

## Stack technique

| Composant | Technologie                        |
|-----------|------------------------------------|
| Backend   | Python 3.12, FastAPI               |
| Auth      | JWT (python-jose), bcrypt          |
| Frontend  | HTML5, CSS3, JavaScript (vanilla)  |
| Graphes   | Canvas API                         |
| Conteneur | Docker, Docker Compose             |
| CI/CD     | GitHub Actions                     |

---

## Documentation

| Doc                   | Description                                    |
|-----------------------|------------------------------------------------|
| `product/README.md`   | Guide détaillé du lab SOC                      |
| `product/RECETTE.md`  | Scénarios de test pas à pas                    |
| `product/SECURITY.md` | Hardening Docker/TLS, checklist production     |
| `product/ARCHITECTURE.md` | Architecture technique et flux de données  |

---

## Commandes utiles

```bash
make up        # Lancer le lab
make down      # Arrêter le lab
make logs      # Logs du SOC
make test      # Tests pytest
make shell     # Shell dans le container SOC
make status    # État des services
make build     # Reconstruire les images
make clean     # Nettoyage complet
```

---

## Licence

Projet à but pédagogique — lab SOC.
