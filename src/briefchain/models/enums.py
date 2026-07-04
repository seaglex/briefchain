"""Enumerations used by BriefChain data models."""

from enum import StrEnum


class BriefUpstreamState(StrEnum):
    """Lifecycle state of a brief from the upstream perspective."""

    EDITING = "editing"
    SENT = "sent"
    IN_PROCESS = "in_process"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    DONE = "done"


class BriefDownstreamState(StrEnum):
    """Sub-state of a brief from the downstream perspective."""

    OPENED = "opened"
    DELEGATED = "delegated"
    BLOCKED = "blocked"
    SUBMITTED = "submitted"


class BriefVersionStatus(StrEnum):
    """Lifecycle status of a brief version."""

    DRAFT = "draft"
    REVIEWED = "reviewed"
    FINAL = "final"


class BriefPriority(StrEnum):
    """Priority levels for a brief."""

    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


class FeedbackType(StrEnum):
    """Types of formal contract notifications exchanged about a brief."""

    # Upstream -> downstream
    CANCEL = "cancel"
    SUSPEND = "suspend"
    RESUME = "resume"
    APPROVE = "approve"
    REJECT_SUBMIT = "reject_submit"
    UPDATE = "update"

    # Downstream -> upstream
    SUBMIT = "submit"
    BLOCK = "block"
    DELEGATE = "delegate"
    OPEN = "open"
    PROGRESS = "progress"


class ArbiterReviewStatus(StrEnum):
    """Possible outcomes of an Arbiter review."""

    PASSED = "passed"
    FAILED = "failed"
    FORCE_SKIPPED = "force_skipped"


class UserType(StrEnum):
    """Types of users supported by BriefChain."""

    REGISTERED = "registered"
    OAUTH = "oauth"
    EXTERNAL = "external"
    TEMPORARY = "temporary"


class TaskType(StrEnum):
    """Types of executable task records."""

    TASK = "task"
    BUG = "bug"
    SUB_TASK = "sub_task"


class TaskStatus(StrEnum):
    """Lifecycle status of a task."""

    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"


class TaskPriority(StrEnum):
    """Priority levels for a task."""

    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


class KanbanTemplateMode(StrEnum):
    """Rendering mode for a kanban template."""

    SIMPLE = "simple"
    CUSTOMIZED = "customized"


class KanbanOwnerType(StrEnum):
    """Owner scope for a kanban board."""

    USER = "user"
    TEAM = "team"


class KanbanGroup(StrEnum):
    """Swimlane grouping strategy for a kanban board."""

    NONE = "none"
    ASSIGNEE = "assignee"
    BRIEF = "brief"
    PRIORITY = "priority"
