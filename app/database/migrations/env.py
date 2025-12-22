from app.database.session import engine
from app.database.base import Base
target_metadata = Base.metadata

def run_migrations_online():
    from alembic import context
    connectable = engine.sync_engine
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()