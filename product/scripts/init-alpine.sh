#!/bin/sh

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INIT] $1"
}

log "Démarrage de l'initialisation Alpine..."

# Mise à jour des dépôts et installation des paquets
log "Installation de curl et awk..."
apk update -q 2>/dev/null || true
apk add --no-cache curl coreutils 2>/dev/null || apk add --no-cache curl 2>/dev/null || true

if command -v curl > /dev/null 2>&1; then
    log "curl OK"
else
    log "WARNING: curl non installe, le script risk de ne pas fonctionner"
fi

log "Initialisation terminee."

if [ $# -gt 0 ]; then
    log "Lancement du script: $1"
    exec sh "$@"
else
    exec sleep infinity
fi
