"""add tenant and api key lifecycle fields"""

import sqlalchemy as sa

from alembic import op

revision = "20260327_0002"
down_revision = "20260327_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("tenants", sa.Column("disabled_at", sa.DateTime(), nullable=True))
    op.add_column("api_keys", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("api_keys", sa.Column("revoked_at", sa.DateTime(), nullable=True))

    op.execute("UPDATE tenants SET updated_at = created_at WHERE updated_at IS NULL")
    op.execute("UPDATE api_keys SET updated_at = created_at WHERE updated_at IS NULL")

    with op.batch_alter_table("tenants") as batch_op:
        batch_op.alter_column("updated_at", nullable=False)
    with op.batch_alter_table("api_keys") as batch_op:
        batch_op.alter_column("updated_at", nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("api_keys") as batch_op:
        batch_op.drop_column("revoked_at")
        batch_op.drop_column("updated_at")
    with op.batch_alter_table("tenants") as batch_op:
        batch_op.drop_column("disabled_at")
        batch_op.drop_column("updated_at")
