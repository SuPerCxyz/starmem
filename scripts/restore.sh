#!/usr/bin/env bash
set -euo pipefail

dump_file="${1:?usage: RESTORE_CONFIRM=YES scripts/restore.sh backups/<timestamp>/starmem.dump}"
backup_dir="$(dirname -- "$dump_file")"
attachment_file="$backup_dir/attachments.tar"
if [[ "${RESTORE_CONFIRM:-}" != "YES" ]]; then
  echo "Refusing destructive restore. Set RESTORE_CONFIRM=YES explicitly." >&2
  exit 2
fi
if [[ ! -f "$dump_file" ]]; then
  echo "Backup file not found: $dump_file" >&2
  exit 1
fi

docker compose exec -T postgres sh -c \
  'pg_restore --clean --if-exists --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < "$dump_file"
if [[ -f "$attachment_file" ]]; then
  docker compose exec -T api sh -c \
    'mkdir -p "$STARMEM_STORAGE_PATH" && find "$STARMEM_STORAGE_PATH" -mindepth 1 -delete && tar -C "$STARMEM_STORAGE_PATH" -xf -' \
    < "$attachment_file"
else
  echo "Attachment archive not found; database restored without attachment bytes." >&2
fi
printf 'database restored from %s\n' "$dump_file"
