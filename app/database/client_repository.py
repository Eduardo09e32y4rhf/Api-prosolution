from app.database.db import get_connection
from passlib.hash import bcrypt

def init_clients_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password_hash TEXT,
            plan TEXT
        )
    """)

    # 👑 cria admin se não existir
    cursor.execute(
        "SELECT id FROM clients WHERE email = ?",
        ("admin@admin.com",)
    )

    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO clients (name, email, password_hash, plan)
            VALUES (?, ?, ?, ?)
        """, (
            "Administrador",
            "admin@admin.com",
            bcrypt.hash("123456"),
            "admin"
        ))

    conn.commit()
    conn.close()

from app.database.db import get_session
from app.database.models import Client
from app.auth.security import hash_password


def ensure_admin_exists():
    session = get_session()

    try:
        admin = session.query(Client).filter(
            Client.email == "admin@admin.com"
        ).first()

        if not admin:
            admin = Client(
                name="Administrador",
                email="admin@admin.com",
                password=hash_password("123456"),
                plan="admin",
                active=True
            )
            session.add(admin)
            session.commit()
            print("[BOOTSTRAP] Admin criado com sucesso")
        else:
            print("[BOOTSTRAP] Admin já existe")

    finally:
        session.close()

def create_admin_if_not_exists():
    db = SessionLocal()
    try:
        admin = db.query(Client).filter(Client.email == "admin@admin.com").first()

        if not admin:
            admin = Client(
                name="Administrador",
                email="admin@admin.com",
                password=get_password_hash("123456"),
                plan="admin"
            )
            db.add(admin)
            db.commit()
            print("✅ Admin criado com sucesso")
        else:
            print("ℹ️ Admin já existe")

    finally:
        db.close()