"""Ephemeral stdio bridge for the cross-repository contract test only."""

import argparse
import importlib.util
import json
import sys
from base64 import urlsafe_b64encode
from pathlib import Path


def b64uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return urlsafe_b64encode(raw).rstrip(b"=").decode()


parser = argparse.ArgumentParser()
parser.add_argument("--database", required=True)
args = parser.parse_args()
test_path = Path(__file__).resolve().parents[1] / "tests" / "test_virtuapet.py"
spec = importlib.util.spec_from_file_location("virtuapet_test_fixture", test_path)
if spec is None or spec.loader is None:
    raise RuntimeError("fixture module unavailable")
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
runtime = fixture.build_runtime(args.database)
numbers = runtime.signing_key.public_key().public_numbers()
public_jwk = {"kty": "EC", "crv": "P-256", "x": b64uint(numbers.x), "y": b64uint(numbers.y),
              "kid": runtime.service.kid, "alg": "ES256", "use": "sig"}


def interop_fixture():
    return {"clerkToken": fixture.clerk_token(runtime), "apiKey": fixture.API_KEY,
            "subject": fixture.VP_SUBJECT, "tenantId": fixture.VP_TENANT,
            "issuer": runtime.service.issuer, "linkAudience": runtime.service.link_audience,
            "policyAudience": runtime.service.audience, "kid": runtime.service.kid,
            "publicJwks": {"keys": [public_jwk]}}
for line in sys.stdin:
    message = {}
    try:
        message = json.loads(line)
        if message["operation"] == "fixture":
            result = {"id": message["id"], "ok": True, "body": interop_fixture()}
        elif message["operation"] == "request":
            response = runtime.client.request(message["method"], message["path"],
                                              json=message.get("json"), headers=message.get("headers", {}))
            result = {"id": message["id"], "ok": True, "status": response.status_code,
                      "headers": dict(response.headers), "body": response.json()}
        else:
            raise ValueError("unknown operation")
    except Exception as exc:  # noqa: BLE001 - boundary must redact all fixture failures.
        result = {"id": message.get("id") if isinstance(message, dict) else None,
                  "ok": False, "error": type(exc).__name__}
    print(json.dumps(result, separators=(",", ":")), flush=True)
