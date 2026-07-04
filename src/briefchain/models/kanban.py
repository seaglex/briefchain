"""SQLAlchemy models for the Task and Kanban sub-systems."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from briefchain.models.base import Base, TimestampMixin
from briefchain.models.enums import (
    KanbanGroup,
    KanbanOwnerType,
    KanbanTemplateMode,
    TaskPriority,
    TaskStatus,
    TaskType,
)

if TYPE_CHECKING:
    pass


class Task(Base, TimestampMixin):
    """An executable unit of work. Tasks are fully decoupled from kanban boards;
    a board renders tasks by matching ``status`` to template columns.
    """

    __tablename__ = "tasks"

    task_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    brief_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("briefs.brief_id"),
        nullable=True,
        index=True,
    )
    parent_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.task_id"),
        nullable=True,
        index=True,
    )
    team_id: Mapped[UUID | None] = mapped_column(
        nullable=True,
        index=True,
    )

    type: Mapped[TaskType] = mapped_column(
        String(20),
        nullable=False,
        default=TaskType.TASK,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[TaskStatus] = mapped_column(
        String(20),
        nullable=False,
        default=TaskStatus.TODO,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        String(10),
        nullable=False,
        default=TaskPriority.P2,
    )

    created_by: Mapped[UUID] = mapped_column(nullable=False, index=True)
    created_by_name: Mapped[str] = mapped_column(String(255), nullable=False)

    assignee_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    assignee_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    estimated_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status_changed_by: Mapped[UUID | None] = mapped_column(nullable=True)
    status_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    deleted_by: Mapped[UUID | None] = mapped_column(nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    parent: Mapped[Task | None] = relationship(
        "Task",
        lazy="select",
        remote_side="Task.task_id",
        foreign_keys=[parent_task_id],
        back_populates="sub_tasks",
    )
    sub_tasks: Mapped[list[Task]] = relationship(
        "Task",
        lazy="select",
        foreign_keys=[parent_task_id],
        back_populates="parent",
    )
    comments: Mapped[list[TaskComment]] = relationship(
        "TaskComment",
        lazy="select",
        back_populates="task",
        order_by="TaskComment.created_at.desc()",
    )


class KanbanTemplate(Base, TimestampMixin):
    """A reusable column mapping for kanban boards."""

    __tablename__ = "kanban_templates"

    kanban_template_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kanban_template_mode: Mapped[KanbanTemplateMode] = mapped_column(
        String(20),
        nullable=False,
        default=KanbanTemplateMode.SIMPLE,
    )
    created_by: Mapped[UUID] = mapped_column(
        nullable=False,
        default=UUID(int=0),
        index=True,
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    columns: Mapped[list[KanbanTemplateColumn]] = relationship(
        "KanbanTemplateColumn",
        lazy="select",
        back_populates="template",
        order_by="KanbanTemplateColumn.position.asc()",
        cascade="all, delete-orphan",
    )


class KanbanTemplateColumn(Base, TimestampMixin):
    """A single column definition inside a kanban template."""

    __tablename__ = "kanban_template_columns"

    column_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    kanban_template_id: Mapped[int] = mapped_column(
        ForeignKey("kanban_templates.kanban_template_id"),
        nullable=False,
        index=True,
    )

    status_key: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_hidden: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    template: Mapped[KanbanTemplate] = relationship(
        "KanbanTemplate",
        lazy="raise",
        back_populates="columns",
    )


class Kanban(Base, TimestampMixin):
    """A kanban board instance owned by a user or team."""

    __tablename__ = "kanbans"

    kanban_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    kanban_template_id: Mapped[int] = mapped_column(
        ForeignKey("kanban_templates.kanban_template_id"),
        nullable=False,
    )
    kanban_template_mode: Mapped[KanbanTemplateMode] = mapped_column(
        String(20),
        nullable=False,
        default=KanbanTemplateMode.SIMPLE,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_type: Mapped[KanbanOwnerType] = mapped_column(
        String(20),
        nullable=False,
    )
    owner_id: Mapped[UUID] = mapped_column(nullable=False, index=True)

    group: Mapped[KanbanGroup] = mapped_column(
        "group",
        String(20),
        nullable=False,
        default=KanbanGroup.NONE,
        quote=True,
    )
    done_visible_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=14,
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )


class TaskComment(Base, TimestampMixin):
    """A plain comment on a task."""

    __tablename__ = "task_comments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.task_id"),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_by: Mapped[UUID] = mapped_column(nullable=False, index=True)
    created_by_name: Mapped[str] = mapped_column(String(255), nullable=False)

    task: Mapped[Task] = relationship(
        "Task",
        lazy="raise",
        back_populates="comments",
    )
