"""Alembic environment configuration.

Migrations run against the SAME models the app uses
(app.models.database.Base) and the SAME DATABASE_URL from .env/settings,
so what you generate here always matches the real app models and never
drifts out of sync with two separate configs.

Async engine: the app itself uses an async (asyncpg) engine, so
migrations run async too, using run_sync to execute the actual DDL
through Alembic's underlying sync migration machinery.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import Base and every model so Base.metadata knows about all tables -
# app.models (the package __init__) imports each model module, which
# registers it on Base.metadata as a side effect of being imported.
from app.models.database import Base
import app.models  # noqa: F401 - imported for its side effects (see above)
from app.config import settings

# this is the Alembic Config object, which provides access to the
# values within the .ini file in use.
config = context.config

# Override the .ini's sqlalchemy.url with the real one from settings, so
# there's only one place (.env) that defines the database connection -
# alembic.ini's own value is just a placeholder and is never actually
# used.
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL without a live DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode, using an async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())