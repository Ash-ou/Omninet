#!/bin/sh
# Omninet — Heartbeat script for simulated endpoints
# Compatible Alpine (ash shell)

SOC_URL="http://soc:8000/telemetry/heartbeat"
AGENT_TOKEN="${OMNINET_AGENT_TOKEN:-change-me-agent-token}"
INTERVAL_MIN=15
INTERVAL_MAX=30

ENDPOINTS="endpoint-01 endpoint-02 endpoint-03"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

rand_range() {
    min=$1
    max=$2
    range=$((max - min + 1))
    rand=$(od -An -N2 -i /dev/urandom 2>/dev/null || echo "$(date +%N | sed 's/^0*//')")
    rand=${rand:-$$}
    echo $((min + (rand % range)))
}

send_heartbeat() {
    endpoint_id=$1

    hostname="${endpoint_id}-vm"
    case "$endpoint_id" in
        *-01) ip_address="10.0.0.1" ;;
        *-02) ip_address="10.0.0.2" ;;
        *-03) ip_address="10.0.0.3" ;;
        *) ip_address="10.0.0.10" ;;
    esac

    payload=$(cat <<EOF
{
    "endpoint_id": "$endpoint_id",
    "hostname": "$hostname",
    "ip_address": "$ip_address",
    "os_info": "Alpine Linux 3.20",
    "agent_version": "1.0.0"
}
EOF
)

    log "Heartbeat: $endpoint_id ($ip_address)"

    max_retries=3
    retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        http_code=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST "$SOC_URL" \
            -H "Content-Type: application/json" \
            -H "X-Agent-Token: $AGENT_TOKEN" \
            -d "$payload" \
            --connect-timeout 5 \
            --max-time 10 2>/dev/null)

        if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
            log "OK $endpoint_id (HTTP $http_code)"
            return 0
        else
            retry_count=$((retry_count + 1))
            log "RETRY $endpoint_id (HTTP $http_code, $retry_count/$max_retries)"
            sleep 2
        fi
    done

    log "FAIL $endpoint_id after $max_retries retries"
    return 1
}

main_loop() {
    log "Starting heartbeat service for: $ENDPOINTS"

    while true; do
        for ep in $ENDPOINTS; do
            send_heartbeat "$ep"
            sleep 2
        done

        interval=$(rand_range $INTERVAL_MIN $INTERVAL_MAX)
        log "Sleep ${interval}s..."
        sleep "$interval"
    done
}

trap 'log "Stopping heartbeat"; exit 0' TERM INT

log "Waiting for SOC..."
max_wait=60
wait_count=0
while [ $wait_count -lt $max_wait ]; do
    if curl -sf http://soc:8000/health > /dev/null 2>&1; then
        log "SOC ready"
        break
    fi
    sleep 2
    wait_count=$((wait_count + 2))
done

main_loop
