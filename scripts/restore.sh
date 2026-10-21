#!/bin/sh
# Restaura um backup no banco do docker-compose (APAGA os dados atuais do banco).
# uso: ./scripts/restore.sh backups/prosolution-AAAAMMDD-HHMMSS.dump
set -eu

[ $# -eq 1 ] || { echo "uso: $0 caminho/do/backup.dump" >&2; exit 1; }
[ -f "$1" ] || { echo "arquivo não encontrado: $1" >&2; exit 1; }

printf "Isto vai SUBSTITUIR o banco atual pelo conteúdo de %s. Digite 'restaurar' para continuar: " "$1"
read -r answer
[ "$answer" = "restaurar" ] || { echo "cancelado"; exit 1; }

docker compose stop web worker
docker compose exec -T db sh -c 'pg_restore --clean --if-exists --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < "$1"
docker compose start web worker
echo "Restauração concluída."
