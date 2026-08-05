"""rename resumes.pdf_url to pdf_key

Stores the R2 object key instead of a permanent public URL — PDFs are now
served via short-lived presigned URLs generated on read, so persisting a
"url" was both misleading and meant the bucket had to stay publicly
readable forever for old links to keep working.

Revision ID: b1f3a7c9d2e4
Revises: ae0554fe5a62
Create Date: 2026-08-05 00:00:00.000000

"""
from alembic import op

revision = 'b1f3a7c9d2e4'
down_revision = 'ae0554fe5a62'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('resumes', 'pdf_url', new_column_name='pdf_key')


def downgrade() -> None:
    op.alter_column('resumes', 'pdf_key', new_column_name='pdf_url')
