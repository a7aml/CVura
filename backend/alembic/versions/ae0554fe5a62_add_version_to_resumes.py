"""add version to resumes

Revision ID: ae0554fe5a62
Revises: 224c6f3f544e
Create Date: 2026-08-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'ae0554fe5a62'
down_revision = '224c6f3f544e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('resumes', sa.Column('version', sa.Integer(), server_default='1', nullable=False))
    op.create_unique_constraint('uq_resumes_user_job_version', 'resumes', ['user_id', 'job_id', 'version'])


def downgrade() -> None:
    op.drop_constraint('uq_resumes_user_job_version', 'resumes', type_='unique')
    op.drop_column('resumes', 'version')
