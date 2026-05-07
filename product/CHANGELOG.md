# Changelog — Omninet

## [0.1.0] — 2026-05-07

### MVP SOC — Première version fonctionnelle

#### Backend
- Authentification JWT (admin/analyst) avec rate limiting
- Auth agent séparée (X-Agent-Token pour les endpoints)
- Ingestion d'événements de sécurité avec validation stricte
- Moteur d'alertes (4 règles : sévérité critique, flood, intrusion, ports sensibles)
- Cycle de vie des alertes (new → acknowledged → resolved)
- Corrélation d'événements répétitifs
- Discovery non destructif (ping, port, service)
- Inventaire d'actifs consolidé
- Exports CSV/JSON (événements, alertes, scans)
- KPI dashboard avec indicateurs temps réel
- Audit trail sécurisé (sanitization des secrets)
- Standardisation des réponses d'erreur API

#### Frontend
- Dashboard avec KPI et graphiques Canvas (barres + camembert)
- Page Alertes avec filtres, tri, pagination, auto-refresh
- Page Événements avec recherche et pagination
- Page Endpoints avec inventaire et filtres
- Page Scans avec formulaire de simulation
- Persistance du token JWT en sessionStorage
- Navigation entre pages sans re-login

#### Docker Lab
- Container `soc` : backend FastAPI (Python 3.12)
- Container `endpoint` : heartbeats simulés (3 hosts, métriques CPU/RAM/DISK)
- Container `attacker` : 4 scénarios d'attaque (port scan, brute force, flood, intrusion)
- Volume persistant pour la base de données
- Réseau isolé en bridge

#### CI/CD
- Pipeline GitHub Actions (test, lint, security)
- Pre-commit hooks (ruff, black)
- Bandit + pip-audit pour la sécurité

#### Tests
- 161 tests pytest
- Couverture : auth, events, alerts, audit, discovery, assets, correlation, reports, telemetry, health, frontend routes

#### Sécurité
- Utilisateur non-root dans le container Docker
- Sanitization des secrets dans les logs d'audit
- Rate limiting sur /auth/login
- Content Security Policy headers
- Validation stricte des cibles de scan (IP/FQDN uniquement)
