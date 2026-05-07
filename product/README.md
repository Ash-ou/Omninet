# Omninet — Lab SOC

Plateforme de cybersurveillance réseau orientée SOC.

## Prérequis

- **Docker** >= 24.0
- **Docker Compose** >= 2.20 (plugin Docker)
- **Make** (optionnel, mais recommandé)

## Installation rapide

```bash
# 1. Se placer dans le répertoire product/
cd product/

# 2. Créer le fichier .env depuis le template
cp .env.example .env

# 3. Modifier .env avec vos valeurs (surtout OMNINET_SECRET_KEY)
#    NE JAMAIS commiter le fichier .env

# 4. Lancer le lab
make up
```

## Architecture du lab

```
┌─────────────────────────────────────────────┐
│              Réseau: omninet-lab             │
│                                             │
│  ┌──────────┐   ┌──────────┐  ┌──────────┐ │
│  │   soc    │   │ endpoint │  │ attacker │ │
│  │ (FastAPI)│   │ (alpine) │  │ (alpine) │ │
│  │ :8000    │   │          │  │          │ │
│  └────┬─────┘   └──────────┘  └──────────┘ │
│       │                                     │
└───────┼─────────────────────────────────────┘
        │
        ▼
   localhost:8000
```

| Service    | Rôle                          | Image            |
|------------|-------------------------------|------------------|
| `soc`      | Backend FastAPI (API SOC)     | Build local      |
| `endpoint` | Endpoint simulé (heartbeats)  | alpine:latest    |
| `attacker` | Container d'attaque simulée   | alpine:latest    |

## Endpoints API

| Méthode | Chemin                  | Description                  | Auth |
|---------|-------------------------|------------------------------|------|
| GET     | `/`                     | Info application             | Non  |
| GET     | `/health`               | Healthcheck                  | Non  |
| POST    | `/auth/login`           | Obtenir un token JWT         | Non  |
| POST    | `/auth/register`        | Créer un utilisateur         | Non  |
| GET     | `/telemetry/heartbeat`  | Heartbeat endpoint           | Oui  |
| POST    | `/events`               | Créer un événement           | Oui  |
| GET     | `/events`               | Lister les événements        | Oui  |
| POST    | `/alerts`               | Créer une alerte             | Oui  |
| GET     | `/alerts`               | Lister les alertes           | Oui  |
| GET     | `/alerts/{id}/acknowledge` | Acquitter une alerte      | Admin |
| GET     | `/alerts/{id}/resolve`  | Résoudre une alerte          | Admin |
| GET     | `/telemetry/endpoints`  | Lister les endpoints         | Oui  |
| POST    | `/discovery/scan`       | Lancer un scan               | Oui  |
| GET     | `/discovery/scans`      | Résultats des scans          | Oui  |
| GET     | `/assets`               | Inventaire des assets        | Oui  |
| GET     | `/audit`                | Logs d'audit                 | Oui  |
| GET     | `/reports/kpi`          | KPI dashboard                | Oui  |
| GET     | `/reports/events`       | Export événements (CSV/JSON) | Oui  |
| GET     | `/reports/alerts`       | Export alertes (CSV/JSON)    | Oui  |
| GET     | `/reports/scans`        | Export scans (CSV/JSON)      | Oui  |

## Commandes utiles

```bash
make up        # Lancer le lab
make down      # Arrêter le lab
make logs      # Logs du serveur SOC
make test      # Exécuter les tests
make shell     # Shell dans le container SOC
make status    # État des services
make build     # Reconstruire les images
make clean     # Nettoyage complet (containers + images + volumes)
make help      # Afficher l'aide
```

## Variables d'environnement

Voir `.env.example` pour la liste complète.

| Variable                             | Description                | Défaut                    |
|--------------------------------------|----------------------------|---------------------------|
| `OMNINET_APP_NAME`                   | Nom de l'application       | `Omninet`                 |
| `OMNINET_APP_VERSION`                | Version                    | `0.1.0`                   |
| `OMNINET_DEBUG`                      | Mode debug                 | `false`                   |
| `OMNINET_SECRET_KEY`                 | Clé de signature JWT       | `change-me-in-production` |
| `OMNINET_ALGORITHM`                  | Algorithme JWT             | `HS256`                   |
| `OMNINET_ACCESS_TOKEN_EXPIRE_MINUTES`| Expiration token (minutes) | `30`                      |
| `OMNINET_ADMIN_USERNAME`             | Login admin                | `admin`                   |
| `OMNINET_ADMIN_PASSWORD`             | Mot de passe admin         | `admin`                   |
| `OMNINET_ANALYST_USERNAME`           | Login analyste             | `analyst`                 |
| `OMNINET_ANALYST_PASSWORD`           | Mot de passe analyste      | `analyst`                 |

## Vérification

```bash
# Vérifier que le SOC est opérationnel
curl http://localhost:8000/health

# Vérifier l'état des services
make status

# Tester l'authentification
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

## Sécurité

> ⚠️ **Important** : Ce lab est configuré pour le développement et les tests. Pour un déploiement en production, consultez le [Guide de Sécurité](SECURITY.md).

### Mesures de sécurité implémentées (Lab)

- Le backend tourne en utilisateur non-root (`appuser`) dans le container.
- Le réseau Docker `omninet-lab` est isolé (bridge).
- Aucun secret réel n'est commité dans le dépôt.
- Le fichier `.env` est ignoré par Git (voir `.gitignore` à la racine).

### Hardening recommandé pour la production

1. **Docker** :
   - Activer le filesystem en lecture seule (`read_only: true`)
   - Supprimer toutes les capabilities Linux (`cap_drop: ALL`)
   - Limiter les ressources (CPU, mémoire)
   - Activer `no-new-privileges`

2. **Réseau** :
   - Utiliser un reverse proxy (Nginx/Traefik) avec TLS
   - Ne pas exposer directement le backend FastAPI
   - Configurer le rate limiting

3. **Application** :
   - Générer un `OMNINET_SECRET_KEY` fort (min 32 caractères aléatoires)
   - Configurer `OMNINET_AGENT_TOKEN` pour les agents endpoints
   - Désactiver le mode debug (`OMNINET_DEBUG=false`)
   - Changer les mots de passe par défaut (`admin`/`analyst`)

### Documentation sécurité

- [SECURITY.md](SECURITY.md) — Guide complet de hardening, configuration TLS, et checklist pré-production
- [.env.example](.env.example) — Template des variables d'environnement (jamais de secrets réels)

### Audit de sécurité

```bash
# Vérifier que le backend ne tourne pas en root
docker exec omninet-soc whoami

# Scanner les vulnérabilités (nécessite trivy)
trivy image python:3.14-slim
trivy image omninet-soc:latest
```

Pour plus de détails, voir [SECURITY.md](SECURITY.md).
