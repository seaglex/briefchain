"""Enumerations used by BriefChain data models."""

from enum import StrEnum


class BriefStatus(StrEnum):
    """Lifecycle status of a brief from the upstream perspective."""

    DRAFT = "draft"
    REVIEWED = "reviewed"
    SENT = "sent"
    ACCEPTED = "accepted"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class BriefPriority(StrEnum):
    """Priority levels for a brief."""

    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


class FeedbackType(StrEnum):
    """Types of feedback that a downstream can send."""

    BLOCKED = "blocked"
    PROGRESS = "progress"
    COMPLETION = "completion"


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
