from app.database.user_repository import create_table, create_user

create_table()
create_user("admin@prosolution.com", "admin123")
print("✅ Admin criado")
