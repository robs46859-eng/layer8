"""link customer identity organizations to tenants"""

import sqlalchemy as sa

from alembic import op

revision = "20260728_0004"
down_revision = "20260728_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tenants") as batch_op:
        batch_op.add_column(
            sa.Column("clerk_organization_id", sa.String(length=64), nullable=True)
        )
        batch_op.create_unique_constraint(
            "uq_tenants_clerk_organization_id",
            ["clerk_organization_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("tenants") as batch_op:
        batch_op.drop_constraint(
            "uq_tenants_clerk_organization_id",
            type_="unique",
        )
        batch_op.drop_column("clerk_organization_id")
