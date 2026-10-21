#!/bin/sh
# Backup diário do Postgres com retenção. Roda no serviço `backup` do docker-compose.
# Também pode ser executado à mão (variáveis PG* padrão do libpq):
#   PGHOST=... PGUSER=... PGPASSWORD=... PGDATABASE=... ./scripts/backup.sh --once
set -eu

BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
# Horário (UTC) do backup diário, formato HH:MM
BACKUP_TIME="${BACKUP_TIME:-06:00}"

run_backup() {
    mkdir -p "$BACKUP_DIR"
    stamp="$(date -u +%Y%m%d-%H%M%S)"
    target="$BACKUP_DIR/${PGDATABASE}-${stamp}.dump"
    # Formato custom (-Fc): comprimido e restaurável com pg_restore
    pg_dump -Fc --no-owner --file="$target.partial" || { rm -f "$target.partial"; return 1; }
    mv "$target.partial" "$target" || return 1
    echo "[backup] $(date -u +%FT%TZ) gerado $target ($(du -h "$target" | cut -f1))"
    find "$BACKUP_DIR" -name "${PGDATABASE}-*.dump" -type f -mtime +"$((RETENTION_DAYS - 1))" -print -delete \
        | sed 's/^/[backup] removido (retenção): /'
}

strip_zeros() {
    v=$(echo "$1" | sed 's/^0*//')
    echo "${v:-0}"
}

# Segundos até o próximo BACKUP_TIME (sem `date -d`, que varia entre GNU e BusyBox)
seconds_until_next() {
    target=$(( $(strip_zeros "${BACKUP_TIME%%:*}") * 3600 + $(strip_zeros "${BACKUP_TIME##*:}") * 60 ))
    now=$(( $(strip_zeros "$(date -u +%H)") * 3600 + $(strip_zeros "$(date -u +%M)") * 60 + $(strip_zeros "$(date -u +%S)") ))
    wait=$(( target - now ))
    [ "$wait" -le 0 ] && wait=$(( wait + 86400 ))
    echo "$wait"
}

case "${1:-}" in
    --once)
        run_backup
        exit 0
        ;;
    --next)
        seconds_until_next
        exit 0
        ;;
esac

echo "[backup] agendado diariamente às $BACKUP_TIME UTC, retenção de $RETENTION_DAYS dias"
run_backup
while true; do
    sleep "$(seconds_until_next)"
    run_backup || echo "[backup] ERRO: backup falhou" >&2
done
