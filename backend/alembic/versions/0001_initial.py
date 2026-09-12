"""initial baseline schema

Materializes the full schema from the ORM models so the baseline migration
can never drift from the models. Subsequent schema changes should use
``alembic revision --autogenerate``.

Revision ID: 0001
Revises:
Create Date: 2026-09-13
"""

import app.models  # noqa: F401  (populate Base.metadata)
from alembic import op
from app.core.database import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
