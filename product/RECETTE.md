# Omninet — Guide de Recette Opérateur

Ce document décrit pas-à-pas comment valider le fonctionnement d'Omninet (MVP SOC).

## Prérequis

- Docker + Docker Compose installés
- Terminal avec `curl` et `jq` (optionnel)
- Variables d'environnement définies dans `product/.env` (copier depuis `.env.example`)

### Lancement du lab

```bash
cd product/
cp .env.example .env
# Éditer .env si besoin (OMNINET_SECRET_KEY, OMNINET_AGENT_TOKEN)
docker compose up -d
```

Vérifier que le service SOC est sain :
```bash
curl -s http://localhost:8000/health | jq
# Attendu: {"status":"ok","service":"omninet-api"}
```

---

## Scénario 1 : Authentification

### 1.1 Login admin
```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq
```
✅ Attendu : `access_token` + `token_type: "bearer"`

### 1.2 Login analyst
```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"analyst","password":"analyst"}' | jq
```
✅ Attendu : token valide

### 1.3 Login invalide
```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"wrong"}' | jq
```
✅ Attendu : `401 Unauthorized`

### 1.4 Rate limiting (6 tentatives rapides)
Répéter 6 fois le login invalide.
✅ Attendu : la 6e tentative retourne `429 Too Many Requests`

---

## Scénario 2 : Accès protégé

### 2.1 Sans token
```bash
curl -s http://localhost:8000/auth/me | jq
```
✅ Attendu : `401`

### 2.2 Avec token admin
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

curl -s http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq
```
✅ Attendu : `{"username":"admin","role":"admin"}`

---

## Scénario 3 : Heartbeat Agent

```bash
AGENT_TOKEN="lab-agent-token-change-me" # ou valeur de .env

curl -s -X POST http://localhost:8000/telemetry/heartbeat \
  -H "X-Agent-Token: $AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"endpoint_id":"ep-001","hostname":"srv-web-01","ip_address":"10.0.1.10","os_info":"Ubuntu 22.04","agent_version":"1.0.0"}' | jq
```
✅ Attendu : `200`, `status: "accepted"`

### Vérification endpoints
```bash
curl -s http://localhost:8000/telemetry/endpoints \
  -H "Authorization: Bearer $TOKEN" | jq
```
✅ Attendu : liste contenant `ep-001` avec `status: "alive"`

---

## Scénario 4 : Événement + Alerte auto

### 4.1 Event low (pas d'alerte)
```bash
curl -s -X POST http://localhost:8000/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"endpoint_id":"ep-001","event_type":"info","severity":"low","source":"system","description":"Test info"}' | jq
```
✅ Attendu : `201`, `status: "ingested"`

### 4.2 Event critical (génère alerte auto)
```bash
curl -s -X POST http://localhost:8000/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"endpoint_id":"ep-001","event_type":"intrusion","severity":"critical","source":"ids","description":"Tentative d\\'intrusion détectée"}' | jq
```
✅ Attendu : `201`, `status: "ingested"`

### 4.3 Vérification alerte créée
```bash
curl -s "http://localhost:8000/alerts" \
  -H "Authorization: Bearer $TOKEN" | jq
```
✅ Attendu : au moins 1 alerte avec `severity: "critical"`, `status: "new"`

---

## Scénario 5 : Acknowledge Alerte (Admin uniquement)

Récupérer l'`alert_id` du scénario 4.
```bash
ALERT_ID="<alert_id>"

curl -s -X POST "http://localhost:8000/alerts/$ALERT_ID/acknowledge" \
  -H "Authorization: Bearer $TOKEN" | jq
```
✅ Attendu : `200`, `status: "acknowledged"`

### Test avec analyst (doit échouer)
```bash
ANALYST_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"analyst","password":"analyst"}' | jq -r '.access_token')

curl -s -X POST "http://localhost:8000/alerts/$ALERT_ID/acknowledge" \
  -H "Authorization: Bearer $ANALYST_TOKEN" | jq
```
✅ Attendu : `403 Forbidden`

---

## Scénario 6 : Scan Simulé (UI ou API)

```bash
curl -s -X POST http://localhost:8000/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"endpoint_id":"ep-001","event_type":"scan_port","severity":"medium","source":"ui-scan-tool","description":"Scan port 443","details":{"target":"10.0.1.10:443","simulated":true}}' | jq
```
✅ Attendu : `201`, event créé

---

## Scénario 7 : Audit Trail

```bash
curl -s "http://localhost:8000/audit" \
  -H "Authorization: Bearer $TOKEN" | jq
```
✅ Attendu : liste d'entrées avec actions `login`, `login_failed`, `login_rate_limited`, `agent_auth_success`, `acknowledge_alert`, etc.
✅ Vérifier qu'aucun mot de passe ou token n'apparaît dans `details`.

---

## Scénario 8 : Interface Web

Ouvrir dans un navigateur :
- `http://localhost:8000/ui` → Dashboard KPI
- `http://localhost:8000/ui/alerts` → Liste alertes + filtres + auto-refresh
- `http://localhost:8000/ui/events` → Liste événements + tri/recherche/pagination
- `http://localhost:8000/ui/scans` → Formulaire scan simulé

✅ Vérifier :
- Login fonctionne depuis l'UI
- Compteurs se mettent à jour
- Alertes affichées avec badges colorés
- Scan simulé crée un event visible

---

## Checklist de Validation Finale

| Test | Résultat |
|------|----------|
| Healthcheck OK | ☐ |
| Login admin/analyst OK | ☐ |
| Rate limiting login actif | ☐ |
| Heartbeat agent OK | ☐ |
| Event low → pas d'alerte | ☐ |
| Event critical → alerte auto | ☐ |
| Acknowledge admin OK | ☐ |
| Acknowledge analyst → 403 | ☐ |
| Audit trail présent | ☐ |
| Pas de secret dans audit | ☐ |
| UI accessible et fonctionnelle | ☐ |
| Tests backend : `pytest -q` → tous verts | ☐ |

---

## Nettoyage

```bash
cd product/
docker compose down
```
