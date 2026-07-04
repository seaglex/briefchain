"""add task and kanban models

Revision ID: a23a9807994f
Revises: e6bb32828cd4
Create Date: 2026-07-03 01:50:00.000000

"""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a23a9807994f"
down_revision: str | None = "e6bb32828cd4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


SYSTEM_USER_ID = UUID(int=0)


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("task_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("brief_id", sa.CHAR(length=32), nullable=True),
        sa.Column("parent_task_id", sa.Integer(), nullable=True),
        sa.Column("team_id", sa.CHAR(length=32), nullable=True),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("created_by", sa.CHAR(length=32), nullable=False),
        sa.Column("created_by_name", sa.String(length=255), nullable=False),
        sa.Column("assignee_id", sa.CHAR(length=32), nullable=True),
        sa.Column("assignee_name", sa.String(length=255), nullable=True),
        sa.Column("estimated_hours", sa.Integer(), nullable=True),
        sa.Column("actual_hours", sa.Integer(), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("status_changed_by", sa.CHAR(length=32), nullable=True),
        sa.Column("status_changed_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_by", sa.CHAR(length=32), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["brief_id"], ["briefs.brief_id"]),
        sa.ForeignKeyConstraint(["parent_task_id"], ["tasks.task_id"]),
        sa.PrimaryKeyConstraint("task_id"),
    )
    op.create_index(op.f("ix_tasks_assignee_id"), "tasks", ["assignee_id"], unique=False)
    op.create_index(op.f("ix_tasks_brief_id"), "tasks", ["brief_id"], unique=False)
    op.create_index(op.f("ix_tasks_created_by"), "tasks", ["created_by"], unique=False)
    op.create_index(
        op.f("ix_tasks_parent_task_id"), "tasks", ["parent_task_id"], unique=False
    )
    op.create_index(op.f("ix_tasks_team_id"), "tasks", ["team_id"], unique=False)

    op.create_table(
        "kanban_templates",
        sa.Column(
            "kanban_template_id", sa.Integer(), autoincrement=True, nullable=False
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("kanban_template_mode", sa.String(length=20), nullable=False),
        sa.Column("created_by", sa.CHAR(length=32), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("kanban_template_id"),
    )
    op.create_index(
        op.f("ix_kanban_templates_created_by"),
        "kanban_templates",
        ["created_by"],
        unique=False,
    )

    op.create_table(
        "kanban_template_columns",
        sa.Column("column_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("kanban_template_id", sa.Integer(), nullable=False),
        sa.Column("status_key", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("color", sa.String(length=50), nullable=True),
        sa.Column("is_hidden", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["kanban_template_id"],
            ["kanban_templates.kanban_template_id"],
        ),
        sa.PrimaryKeyConstraint("column_id"),
    )
    op.create_index(
        op.f("ix_kanban_template_columns_kanban_template_id"),
        "kanban_template_columns",
        ["kanban_template_id"],
        unique=False,
    )

    op.create_table(
        "kanbans",
        sa.Column("kanban_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("kanban_template_id", sa.Integer(), nullable=False),
        sa.Column("kanban_template_mode", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("owner_type", sa.String(length=20), nullable=False),
        sa.Column("owner_id", sa.CHAR(length=32), nullable=False),
        sa.Column("group", sa.String(length=20), nullable=False),
        sa.Column("done_visible_days", sa.Integer(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["kanban_template_id"],
            ["kanban_templates.kanban_template_id"],
        ),
        sa.PrimaryKeyConstraint("kanban_id"),
    )
    op.create_index(op.f("ix_kanbans_owner_id"), "kanbans", ["owner_id"], unique=False)

    op.create_table(
        "task_comments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_by", sa.CHAR(length=32), nullable=False),
        sa.Column("created_by_name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_task_comments_task_id"), "task_comments", ["task_id"], unique=False
    )
    op.create_index(
        op.f("ix_task_comments_created_by"),
        "task_comments",
        ["created_by"],
        unique=False,
    )

    # Seed the global default simple template.
    op.execute(
        sa.text(
            """
            INSERT INTO kanban_templates
                (kanban_template_id, name, kanban_template_mode, created_by, is_public, created_at, updated_at)
            VALUES
                (1, '默认模板', 'simple', :created_by, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
        ).bindparams(created_by=SYSTEM_USER_ID.hex)
    )
    op.execute(
        sa.text(
            """
            INSERT INTO kanban_template_columns
                (kanban_template_id, status_key, name, color, is_hidden, position, created_at, updated_at)
            VALUES
                (1, 'backlog', 'Backlog', NULL, 1, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (1, 'todo', 'Todo', '#3498db', 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (1, 'in_progress', 'In Progress', '#e67e22', 0, 2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (1, 'in_review', 'In Review', '#9b59b6', 0, 3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (1, 'done', 'Done', '#27ae60', 0, 4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_task_comments_task_id"), table_name="task_comments")
    op.drop_table("task_comments")
    op.drop_index(op.f("ix_kanbans_owner_id"), table_name="kanbans")
    op.drop_table("kanbans")
    op.drop_index(
        op.f("ix_kanban_template_columns_kanban_template_id"),
        table_name="kanban_template_columns",
    )
    op.drop_table("kanban_template_columns")
    op.drop_table("kanban_templates")
    op.drop_index(op.f("ix_tasks_team_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_parent_task_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_created_by"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_brief_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_assignee_id"), table_name="tasks")
    op.drop_table("tasks")
