"""add bounded payment grace to billing accounts"""

import sqlalchemy as sa

from alembic import op

revision = "20260728_0006"
down_revision = "20260728_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "billing_accounts",
        sa.Column("payment_grace_ends_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("billing_accounts", "payment_grace_ends_at")
