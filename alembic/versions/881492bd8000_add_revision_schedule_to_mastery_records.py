"""add revision schedule to mastery records

Revision ID: 881492bd8000
Revises: 771392bd7999
Create Date: 2026-08-26 17:04:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '881492bd8000'
down_revision: Union[str, Sequence[str], None] = '771392bd7999'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('mastery_records', sa.Column('next_review_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('mastery_records', sa.Column('last_reviewed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_mastery_records_next_review_at'), 'mastery_records', ['next_review_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_mastery_records_next_review_at'), table_name='mastery_records')
    op.drop_column('mastery_records', 'last_reviewed_at')
    op.drop_column('mastery_records', 'next_review_at')
