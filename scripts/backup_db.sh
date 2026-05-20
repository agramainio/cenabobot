#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE="${ENV_FILE:-.env.production}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

DB_USER="${POSTGRES_USER:-cenabobot_user}"
DB_NAME="${POSTGRES_DB:-cenabobot}"

mkdir -p backups

timestamp="$(date +%Y%m%d-%H%M%S)"
output="backups/cenabobot-${timestamp}.sql"

docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" exec -T db \
  pg_dump -U "$DB_USER" "$DB_NAME" > "$output"

echo "Backup written to $output"
