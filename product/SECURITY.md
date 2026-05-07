# Omninet — Guide de Sécurité et Hardening

> Document de référence pour sécuriser l'infrastructure Omninet en production.

## Table des matières

- [Hardening Docker](#hardening-docker)
- [Configuration Reverse Proxy et TLS](#configuration-reverse-proxy-et-tls)
- [Recommandations Production](#recommandations-production)
- [Checklist Sécurité Pré-Production](#checklist-sécurité-pré-production)
- [Audit et Tests](#audit-et-tests)

---

## Hardening Docker

### 1. Utilisateur non-root (déjà implémenté)

Le backend FastAPI utilise déjà un utilisateur non-privilégié (`appuser`) :

```dockerfile
RUN useradd --create-home --shell /bin/sh appuser && \
    chown -R appuser:appuser /app
USER appuser
```

**Vérification :**
```bash
docker exec omninet-soc whoami
# Doit retourner: appuser
```

### 2. Filesystem en lecture seule (Read-only)

Pour limiter l'impact d'une compromission, montez le filesystem en lecture seule :

```yaml
services:
  soc:
    # ... autres paramètres ...
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=64M
      - /app/logs:noexec,nosuid,size=32M
```

**Note :** Nécessite que l'application n'écrive pas sur le filesystem (logs vers stdout, pas de fichiers temporaires).

### 3. Capabilities minimales (Drop all, add only required)

Supprimez toutes les capabilities Linux et n'ajoutez que le strict nécessaire :

```yaml
services:
  soc:
    # ... autres paramètres ...
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Si bind sur port < 1024 (pas notre cas avec 8000)
    # Pas de cap_add nécessaire pour le port 8000
```

Pour les containers `endpoint` et `attacker` (simulation) :
```yaml
  endpoint:
    image: alpine:latest
    cap_drop:
      - ALL
    cap_add:
      - NET_RAW  # Si besoin de ping/traceroute pour les tests
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=16M
```

### 4. Resource Limits (Prevention DoS)

Limitez l'utilisation des ressources :

```yaml
services:
  soc:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### 5. No new privileges

Empêchez l'élévation de privilèges :

```yaml
services:
  soc:
    security_opt:
      - no-new-privileges:true
```

### 6. Réseau isolé et restrictif

- Utilisez un réseau Docker isolé (déjà fait avec `omninet-lab`)
- Limitez les ports exposés
- Utilisez `internal: true` pour les containers qui n'ont pas besoin d'accès Internet

```yaml
networks:
  omninet-lab:
    driver: bridge
    internal: true  # Pas d'accès Internet pour les containers
```

---

## Configuration Reverse Proxy et TLS

### Option 1 : Nginx Reverse Proxy avec TLS

#### Architecture recommandée

```
Internet
   │
   ▼
[Nginx Reverse Proxy] (port 443)
   │  ├─ TLS Termination
   │  ├─ Rate Limiting
   │  └─ WAF (optionnel)
   │
   ▼
[Omninet SOC Backend] (port 8000, sur réseau interne uniquement)
```

#### Configuration Nginx (`nginx.conf`)

```nginx
events {
    worker_connections 1024;
}

http {
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=omninet:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=omninet_login:10m rate=2r/s;

    server {
        listen 443 ssl http2;
        server_name soc.omninet.local;  # Changer pour votre domaine

        # TLS Configuration (TLS 1.2 minimum)
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5:!3DES;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Proxy to backend
        location / {
            limit_req zone=omninet burst=20 nodelay;
            
            proxy_pass http://soc:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Rate limiting plus strict pour l'authentification
        location /auth/ {
            limit_req zone=omninet_login burst=5 nodelay;
            
            proxy_pass http://soc:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }
}
```

#### Docker Compose avec Nginx

Voir la section "Profil Production" dans `docker-compose.yml`.

### Option 2 : Traefik avec Let's Encrypt

#### Configuration Traefik (`traefik.yml`)

```yaml
version: "3.7"

services:
  traefik:
    image: traefik:v3.0
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@omninet.local"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"
    networks:
      - omninet-lab

  soc:
    build: ./backend
    expose:
      - "8000"
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.omninet.rule=Host(`soc.omninet.local`)"
      - "traefik.http.routers.omninet.entrypoints=websecure"
      - "traefik.http.routers.omninet.tls=true"
      - "traefik.http.routers.omninet.tls.certresolver=letsencrypt"
      - "traefik.http.services.omninet.loadbalancer.server.port=8000"
    networks:
      - omninet-lab
```

---

## Recommandations Production

### 1. Secrets forts (CRITIQUE)

**OMNINET_SECRET_KEY :**
```bash
# Générer une clé sécurisée (minimum 256 bits / 32 octets)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Ou avec openssl
openssl rand -base64 32
```

**OMNINET_AGENT_TOKEN :**
```bash
# Token pour l'authentification des agents endpoints
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

⚠️ **Ne jamais utiliser les valeurs par défaut en production !**

### 2. HTTPS obligatoire

- Configurez TLS avec des certificats valides (Let's Encrypt ou CA interne)
- Forcez la redirection HTTP → HTTPS
- Configurez HSTS (`Strict-Transport-Security`)
- Désactivez le mode debug : `OMNINET_DEBUG=false`

### 3. Rate Limiting

Implémentez le rate limiting au niveau :
- **Nginx/Traefik** : Protection réseau (voir configurations ci-dessus)
- **Application (FastAPI)** : Middleware de rate limiting par IP ou par utilisateur

Exemple middleware FastAPI (à implémenter dans le backend) :
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")  # 5 tentatives par minute par IP
async def login(request: Request, ...):
    ...
```

### 4. CORS restrictif

Configurez CORS pour n'autoriser que les origines connues :
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://soc.omninet.local"],  # Pas de "*" en production !
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### 5. Logs et Audit

- Centralisez les logs (ELK, Loki, ou syslog)
- Assurez-vous que les logs d'audit sont actifs (endpoint `/audit/logs`)
- Ne logguez jamais de secrets (tokens, mots de passe)
- Configurez la rotation des logs

### 6. Mises à jour de sécurité

```bash
# Mettre à jour régulièrement les images de base
docker pull python:3.14-slim
docker pull alpine:latest
make build  # Reconstruire avec les dernières mises à jour
```

### 7. Scan de vulnérabilités

```bash
# Scanner les images Docker avec Trivy
trivy image python:3.14-slim
trivy image omninet-soc:latest

# Ou avec Snyk
snyk container test omninet-soc:latest
```

---

## Checklist Sécurité Pré-Production

Utilisez cette checklist avant de déployer en production :

### Configuration
- [ ] `OMNINET_DEBUG=false` dans `.env`
- [ ] `OMNINET_SECRET_KEY` est une valeur forte (générée aléatoirement, min 32 chars)
- [ ] `OMNINET_AGENT_TOKEN` est configuré avec une valeur forte
- [ ] Mots de passe par défaut (`admin`/`analyst`) changés ou désactivés
- [ ] `.env` n'est pas commité (vérifiez `.gitignore`)

### Infrastructure Docker
- [ ] Containers exécutés avec utilisateur non-root (`appuser`)
- [ ] Filesystem en lecture seule activé (`read_only: true`)
- [ ] Capabilities réduites (`cap_drop: [ALL]`)
- [ ] Resource limits configurés (`deploy.resources`)
- [ ] `no-new-privileges` activé
- [ ] Réseau Docker isolé (pas d'accès Internet si non nécessaire)

### TLS et Réseau
- [ ] Certificat TLS valide (Let's Encrypt ou CA reconnue)
- [ ] TLS 1.2 minimum, préférer TLS 1.3
- [ ] HTTP redirigé vers HTTPS
- [ ] HSTS activé
- [ ] Ports exposés limités (éviter l'exposition directe du backend)
- [ ] Rate limiting configuré (Nginx/Traefik + Application)

### Application
- [ ] CORS configuré de manière restrictive (pas de `*`)
- [ ] Headers de sécurité présents (X-Frame-Options, X-XSS-Protection, etc.)
- [ ] JWT avec expiration courte (30 min max)
- [ ] Validation stricte des entrées (schemas Pydantic)
- [ ] Pas de secrets dans les logs
- [ ] Audit logs actifs

### Monitoring et Incident Response
- [ ] Logs centralisés configurés
- [ ] Alerting sur événements suspects configuré
- [ ] Backup de la configuration effectué
- [ ] Procédure d'incident documentée
- [ ] Contact sécurité défini

### Tests
- [ ] Tests de pénétration basiques effectués
- [ ] Scan de vulnérabilités passé
- [ ] Tests fonctionnels passés
- [ ] Test de charge effectué (vérifier rate limiting)

---

## Audit et Tests

### Test de sécurité rapide

```bash
# Vérifier que le backend ne tourne pas en root
docker exec omninet-soc whoami

# Vérifier les capabilities
docker inspect omninet-soc | grep -A 10 Cap

# Vérifier que le filesystem est read-only (si activé)
docker exec omninet-soc touch /test-write 2>&1 | grep -i "read-only"

# Tester HTTPS (remplacer par votre domaine)
curl -v https://soc.omninet.local/health

# Vérifier les headers de sécurité
curl -I https://soc.omninet.local

# Test de force brute sur /auth/login (doit être limité)
for i in {1..10}; do curl -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"wrong"}' 2>/dev/null; done
```

### Outils recommandés

- **Trivy** : Scan de vulnérabilités des images Docker
- **OWASP ZAP** : Tests de pénétration automatisés
- **Nmap** : Audit réseau
- **SSL Labs** : Test de configuration TLS (https://www.ssllabs.com/ssltest/)

---

## Contact et Signalement

Pour signaler une vulnérabilité de sécurité, contactez : security@omninet.local

**Ne créez pas d'issue publique pour les vulnérabilités de sécurité.**

---

*Document version : 1.0 — Mis à jour le 2026-05-07*
