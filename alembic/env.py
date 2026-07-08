"""Alembic environment configuration."""

from logging.config import fileConfig
from os import getenv

from sqlalchemy import engine_from_config, pool

from alembic import context

from briefchain.models.base import Base
from briefchain.models.brief import (  # noqa: F401
    Brief,
    BriefArbiterReview,
    BriefChain,
    BriefTransferHistory,
    BriefVersion,
)
from briefchain.models.feedback import Feedback, FeedbackArbiterReview  # noqa: F401
from briefchain.models.invite import BriefInvite  # noqa: F401
from briefchain.models.kanban import (  # noqa: F401
    Kanban,
    KanbanTemplate,
    KanbanTemplateColumn,
    Task,
    TaskComment,
)
from briefchain.models.user import User, UserIdentity  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Ensure the database URL can be overridden via environment variable.
database_url = getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
