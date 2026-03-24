from logging.config import fileConfig
from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool
from alembic import context
import sys
from pathlib import Path 
from database.database import Base
from models.models import Client, Order, Product, Transaction
from core.config import DATABASE_URL

sys.path.append(str(Path(__file__).parent.parent))
target_metadata = Base.metadata
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    url = DATABASE_URL 
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},      
    )


    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
        url = DATABASE_URL
        if "+asyncpg" in url:
            url = url.replace("+asyncpg", "")
        connectable = create_engine(url, poolclass=pool.NullPool)

        with connectable.connect() as connection:
            context.configure(
                connection=connection, target_metadata=target_metadata, compare_type=True, include_schemas=True
            )
            with context.begin_transaction():
                context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
