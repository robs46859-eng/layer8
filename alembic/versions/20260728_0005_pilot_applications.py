"""add public pilot application leads"""

import sqlalchemy as sa

from alembic import op

revision = "20260728_0005"
down_revision = "20260728_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pilot_applications",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("contact_name", sa.String(length=120), nullable=False),
        sa.Column("work_email", sa.String(length=254), nullable=False),
        sa.Column("company", sa.String(length=160), nullable=False),
        sa.Column("role", sa.String(length=120), nullable=True),
        sa.Column("use_case", sa.Text(), nullable=False),
        sa.Column("timeline", sa.String(length=32), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("consent_to_contact", sa.Boolean(), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_pilot_applications_source",
        "pilot_applications",
        ["source"],
        unique=False,
    )
    op.create_index(
        "ix_pilot_applications_status",
        "pilot_applications",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pilot_applications_status",
        table_name="pilot_applications",
    )
    op.drop_index(
        "ix_pilot_applications_source",
        table_name="pilot_applications",
    )
    op.drop_table("pilot_applications")
