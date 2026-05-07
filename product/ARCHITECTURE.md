# Architecture Omninet

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                      Navigateur Web                         │
│                   http://localhost:8000/ui                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (port 8000)                │
│                                                              │
│  ┌─────────┐  ┌────────┐  ┌─────────┐  ┌────────────────┐   │
│  │ Auth    │  │ Events │  │ Alerts  │  │ Discovery      │   │
│  │ JWT     │  │ CRUD   │  │ Engine  │  │ Scan           │   │
│  │ Agent   │  │        │  │ Rules   │  │ Assets         │   │
│  └─────────┘  └────────┘  └─────────┘  └────────────────┘   │
│                                                              │
│  ┌─────────┐  ┌────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Audit   │  │ Report │  │ Correl    │  │ Telemetry    │   │
│  │ Trail   │  │ KPI    │  │ Engine    │  │ Heartbeat    │   │
│  └─────────┘  └────────┘  └──────────┘  └──────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                  Stockage mémoire                     │    │
│  │  Events, Alerts, Audit, Endpoints, Assets, Scans     │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  SOC     │ │Endpoint  │ │ Attacker │
        │  Server  │ │ 3 hosts  │ │ 4 attk   │
        └──────────┘ └──────────┘ └──────────┘
              Réseau Docker bridge: omninet-lab
```

## Flux de données

### 1. Heartbeat
```
endpoint ──POST /telemetry/heartbeat──> soc
    │ X-Agent-Token                        │
    │ {endpoint_id, hostname, ip}          │ stockage mémoire
                                           ▼
                                GET /telemetry/endpoints
                                           │
                                    UI Dashboard
```

### 2. Événement → Alerte
```
attacker ──POST /events──> soc
    │ Bearer JWT             │
    │ {event_type, severity, │──> create_alert_from_event()
    │  source, description}  │       │
                                │     ├─ règle high_critical_severity
                                │     ├─ règle medium_flood
                                │     ├─ règle intrusion_type
                                │     └─ règle sensitive_ports
                                ▼
                          stockage mémoire
                                │
                          GET /alerts
                                │
                          UI Alertes
```

### 3. Scan → Découverte
```
UI ──POST /events (scan_ping/port/service)──> soc
    │ Bearer JWT                              │
    │ {details.target, ...}                   │──> evaluate_rules()
                                               │
                                         GET /discovery/scans
                                               │
                                         GET /assets
                                               │
                                         UI Scans / Assets
```

## Modules

### backend/app/

| Module | Rôle | Routes |
|--------|------|--------|
| `auth` | Authentification JWT + Agent | `/auth/login`, `/auth/me` |
| `events` | Ingestion d'événements | `/events` POST/GET |
| `alerts` | Moteur d'alertes + cycle de vie | `/alerts` POST/GET, `/alerts/{id}/acknowledge`, `/alerts/{id}/resolve` |
| `audit` | Traçabilité des actions | `/audit` GET |
| `telemetry` | Heartbeat des endpoints | `/telemetry/heartbeat`, `/telemetry/endpoints` |
| `discovery` | Scan non destructif | `/discovery/scan`, `/discovery/scans` |
| `assets` | Inventaire consolidé | `/assets` GET |
| `correlation` | Corrélation d'événements | `/correlation` |
| `reports` | KPI + exports | `/reports/kpi`, `/reports/events`, `/reports/alerts`, `/reports/scans` |
| `core` | Configuration, sécurité, réponses | `config.py`, `security.py`, `responses.py` |
| `database` | SQLAlchemy (prêt pour V2) | `base.py`, `models.py` |

## Décisions techniques

| Décision | Justification |
|----------|---------------|
| **Stockage mémoire** | Simplicité pour le MVP. Migration PostgreSQL en V2. |
| **Vanilla JS** | Pas de dépendances frontend lourdes. Canvas natif pour les graphes. |
| **JWT** | Solution d'auth légère sans base de données. |
| **Auth Agent séparée** | Permet aux endpoints de s'authentifier sans compte utilisateur. |
| **FastAPI** | Performance, auto-documentation Swagger, validation Pydantic. |
| **Docker bridge** | Isolation réseau entre les services du lab. |
