"""add scope columns to conversations table

Revision ID: 660292bd6986
Revises: 550181ac5875
Create Date: 2026-08-26 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '660292bd6986'
down_revision: Union[str, Sequence[str], None] = '550181ac5875'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'conversations',
        sa.Column('scope_mode', sa.String(length=50), nullable=False, server_default='all')
    )
    op.add_column(
        'conversations',
        sa.Column('resource_ids_json', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('conversations', 'resource_ids_json')
    op.drop_column('conversations', 'scope_mode')
