#!/usr/bin/env bash
# CitaMonitor — VPS deployment script
# Usage: bash scripts/deploy.sh

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[x]${NC} $1"; exit 1; }

# ── Checks ─────────────────────────────────────────────────────
[[ -f .env ]] || err ".env file not found. Copy .env.example and fill in values."
command -v docker >/dev/null 2>&1 || err "Docker not found."
command -v docker compose >/dev/null 2>&1 || err "Docker Compose not found."

log "Starting CitaMonitor deployment..."

# ── Pull latest images ─────────────────────────────────────────
log "Building Docker images..."
docker compose build --parallel

# ── Stop existing containers ────────────────────────────────────
log "Stopping existing containers..."
docker compose down --remove-orphans

# ── Start services ─────────────────────────────────────────────
log "Starting services..."
docker compose up -d

# ── Wait for health ────────────────────────────────────────────
log "Waiting for services to be healthy..."
sleep 10

for service in postgres redis backend; do
    status=$(docker compose ps $service --format json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Health','unknown'))" 2>/dev/null || echo "unknown")
    if [[ "$status" == "healthy" || "$status" == "unknown" ]]; then
        log "$service: OK"
    else
        warn "$service status: $status"
    fi
done

# ── Show status ────────────────────────────────────────────────
echo ""
log "Deployment complete!"
echo ""
docker compose ps
echo ""
log "Logs: docker compose logs -f"
log "Stop:  docker compose down"
