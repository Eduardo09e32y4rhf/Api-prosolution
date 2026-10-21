"""Roda o Alembic de verdade (processo separado) sobre um SQLite temporário."""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def alembic(db_path: Path, *args: str) -> None:
    env = {**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{db_path}"}
    result = subprocess.run([sys.executable, "-m", "alembic", *args], cwd=ROOT, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def columns(db_path: Path, table: str) -> set[str]:
    with sqlite3.connect(db_path) as conn:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}  # noqa: S608


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "mig.db"


def test_image_key_migration_converts_posts_and_roundtrips(db_path: Path):
    alembic(db_path, "upgrade", "7b3e9f1c2d4a")
    assert "image_url" in columns(db_path, "posts")

    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO users (email, password_hash, is_active) VALUES ('a@a.com', 'h', 1)")
        for title, status in (("agendado", "scheduled"), ("rascunho", "draft"), ("publicado", "published")):
            conn.execute(
                "INSERT INTO posts (user_id, title, content, status, image_url) VALUES (1, ?, 'x', ?, 'https://externo/a.jpg')",
                (title, status),
            )

    alembic(db_path, "upgrade", "head")
    cols = columns(db_path, "posts")
    assert "image_key" in cols and "image_url" not in cols
    with sqlite3.connect(db_path) as conn:
        statuses = dict(conn.execute("SELECT title, status FROM posts"))
    # Agendado dependia de URL externa (descartada): volta a rascunho. Os demais ficam como estavam.
    assert statuses == {"agendado": "draft", "rascunho": "draft", "publicado": "published"}

    alembic(db_path, "downgrade", "7b3e9f1c2d4a")
    assert "image_url" in columns(db_path, "posts") and "image_key" not in columns(db_path, "posts")
    alembic(db_path, "upgrade", "head")
    alembic(db_path, "check")


def test_models_and_migrations_are_in_sync(db_path: Path):
    alembic(db_path, "upgrade", "head")
    alembic(db_path, "check")
