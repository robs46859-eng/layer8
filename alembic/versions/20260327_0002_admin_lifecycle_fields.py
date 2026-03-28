"""add tenant and api key lifecycle fields"""

from alembic import op
import sqlalchemy as sa


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

    op.alter_column("tenants", "updated_at", nullable=False)
    op.alter_column("api_keys", "updated_at", nullable=False)


def downgrade() -> None:
    op.drop_column("api_keys", "revoked_at")
    op.drop_column("api_keys", "updated_at")
    op.drop_column("tenants", "disabled_at")
    op.drop_column("tenants", "updated_at")
