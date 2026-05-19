#!/usr/bin/env bash
set -euo pipefail

mkdir -p backups

timestamp="$(date +%Y%m%d-%H%M%S)"
output="backups/cenabobot-${timestamp}.sql"

docker compose -f docker-compose.prod.yml --env-file .env.production exec -T db \
  pg_dump -U "${POSTGRES_USER:-cenabobot_user}" "${POSTGRES_DB:-cenabobot}" > "$output"

echo "Backup written to $output"
