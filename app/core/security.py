import hashlib
import hmac
import secrets
import uuid


def hash_api_secret(prefix: str, secret: str) -> str:
    return hashlib.sha256(f"{prefix}:{secret}".encode("utf-8")).hexdigest()


def verify_api_secret(prefix: str, presented_secret: str, expected_hash: str) -> bool:
    candidate_hash = hash_api_secret(prefix, presented_secret)
    return hmac.compare_digest(candidate_hash, expected_hash)


def split_api_key(presented_key: str) -> tuple[str, str]:
    prefix, separator, secret = presented_key.partition(".")
    if not separator or not prefix or not secret:
        raise PermissionError("invalid api key format")
    return prefix, secret


def generate_request_id() -> str:
    return f"req_{uuid.uuid4().hex}"


def generate_trace_id() -> str:
    return secrets.token_hex(16)
