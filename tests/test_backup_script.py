"""Testa scripts/backup.sh de verdade: contra o Postgres de TEST_DATABASE_URL (pula sem ele)."""

import os
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "backup.sh"
TEST_DB = os.environ.get("TEST_DATABASE_URL", "")

needs_postgres = pytest.mark.skipif(
    not TEST_DB.startswith("postgresql") or not shutil.which("pg_dump") or not shutil.which("pg_restore"),
    reason="requer TEST_DATABASE_URL apontando para Postgres e pg_dump/pg_restore instalados",
)


def _pg_env(backup_dir: Path) -> dict[str, str]:
    url = urlparse(TEST_DB.replace("+asyncpg", ""))
    return {
        **os.environ,
        "PGHOST": url.hostname or "localhost",
        "PGPORT": str(url.port or 5432),
        "PGUSER": url.username or "postgres",
        "PGPASSWORD": url.password or "",
        "PGDATABASE": url.path.lstrip("/"),
        "BACKUP_DIR": str(backup_dir),
        "BACKUP_RETENTION_DAYS": "7",
    }


def test_next_run_is_within_one_day():
    for backup_time in ("00:00", "06:00", "08:30", "23:59"):
        out = subprocess.run(
            ["sh", str(SCRIPT), "--next"],
            env={**os.environ, "BACKUP_TIME": backup_time},
            capture_output=True,
            text=True,
            check=True,
        )
        assert 0 < int(out.stdout.strip()) <= 86400, backup_time


@needs_postgres
def test_backup_creates_restorable_dump_and_applies_retention(tmp_path: Path):
    env = _pg_env(tmp_path)
    db = env["PGDATABASE"]

    old = tmp_path / f"{db}-20200101-060000.dump"
    recent = tmp_path / f"{db}-20990101-060000.dump"
    unrelated = tmp_path / "outro-arquivo.dump"
    for f in (old, recent, unrelated):
        f.write_bytes(b"x")
    ten_days_ago = time.time() - 10 * 86400
    os.utime(old, (ten_days_ago, ten_days_ago))
    os.utime(unrelated, (ten_days_ago, ten_days_ago))

    result = subprocess.run(["sh", str(SCRIPT), "--once"], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

    dumps = sorted(p for p in tmp_path.glob(f"{db}-*.dump") if p not in (old, recent))
    assert len(dumps) == 1, result.stdout
    assert not old.exists(), "backup com mais de 7 dias deveria ter sido removido"
    assert recent.exists() and unrelated.exists()
    assert not list(tmp_path.glob("*.partial"))

    # O arquivo é um dump válido e contém as tabelas da aplicação
    listing = subprocess.run(["pg_restore", "--list", str(dumps[0])], capture_output=True, text=True, check=True)
    for table in ("users", "posts", "subscriptions", "brand_profiles"):
        assert f"TABLE public {table}" in listing.stdout


@needs_postgres
def test_backup_failure_returns_error_and_leaves_no_partial_file(tmp_path: Path):
    env = {**_pg_env(tmp_path), "PGDATABASE": "banco_que_nao_existe"}
    result = subprocess.run(["sh", str(SCRIPT), "--once"], env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert list(tmp_path.iterdir()) == []
