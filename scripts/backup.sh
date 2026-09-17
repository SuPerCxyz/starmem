#!/usr/bin/env bash
set -euo pipefail

backup_dir="${1:-backups/$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$backup_dir"
dump_file="$backup_dir/starmem.dump"
attachment_file="$backup_dir/attachments.tar"

docker compose exec -T postgres sh -c \
  'pg_dump -Fc --no-owner -U "$POSTGRES_USER" "$POSTGRES_DB"' > "$dump_file"

docker compose exec -T api sh -c \
  'mkdir -p "$STARMEM_STORAGE_PATH" && tar -C "$STARMEM_STORAGE_PATH" -cf - .' > "$attachment_file"

if [[ -f .env ]]; then
  sed -E 's/^(STARMEM_[A-Z0-9_]*(KEY|SECRET|PASSWORD)=).*/\1<redacted>/' .env \
    > "$backup_dir/env.redacted"
fi

printf '%s\n' \
  'StarMem backup' \
  "Database: $dump_file" \
  "Attachments: $attachment_file" \
  'Embedding vectors are rebuildable; Raw Entry and Memory provenance are in the database dump.' \
  'The environment file is redacted. Restore secrets separately through the runtime environment.' \
  > "$backup_dir/README.txt"
printf 'backup written to %s\n' "$backup_dir"
