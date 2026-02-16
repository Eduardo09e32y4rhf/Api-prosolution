import sqlite3

DB_PATH = "app/database/database.db"


def init_automation_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS automation_config (
            id INTEGER PRIMARY KEY,
            enabled BOOLEAN,
            times TEXT
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO automation_config (id, enabled, times)
        VALUES (1, 0, '')
    """)

    conn.commit()
    conn.close()


def save_config(enabled, times):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE automation_config
        SET enabled = ?, times = ?
        WHERE id = 1
    """, (enabled, ",".join(times)))

    conn.commit()
    conn.close()
