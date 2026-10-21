#!/bin/bash
set -euo pipefail

echo "Rodando migrações do Alembic..."
alembic upgrade head

echo "Iniciando servidor FastAPI com Uvicorn..."
# Só confie em X-Forwarded-For vindo do seu proxy reverso; com '*' qualquer cliente
# poderia falsificar o IP e escapar do rate limit.
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-3000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --proxy-headers \
    --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-127.0.0.1}"
