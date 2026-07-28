"""add stripe billing and webhook event state"""

import sqlalchemy as sa

from alembic import op

revision = "20260728_0003"
down_revision = "20260327_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "billing_accounts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("stripe_customer_id", sa.String(length=64), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(length=64), nullable=True),
        sa.Column("stripe_price_id", sa.String(length=64), nullable=True),
        sa.Column("plan_key", sa.String(length=32), nullable=False),
        sa.Column("subscription_status", sa.String(length=32), nullable=False),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        sa.Column("entitlements", sa.JSON(), nullable=False),
        sa.Column("last_invoice_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_customer_id"),
        sa.UniqueConstraint("stripe_subscription_id"),
        sa.UniqueConstraint("tenant_id"),
    )
    op.create_table(
        "stripe_webhook_events",
        sa.Column("stripe_event_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("livemode", sa.Boolean(), nullable=False),
        sa.Column("payload_sha256", sa.String(length=64), nullable=False),
        sa.Column("processing_status", sa.String(length=32), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("stripe_event_id"),
    )


def downgrade() -> None:
    op.drop_table("stripe_webhook_events")
    op.drop_table("billing_accounts")
