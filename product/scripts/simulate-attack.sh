#!/bin/sh
# Omninet — Attack simulation script
# Compatible Alpine (ash shell)

SOC_URL="http://soc:8000"
LOGIN_URL="$SOC_URL/auth/login"
EVENTS_URL="$SOC_URL/events"
ADMIN_USER="${OMNINET_ADMIN_USERNAME:-admin}"
ADMIN_PASS="${OMNINET_ADMIN_PASSWORD:-admin}"

JWT_TOKEN=""

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ATTACKER] $1"
}

rand() {
    min=$1
    max=$2
    range=$((max - min + 1))
    r=$(od -An -N2 -i /dev/urandom 2>/dev/null || echo "123")
    echo $((min + (r % range)))
}

wait_soc() {
    log "Waiting for SOC..."
    i=0
    while [ $i -lt 60 ]; do
        if curl -sf "$SOC_URL/health" > /dev/null 2>&1; then
            log "SOC ready"
            return 0
        fi
        sleep 2
        i=$((i + 2))
    done
    log "SOC not available after 60s, continuing anyway"
    return 1
}

login() {
    log "Getting JWT token..."
    resp=$(curl -s -X POST "$LOGIN_URL" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$ADMIN_USER\",\"password\":\"$ADMIN_PASS\"}" \
        --connect-timeout 5 --max-time 10 2>/dev/null)

    JWT_TOKEN=$(echo "$resp" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
    if [ -n "$JWT_TOKEN" ]; then
        log "Token OK"
        return 0
    fi
    log "Login failed"
    return 1
}

send_event() {
    etype=$1
    sev=$2
    src=$3
    desc=$4

    if [ -z "$JWT_TOKEN" ]; then
        login || return 1
    fi

    payload="{\"endpoint_id\":\"attacker-sim\",\"event_type\":\"$etype\",\"severity\":\"$sev\",\"source\":\"$src\",\"description\":\"$desc\"}"

    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$EVENTS_URL" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -d "$payload" \
        --connect-timeout 5 --max-time 10 2>/dev/null)

    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        log "OK $etype ($http_code)"
    else
        log "FAIL $etype (HTTP $http_code)"
        JWT_TOKEN=""
    fi
}

run_port_scan() {
    log "=== Port Scan ==="
    for port in 22 23 80 443 3389 8080; do
        send_event "port_scan" "high" "10.0.0.99" "Port scan on $port from 10.0.0.99"
        sleep $(rand 1 2)
    done
    sleep $(rand 2 4)
}

run_brute_force() {
    log "=== Brute Force ==="
    i=1
    count=$(rand 5 8)
    while [ $i -le $count ]; do
        send_event "auth_failure" "medium" "10.0.0.99" "Failed login attempt #$i from 10.0.0.99"
        i=$((i + 1))
        sleep $(rand 1 2)
    done
    sleep $(rand 2 4)
}

run_flood() {
    log "=== Traffic Flood ==="
    i=1
    count=$(rand 8 12)
    while [ $i -le $count ]; do
        pkts=$(rand 1000 9999)
        send_event "traffic_flood" "low" "10.0.0.99" "Flood ${pkts}pkts/s from 10.0.0.99"
        i=$((i + 1))
        sleep 1
    done
    sleep $(rand 2 4)
}

run_intrusion() {
    log "=== Intrusion ==="
    for desc in \
        "Unauthorized SSH access attempt" \
        "CVE-2025-1234 exploitation detected" \
        "Suspicious process /tmp/malware.bin" \
        "Privilege escalation attempt" \
        "CVE-2025-5678 exploit payload in HTTP" \
        "Reverse shell attempt blocked" \
        "Exploit kit fake update campaign"; do
        send_event "intrusion_attempt" "high" "10.0.0.99" "$desc"
        sleep $(rand 2 3)
    done
    sleep $(rand 2 4)
}

# Main
wait_soc
login

while true; do
    log "=== New attack cycle ==="
    run_port_scan
    run_brute_force
    run_flood
    run_intrusion
    log "Cycle done, sleep 60s..."
    sleep 60
done
