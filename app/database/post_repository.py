import sqlite3
from datetime import datetime

DB_PATH = "app/database/database.db"


def init_posts_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            content TEXT,
            source TEXT,
            mode TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_post(client_id, content, source, mode):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO posts (client_id, content, source, mode, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (client_id, content, source, mode, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def list_posts(client_id, limit=50):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT content, source, mode, created_at
        FROM posts
        WHERE client_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (client_id, limit))

    rows = cursor.fetchall()
    conn.close()
    return rows
