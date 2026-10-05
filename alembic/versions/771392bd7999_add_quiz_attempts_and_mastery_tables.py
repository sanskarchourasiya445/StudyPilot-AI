"""add quiz attempts and mastery tables

Revision ID: 771392bd7999
Revises: 660292bd6986
Create Date: 2026-08-26 16:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '771392bd7999'
down_revision: Union[str, Sequence[str], None] = '660292bd6986'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('quiz_id', sa.String(length=36), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('topic', sa.String(length=255), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('percentage', sa.Float(), nullable=False),
        sa.Column('attempted_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.resource_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quiz_attempts_id'), 'quiz_attempts', ['id'], unique=False)
    op.create_index(op.f('ix_quiz_attempts_quiz_id'), 'quiz_attempts', ['quiz_id'], unique=False)
    op.create_index(op.f('ix_quiz_attempts_resource_id'), 'quiz_attempts', ['resource_id'], unique=False)
    op.create_index(op.f('ix_quiz_attempts_topic'), 'quiz_attempts', ['topic'], unique=False)
    op.create_index(op.f('ix_quiz_attempts_user_id'), 'quiz_attempts', ['user_id'], unique=False)

    op.create_table(
        'mastery_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('topic', sa.String(length=255), nullable=False),
        sa.Column('mastery_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_questions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('correct_answers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'topic', name='uq_user_topic_mastery')
    )
    op.create_index(op.f('ix_mastery_records_id'), 'mastery_records', ['id'], unique=False)
    op.create_index(op.f('ix_mastery_records_topic'), 'mastery_records', ['topic'], unique=False)
    op.create_index(op.f('ix_mastery_records_user_id'), 'mastery_records', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_mastery_records_user_id'), table_name='mastery_records')
    op.drop_index(op.f('ix_mastery_records_topic'), table_name='mastery_records')
    op.drop_index(op.f('ix_mastery_records_id'), table_name='mastery_records')
    op.drop_table('mastery_records')

    op.drop_index(op.f('ix_quiz_attempts_user_id'), table_name='quiz_attempts')
    op.drop_index(op.f('ix_quiz_attempts_topic'), table_name='quiz_attempts')
    op.drop_index(op.f('ix_quiz_attempts_resource_id'), table_name='quiz_attempts')
    op.drop_index(op.f('ix_quiz_attempts_quiz_id'), table_name='quiz_attempts')
    op.drop_index(op.f('ix_quiz_attempts_id'), table_name='quiz_attempts')
    op.drop_table('quiz_attempts')
