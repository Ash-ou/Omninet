---
name: fastapi-backend
description: Construire le backend FastAPI Omninet avec routes, schemas, services, tests et configuration.
compatibility: opencode
---

# Skill FastAPI Backend

## Structure cible

```text
product/backend/app/
├── main.py
├── core/
├── auth/
├── telemetry/
├── discovery/
├── assets/
├── alerts/
├── correlation/
├── reports/
└── audit/
```

## Organisation par module

Chaque module peut contenir :

```text
router.py
schemas.py
models.py
service.py
repository.py
```

## Règles

* Les routes doivent rester simples.
* Les services portent la logique métier.
* Les schemas Pydantic valident les entrées.
* Les modèles SQLAlchemy arrivent seulement quand la persistance est nécessaire.
* Les tests accompagnent chaque endpoint.
