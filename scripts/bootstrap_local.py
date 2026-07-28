from datetime import UTC, datetime

import boto3
from alembic.config import Config
from botocore.exceptions import ClientError

from alembic import command
from app.core.config import get_settings
from app.core.security import hash_api_secret
from app.db.models import APIKey, ProviderAccount, ProviderModel, RoutingPolicy, Tenant
from app.db.session import get_session_factory


def ensure_bucket(settings) -> None:
    s3 = boto3.client(
        "s3",
        region_name=settings.aws_region,
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )
    try:
        s3.head_bucket(Bucket=settings.s3_bucket)
    except ClientError:
        params = {"Bucket": settings.s3_bucket}
        if settings.s3_endpoint_url is None and settings.aws_region != "us-east-1":
            params["CreateBucketConfiguration"] = {"LocationConstraint": settings.aws_region}
        s3.create_bucket(**params)


def ensure_queue(settings) -> None:
    sqs = boto3.client(
        "sqs",
        region_name=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )
    queue_name = settings.audit_queue_url.rstrip("/").split("/")[-1]
    sqs.create_queue(QueueName=queue_name)


def seed_database(settings) -> None:
    session_factory = get_session_factory()
    with session_factory() as session:
        now = datetime.now(UTC).replace(tzinfo=None)
        tenant = session.get(Tenant, "tenant_dev")
        if tenant is None:
            tenant = Tenant(
                id="tenant_dev",
                name="Dev Tenant",
                status="active",
                data_residency="us",
                created_at=now,
                updated_at=now,
            )
            session.add(tenant)

        api_key = session.get(APIKey, "key_dev_001")
        if api_key is None:
            session.add(
                APIKey(
                    id="key_dev_001",
                    tenant_id="tenant_dev",
                    prefix=settings.dev_api_key_prefix,
                    secret_hash=hash_api_secret(
                        settings.dev_api_key_prefix, settings.dev_api_key_secret
                    ),
                    scopes=["inference:invoke"],
                    allowed_models=["gpt-4.1-mini", "gpt-4.1", "mock-echo"],
                    status="active",
                    created_at=now,
                    updated_at=now,
                )
            )
        session.flush()

        if session.get(ProviderAccount, "provider_mock_default") is None:
            session.add(
                ProviderAccount(
                    id="provider_mock_default",
                    tenant_id=None,
                    provider_name="mock",
                    credential_ref="inline://mock",
                    status="active",
                    created_at=now,
                )
            )

        if session.get(ProviderModel, "provider_model_mock") is None:
            session.add(
                ProviderModel(
                    id="provider_model_mock",
                    provider_name="mock",
                    model_name="gpt-4.1-mini",
                    supports_streaming=False,
                    residency_region="us",
                )
            )

        if session.get(RoutingPolicy, "routing_default_dev") is None:
            session.add(
                RoutingPolicy(
                    id="routing_default_dev",
                    tenant_id="tenant_dev",
                    policy_name="default",
                    policy_json={"default_provider": settings.default_provider},
                    created_at=now,
                )
            )
        session.commit()


def main() -> None:
    settings = get_settings()
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    ensure_bucket(settings)
    ensure_queue(settings)
    seed_database(settings)
    print("Bootstrapped local self-hosted environment.")
    print("Tenant: tenant_dev")
    print(f"API key: {settings.dev_api_key_prefix}.{settings.dev_api_key_secret}")


if __name__ == "__main__":
    main()
