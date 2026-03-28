"""initial schema"""

from alembic import op
import sqlalchemy as sa


revision = "20260327_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("data_residency", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("prefix", sa.String(length=64), nullable=False, unique=True),
        sa.Column("secret_hash", sa.String(length=128), nullable=False),
        sa.Column("scopes", sa.JSON(), nullable=False),
        sa.Column("allowed_models", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "provider_accounts",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("credential_ref", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "provider_models",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("supports_streaming", sa.Boolean(), nullable=False),
        sa.Column("residency_region", sa.String(length=64), nullable=True),
    )
    op.create_table(
        "routing_policies",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("policy_name", sa.String(length=255), nullable=False),
        sa.Column("policy_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "plugin_registrations",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("phase", sa.String(length=16), nullable=False),
        sa.Column("contract_version", sa.String(length=32), nullable=False),
        sa.Column("artifact_uri", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "plugin_bindings",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column(
            "plugin_registration_id",
            sa.String(length=64),
            sa.ForeignKey("plugin_registrations.id"),
            nullable=False,
        ),
        sa.Column("blocking", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "request_audit",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("request_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("api_key_id", sa.String(length=64), nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), nullable=False),
        sa.Column("audit_blob_uri", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "quota_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("period", sa.String(length=32), nullable=False),
        sa.Column("requests_used", sa.Integer(), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "cache_manifests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("cache_key", sa.String(length=255), nullable=False, unique=True),
        sa.Column("storage_uri", sa.String(length=255), nullable=True),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("cache_manifests")
    op.drop_table("quota_snapshots")
    op.drop_table("request_audit")
    op.drop_table("plugin_bindings")
    op.drop_table("plugin_registrations")
    op.drop_table("routing_policies")
    op.drop_table("provider_models")
    op.drop_table("provider_accounts")
    op.drop_table("api_keys")
    op.drop_table("tenants")
