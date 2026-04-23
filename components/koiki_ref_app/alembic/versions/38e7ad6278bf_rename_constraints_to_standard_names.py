"""rename_constraints_to_standard_names

Revision ID: 38e7ad6278bf
Revises: merge_300ab7334998_20250908001
Create Date: 2025-10-12 00:00:00.000000

This revision previously existed in the project and was accidentally removed.
Without the script Alembic cannot resolve database states that were already
stamped with this revision identifier, causing migrations executed inside the
Docker container to fail with:

    ERROR [alembic.util.messaging] Can't locate revision identified by '38e7ad6278bf'

We reintroduce the revision as a no-op so existing databases can be upgraded
to newer heads without rewriting history.  The original migration only renamed
constraints and indexes; those renames are cosmetic and already reflected in
the current models.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "38e7ad6278bf"
down_revision: Union[str, None] = "merge_300ab7334998_20250908001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: preserved for historical compatibility."""
    # Intentionally left blank. The original revision performed only constraint
    # renames and keeping it empty avoids interfering with existing schemas.
    pass


def downgrade() -> None:
    """No-op downgrade matching the upgrade."""
    pass
