"""add jd_hash to jobs

Revision ID: 224c6f3f544e
Revises: fcfb647a008b
Create Date: 2026-08-01 17:39:45.876250

"""
from alembic import op
import sqlalchemy as sa


revision = '224c6f3f544e'
down_revision = 'fcfb647a008b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('jobs', sa.Column('jd_hash', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_jobs_jd_hash'), 'jobs', ['jd_hash'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_jobs_jd_hash'), table_name='jobs')
    op.drop_column('jobs', 'jd_hash')
