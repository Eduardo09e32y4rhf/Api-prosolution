#!/bin/bash
echo "Rodando migrações do Alembic..."
alembic upgrade head

echo "Iniciando servidor FastAPI com Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 3000 --proxy-headers --forwarded-allow-ips='*'
