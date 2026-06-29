"""rename brief_version status sent to final

Revision ID: e6bb32828cd4
Revises: 20045ec299dd
Create Date: 2026-06-29 23:22:22.172377

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6bb32828cd4'
down_revision: Union[str, Sequence[str], None] = '20045ec299dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "UPDATE brief_versions SET status = 'final' WHERE status = 'sent'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "UPDATE brief_versions SET status = 'sent' WHERE status = 'final'"
    )
