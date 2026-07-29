#!/usr/bin/env python3
"""envctl — one source of truth for SALTI8 environment configuration.

Problem this solves
-------------------
Configuration currently lives in three dashboards and one `render.yaml` that
was never applied. Values drift, nobody can say what is actually deployed, and
diagnosing a failure means clicking through a UI that deliberately hides values.

envctl makes `env/production.env` the single source of truth, validates it
against a manifest that encodes every rule learned the hard way, and pushes it
to Render over the API. Nothing is typed into a dashboard again.

Usage
-----
    python scripts/envctl.py validate
    python scripts/envctl.py diff    --target render-api
    python scripts/envctl.py push    --target render-api
    python scripts/envctl.py export  --target hostinger
    python scripts/envctl.py doctor

Safety properties
-----------------
* Values are never printed. Diffs report present/missing/changed and compare
  SHA-256 prefixes, never plaintext.
* A variable classified `secret` cannot be routed to a public build target.
  This is a hard failure, not a warning — `NEXT_PUBLIC_*` values are compiled
  into JavaScript that anyone can read.
* Render-managed values (a database or service connection string Render injects
  itself) are marked `managed` and preserved on push, never overwritten from
  the local file.
* `push` requires an explicit confirmation and always shows the diff first.

Standard library only. No install step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / "env" / "production.env"
RENDER_API = "https://api.render.com/v1"

# --------------------------------------------------------------------------
# Targets
# --------------------------------------------------------------------------

RENDER_API_SERVICE = "render-api"
RENDER_WORKER = "render-worker"
HOSTINGER = "hostinger"
LOCAL = "local"

PUBLIC_TARGETS = {HOSTINGER}
"""Targets whose values are compiled into a browser bundle."""


# --------------------------------------------------------------------------
# Validators
# --------------------------------------------------------------------------


def must_be_empty(value: str) -> str | None:
    """Some variables must exist and be empty.

    `S3_ENDPOINT_URL` and `AWS_ENDPOINT_URL` exist only to point boto3 at MinIO
    or ElasticMQ locally. A validator in app/core/config.py turns an empty
    string into None, and None is what tells boto3 to use real AWS. Setting
    these to an AWS URL produces a connection timeout rather than a clear
    error, which is a genuinely expensive afternoon.
    """
    if value.strip():
        return "must be empty in production (empty means 'use real AWS')"
    return None


def non_empty(value: str) -> str | None:
    if not value.strip():
        return "must not be empty"
    return None


def no_trailing_slash(value: str) -> str | None:
    if value.endswith("/"):
        return "must not end with a slash"
    return None


def https_url(value: str) -> str | None:
    if not value.startswith("https://"):
        return "must start with https://"
    return no_trailing_slash(value)


def sqs_queue_url(value: str) -> str | None:
    pattern = r"^https://sqs\.[a-z0-9-]+\.amazonaws\.com/\d{12}/[A-Za-z0-9_-]+$"
    if not re.match(pattern, value):
        return "must look like https://sqs.<region>.amazonaws.com/<account-id>/<queue>"
    return None


def aws_access_key_id(value: str) -> str | None:
    if not value.strip():
        return "empty — botocore will report 'Unable to locate credentials'"
    if not re.match(r"^(AKIA|ASIA)[A-Z0-9]{16,}$", value):
        return "does not look like an AWS access key id (expected AKIA… or ASIA…)"
    return None


def pem_public_key(value: str) -> str | None:
    r"""Clerk's JWT key is an RSA public key in PEM form.

    Accepts it pasted across lines or already flattened with literal \n. The
    header and footer must both be present — a body-only paste is the common
    mistake and produces an opaque PyJWT failure at request time rather than
    at deploy time.
    """
    if not value.strip():
        return "must not be empty"
    normalised = value.replace("\\n", "\n")
    if "BEGIN PUBLIC KEY" not in normalised:
        return "missing the '-----BEGIN PUBLIC KEY-----' header — copy the whole key from Clerk"
    if "END PUBLIC KEY" not in normalised:
        return "missing the '-----END PUBLIC KEY-----' footer — the paste was truncated"
    return None


def min_length(n: int) -> Callable[[str], str | None]:
    def check(value: str) -> str | None:
        if len(value) < n:
            return f"must be at least {n} characters"
        return None

    return check


def one_of(*options: str) -> Callable[[str], str | None]:
    def check(value: str) -> str | None:
        if value not in options:
            return f"must be one of: {', '.join(options)}"
        return None

    return check


def comma_separated_https(value: str) -> str | None:
    parts = [p.strip() for p in value.split(",") if p.strip()]
    if not parts:
        return "must list at least one origin"
    for part in parts:
        if not part.startswith("https://"):
            return f"origin '{part}' must start with https://"
        if part.endswith("/"):
            return f"origin '{part}' must not end with a slash"
    return None


def stripe_key(prefix: str) -> Callable[[str], str | None]:
    def check(value: str) -> str | None:
        if not value.startswith(prefix):
            return f"must start with {prefix}"
        return None

    return check


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Var:
    key: str
    targets: tuple[str, ...]
    note: str
    required: bool = True
    secret: bool = False
    managed: bool = False
    """Render injects this from a linked database or service. Preserve on push."""
    validators: tuple[Callable[[str], str | None], ...] = field(default_factory=tuple)

    def validate(self, value: str | None) -> list[str]:
        problems: list[str] = []
        if value is None:
            if self.required and not self.managed:
                problems.append("missing from env/production.env")
            return problems
        for validator in self.validators:
            problem = validator(value)
            if problem:
                problems.append(problem)
        return problems


BACKEND = (RENDER_API_SERVICE,)
BACKEND_BOTH = (RENDER_API_SERVICE, RENDER_WORKER)

MANIFEST: tuple[Var, ...] = (
    # --- identity of the deployment -------------------------------------
    Var("APP_NAME", BACKEND, "Service name in logs", validators=(non_empty,)),
    Var("ENVIRONMENT", BACKEND_BOTH, "Drives CORS localhost stripping",
        validators=(one_of("production", "staging", "dev"),)),
    Var("BACKEND_MODE", BACKEND_BOTH, "self_hosted enables Postgres/Redis/S3/SQS",
        validators=(one_of("self_hosted", "memory"),)),
    Var("HOST", BACKEND, "Bind address", required=False),

    # --- data stores ------------------------------------------------------
    Var("DATABASE_URL", BACKEND_BOTH, "Render-managed Postgres connection string",
        secret=True, managed=True),
    Var("REDIS_URL", BACKEND, "Render Key Value connection string. Without it the "
        "app falls back to localhost:6379 and readiness fails",
        secret=True, managed=True),

    # --- audit storage ----------------------------------------------------
    Var("AWS_REGION", BACKEND_BOTH, "Must match the bucket and queue region",
        validators=(non_empty,)),
    Var("S3_BUCKET", BACKEND_BOTH, "Audit archive bucket", validators=(non_empty,)),
    Var("AWS_ACCESS_KEY_ID", BACKEND_BOTH, "IAM user salti8-render",
        secret=True, validators=(aws_access_key_id,)),
    Var("AWS_SECRET_ACCESS_KEY", BACKEND_BOTH, "IAM user salti8-render",
        secret=True, validators=(min_length(30),)),
    Var("AUDIT_QUEUE_URL", BACKEND_BOTH, "SQS queue URL",
        validators=(sqs_queue_url,)),
    Var("S3_ENDPOINT_URL", BACKEND_BOTH, "Empty in production — see must_be_empty",
        validators=(must_be_empty,)),
    Var("AWS_ENDPOINT_URL", BACKEND_BOTH, "Empty in production — see must_be_empty",
        validators=(must_be_empty,)),

    # --- public addresses -------------------------------------------------
    Var("PUBLIC_WEB_URL", BACKEND, "Stripe redirect base", validators=(https_url,)),
    Var("PUBLIC_API_URL", BACKEND, "Self-reference", validators=(https_url,)),
    Var("CORS_ALLOWED_ORIGINS", BACKEND, "Explicit origins; wildcard is rejected by config.py",
        validators=(comma_separated_https,)),

    # --- identity ---------------------------------------------------------
    Var("CLERK_JWT_KEY", BACKEND, "Clerk RSA public key, PEM. May be pasted "
        "across multiple lines; envctl flattens it on push",
        validators=(pem_public_key,)),
    Var("CLERK_ISSUER", BACKEND, "Clerk issuer URL", validators=(https_url,)),
    Var("CLERK_AUTHORIZED_PARTIES", BACKEND, "Accepted azp claims",
        validators=(comma_separated_https,)),
    Var("SELF_SERVICE_SIGNUP_ENABLED", BACKEND, "Provision verified Clerk organizations",
        validators=(one_of("true", "false"),)),

    # --- platform admin ---------------------------------------------------
    Var("ADMIN_API_TOKEN", BACKEND, "Bearer token for /admin. Empty makes /admin "
        "return 503 'not configured' instead of 401",
        secret=True, validators=(min_length(32),)),

    # --- billing ----------------------------------------------------------
    Var("STRIPE_SECRET_KEY", BACKEND, "Stripe secret key", secret=True,
        validators=(stripe_key("sk_"),)),
    Var("STRIPE_WEBHOOK_SECRET", BACKEND, "Signing secret for /v1/webhooks/stripe",
        secret=True, validators=(stripe_key("whsec_"),)),
    Var("STRIPE_LIVE_MODE", BACKEND, "true only with live keys",
        validators=(one_of("true", "false"),)),
    Var("STRIPE_PRICE_TEAM_MONTHLY", BACKEND, "Price id",
        validators=(stripe_key("price_"),)),
    Var("STRIPE_PRICE_BUSINESS_MONTHLY", BACKEND, "Price id",
        validators=(stripe_key("price_"),)),
    Var("STRIPE_PORTAL_CONFIGURATION_ID", BACKEND, "Customer portal configuration",
        required=False),
    Var("BILLING_PAST_DUE_GRACE_DAYS", BACKEND, "Grace period", required=False),

    # --- providers --------------------------------------------------------
    Var("OPENAI_API_KEY", BACKEND, "Provider key", secret=True, required=False),
    Var("GEMINI_API_KEY", BACKEND, "Provider key", secret=True, required=False),
    Var("DEFAULT_PROVIDER", BACKEND, "Default routing target", required=False),

    # --- operational tuning ----------------------------------------------
    Var("STARTUP_CHECKS_ENABLED", BACKEND, "Run dependency checks at boot",
        required=False),
    Var("STARTUP_CHECKS_STRICT", BACKEND, "Refuse to boot if a dependency fails",
        required=False),
    Var("RATE_LIMIT_REQUESTS_PER_MINUTE", BACKEND, "Per-tenant limit", required=False),
    Var("ENABLE_PROMPT_LOGGING", BACKEND, "Keep false unless consented", required=False),
    Var("WORKER_POLL_SECONDS", (RENDER_WORKER,), "Queue poll interval", required=False),
    Var("WORKER_BATCH_SIZE", (RENDER_WORKER,), "Messages per poll", required=False),

    # --- public frontend build values -------------------------------------
    # These are compiled into JavaScript. Nothing secret may live here.
    Var("NEXT_PUBLIC_SITE_URL", (HOSTINGER,), "Origin for canonicals and sitemap",
        validators=(https_url,)),
    Var("NEXT_PUBLIC_API_URL", (HOSTINGER,), "API the browser calls",
        validators=(https_url,)),
    Var("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", (HOSTINGER,), "Clerk publishable key",
        validators=(stripe_key("pk_"),)),
    Var("NEXT_PUBLIC_TEAM_PRICE_LABEL", (HOSTINGER,), "Display only",
        validators=(non_empty,)),
    Var("NEXT_PUBLIC_BUSINESS_PRICE_LABEL", (HOSTINGER,), "Display only",
        validators=(non_empty,)),
)

BY_KEY = {var.key: var for var in MANIFEST}


# --------------------------------------------------------------------------
# .env parsing
# --------------------------------------------------------------------------


KEY_LINE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def load_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=VALUE, tolerating values that span multiple lines.

    Blank values are preserved as empty strings. Distinguishing 'absent' from
    'present but empty' is the whole point — S3_ENDPOINT_URL must be present
    and empty.

    Multi-line values: a PEM key copied from Clerk arrives as seven lines,
    because PEM wraps its base64 body at 64 columns. Demanding that a
    non-programmer manually fold that into one line with literal \\n escapes is
    a needless trap, so any line that does not begin with `KEY=` is treated as
    a continuation of the previous key and joined with a newline.

    A consequence worth knowing: a genuinely malformed line is now attached to
    whatever key precedes it rather than reported on its own. Validation
    catches that downstream, because the resulting value fails its format
    check.
    """
    if not path.exists():
        die(
            f"{path} does not exist.\n"
            f"Copy env/production.env.example to env/production.env and fill it in.\n"
            f"That file is gitignored and must never be committed."
        )

    values: dict[str, str] = {}
    current_key: str | None = None

    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        stripped = raw.strip()

        if not stripped or stripped.startswith("#"):
            # A blank line ends a continuation block, so an accidental gap
            # cannot silently swallow the rest of the file.
            current_key = None
            continue

        if KEY_LINE.match(stripped):
            key, _, value = stripped.partition("=")
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[key] = value
            current_key = key
            continue

        if current_key is None:
            die(
                f"{path}:{lineno}: expected KEY=VALUE but found a bare value.\n"
                f"  Every value must sit on the same line as its key, or directly\n"
                f"  beneath one (for multi-line values such as a PEM key)."
            )

        values[current_key] = f"{values[current_key]}\n{stripped}".strip("\n")

    return values


def flatten_multiline(value: str) -> str:
    r"""Collapse real newlines to literal \n for transport.

    app/api/dependencies.py does `clerk_jwt_key.replace("\\n", "\n")` before
    handing the key to PyJWT, so the deployed value must carry escapes rather
    than actual line breaks.
    """
    return value.replace("\r\n", "\n").replace("\n", "\\n")


def fingerprint(value: str) -> str:
    """Short, stable, non-reversible marker so diffs can compare without exposing."""
    if value == "":
        return "<empty>"
    return hashlib.sha256(value.encode()).hexdigest()[:10]


# --------------------------------------------------------------------------
# Render API
# --------------------------------------------------------------------------


class RenderClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def _request(self, method: str, path: str, body: object | None = None) -> object:
        url = f"{RENDER_API}{path}"
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("Authorization", f"Bearer {self.api_key}")
        request.add_header("Accept", "application/json")
        if data:
            request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read().decode()
                return json.loads(payload) if payload else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:500]
            die(f"Render API {method} {path} failed: {exc.code} {detail}")
        except urllib.error.URLError as exc:
            die(f"Could not reach the Render API: {exc.reason}")
        return None

    def find_service(self, name: str) -> dict:
        query = urllib.parse.urlencode({"name": name, "limit": 20})
        results = self._request("GET", f"/services?{query}") or []
        matches = [
            item["service"]
            for item in results
            if item.get("service", {}).get("name") == name
        ]
        if not matches:
            available = sorted(
                item.get("service", {}).get("name", "?") for item in results
            )
            die(
                f"No Render service named {name!r}.\n"
                f"Services matching that search: {', '.join(available) or 'none'}\n"
                f"Set the correct name with --service."
            )
        return matches[0]

    def get_env_vars(self, service_id: str) -> dict[str, str]:
        query = urllib.parse.urlencode({"limit": 100})
        results = self._request("GET", f"/services/{service_id}/env-vars?{query}") or []
        out: dict[str, str] = {}
        for item in results:
            env_var = item.get("envVar", {})
            key = env_var.get("key")
            if key is not None:
                out[key] = env_var.get("value") or ""
        return out

    def put_env_vars(self, service_id: str, values: dict[str, str]) -> None:
        body = [{"key": k, "value": v} for k, v in sorted(values.items())]
        self._request("PUT", f"/services/{service_id}/env-vars", body)


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------


def die(message: str) -> None:
    print(f"\nerror: {message}\n", file=sys.stderr)
    raise SystemExit(1)


def vars_for_target(target: str) -> list[Var]:
    return [v for v in MANIFEST if target in v.targets]


def cmd_validate(args: argparse.Namespace) -> int:
    values = load_env_file(ENV_FILE)
    problems: list[str] = []
    warnings: list[str] = []

    for var in MANIFEST:
        found = values.get(var.key)
        for problem in var.validate(found):
            if var.managed and found is None:
                continue
            problems.append(f"  {var.key}: {problem}")

    # Refuse to leak a secret into a browser bundle.
    for var in MANIFEST:
        if var.secret and set(var.targets) & PUBLIC_TARGETS:
            problems.append(
                f"  {var.key}: classified secret but routed to a public build target"
            )
        if var.key.startswith("NEXT_PUBLIC_") and var.secret:
            problems.append(f"  {var.key}: NEXT_PUBLIC_ variables cannot be secret")

    known = set(BY_KEY)
    for key in sorted(set(values) - known):
        warnings.append(f"  {key}: present in the file but not in the manifest")

    for line in warnings:
        print(f"warning:\n{line}")

    if problems:
        print("\nvalidation failed:\n" + "\n".join(problems) + "\n")
        return 1

    counts = {t: len(vars_for_target(t)) for t in (RENDER_API_SERVICE, RENDER_WORKER, HOSTINGER)}
    print("validation passed")
    print(f"  {counts[RENDER_API_SERVICE]:>2} variables for {RENDER_API_SERVICE}")
    print(f"  {counts[RENDER_WORKER]:>2} variables for {RENDER_WORKER}")
    print(f"  {counts[HOSTINGER]:>2} variables for {HOSTINGER}")
    return 0


def _render_client() -> RenderClient:
    api_key = os.environ.get("RENDER_API_KEY", "").strip()
    if not api_key:
        die(
            "RENDER_API_KEY is not set.\n"
            "Create one at https://dashboard.render.com/u/settings#api-keys\n"
            "then export it in your shell:  export RENDER_API_KEY=rnd_…"
        )
    return RenderClient(api_key)


def _plan(target: str, service_name: str) -> tuple[RenderClient, dict, dict[str, str], dict[str, str]]:
    values = load_env_file(ENV_FILE)
    client = _render_client()
    service = client.find_service(service_name)
    remote = client.get_env_vars(service["id"])

    desired: dict[str, str] = {}
    for var in vars_for_target(target):
        if var.managed:
            # Never overwrite a value Render injects from a linked database or
            # service. Carry the current value through untouched.
            if var.key in remote:
                desired[var.key] = remote[var.key]
            continue
        if var.key in values:
            desired[var.key] = flatten_multiline(values[var.key])
    return client, service, remote, desired


def cmd_diff(args: argparse.Namespace) -> int:
    client, service, remote, desired = _plan(args.target, args.service)
    print(f"service: {service['name']}  ({service['id']})\n")

    added = sorted(set(desired) - set(remote))
    removed = sorted(set(remote) - set(desired))
    changed = sorted(
        k for k in set(desired) & set(remote) if desired[k] != remote[k]
    )
    same = sorted(k for k in set(desired) & set(remote) if desired[k] == remote[k])

    for key in added:
        print(f"  + {key}  (new, {fingerprint(desired[key])})")
    for key in changed:
        print(f"  ~ {key}  {fingerprint(remote[key])} -> {fingerprint(desired[key])}")
    for key in removed:
        managed = BY_KEY.get(key)
        tag = " [MANAGED — will be lost]" if managed and managed.managed else ""
        print(f"  - {key}  (on Render, absent locally){tag}")
    if not (added or changed or removed):
        print("  no changes — Render matches env/production.env")
    print(f"\n  {len(same)} unchanged")

    if removed:
        print(
            "\nnote: push replaces the full set, so anything listed with '-' is deleted.\n"
            "      Add it to env/production.env first if it should survive."
        )
    return 0


def cmd_push(args: argparse.Namespace) -> int:
    if cmd_validate(args) != 0:
        die("refusing to push while validation fails")
    print()
    client, service, remote, desired = _plan(args.target, args.service)

    added = sorted(set(desired) - set(remote))
    removed = sorted(set(remote) - set(desired))
    changed = sorted(k for k in set(desired) & set(remote) if desired[k] != remote[k])

    print(f"service: {service['name']}  ({service['id']})")
    print(f"  {len(added)} added, {len(changed)} changed, {len(removed)} removed")
    for key in added:
        print(f"  + {key}")
    for key in changed:
        print(f"  ~ {key}")
    for key in removed:
        print(f"  - {key}")

    if not (added or changed or removed):
        print("\nnothing to do")
        return 0

    if not args.yes:
        answer = input("\napply to Render? this replaces the full set [y/N] ")
        if answer.strip().lower() not in {"y", "yes"}:
            print("aborted")
            return 1

    client.put_env_vars(service["id"], desired)
    print("\npushed. Render redeploys the service automatically.")
    print("Verify with:  python scripts/envctl.py doctor")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    values = load_env_file(ENV_FILE)
    selected = vars_for_target(args.target)
    if args.target in PUBLIC_TARGETS:
        for var in selected:
            if var.secret:
                die(f"{var.key} is a secret and must never reach {args.target}")
    for var in selected:
        if var.key in values:
            print(f"{var.key}={values[var.key]}")
    return 0


def _admin_request(method: str, path: str, body: object | None = None) -> tuple[int, object]:
    """Call the platform admin API using the token from env/production.env.

    The token is read from the local file and used in-process. It is never
    echoed, logged, or passed on a command line where it would land in shell
    history.
    """
    values = load_env_file(ENV_FILE)
    token = values.get("ADMIN_API_TOKEN", "").strip()
    if not token:
        die("ADMIN_API_TOKEN is not set in env/production.env")
    base = values.get("PUBLIC_API_URL", "https://api.salti8.com").rstrip("/")

    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(f"{base}{path}", data=data, method=method)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/json")
    if data:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = response.read().decode()
            return response.status, (json.loads(payload) if payload else None)
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode(errors="replace")
        try:
            return exc.code, json.loads(payload)
        except json.JSONDecodeError:
            return exc.code, payload
    except urllib.error.URLError as exc:
        die(f"could not reach the admin API: {exc.reason}")
    return 0, None


def _print_tenant(tenant: dict) -> None:
    org = tenant.get("clerk_organization_id") or "(none)"
    print(f"  {tenant['id']:<24} {tenant['status']:<10} {org:<36} {tenant['name']}")


def cmd_tenant(args: argparse.Namespace) -> int:
    if args.action == "list":
        code, payload = _admin_request("GET", "/admin/tenants")
        if code != 200:
            die(f"admin API returned {code}: {payload}")
        if not payload:
            print("no tenants")
            return 0
        print(f"  {'TENANT ID':<24} {'STATUS':<10} {'CLERK ORG':<36} NAME")
        for tenant in payload:
            _print_tenant(tenant)
        return 0

    if args.action == "create":
        body = {
            "tenant_id": args.id,
            "name": args.name,
            "clerk_organization_id": args.clerk_org,
        }
        if args.residency:
            body["data_residency"] = args.residency
        code, payload = _admin_request("POST", "/admin/tenants", body)
        if code == 201:
            print("created:")
            _print_tenant(payload)
            return 0
        if code == 400 and isinstance(payload, dict):
            die(f"rejected: {payload.get('detail')}")
        die(f"admin API returned {code}: {payload}")

    if args.action == "link":
        body = {"clerk_organization_id": args.clerk_org}
        code, payload = _admin_request("PATCH", f"/admin/tenants/{args.id}", body)
        if code == 200:
            print("linked:")
            _print_tenant(payload)
            return 0
        die(f"admin API returned {code}: {payload}")

    return 1


def cmd_doctor(args: argparse.Namespace) -> int:
    """Read the deployed readiness endpoint and explain each failure."""
    values = load_env_file(ENV_FILE)
    base = values.get("PUBLIC_API_URL", "https://api.salti8.com").rstrip("/")
    url = f"{base}/readyz"
    print(f"GET {url}\n")
    try:
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode())
    except Exception as exc:  # noqa: BLE001 - doctor must report anything
        die(f"could not reach {url}: {exc}")

    body = payload.get("detail", payload)
    checks = body.get("checks", {})
    hints = {
        "localhost:6379": "REDIS_URL is unset — the app fell back to its default. "
                          "Create a Render Key Value service and set REDIS_URL.",
        "Unable to locate credentials": "AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY are "
                                        "empty. An empty string becomes None in "
                                        "readiness.py, so boto3 finds nothing.",
        "InvalidAccessKeyId": "The access key is wrong or was deleted in IAM.",
        "SignatureDoesNotMatch": "The secret access key is wrong.",
        "AccessDenied": "Credentials are valid but the IAM policy is too narrow. "
                        "head_bucket needs s3:ListBucket on the bucket ARN "
                        "without /*.",
        "NonExistentQueue": "AUDIT_QUEUE_URL is wrong, or the queue is in another region.",
    }

    worst = 0
    for name, result in checks.items():
        status = result.get("status")
        if status == "ok":
            print(f"  ok    {name}")
            continue
        worst = 1
        detail = result.get("detail", "")
        print(f"  FAIL  {name}: {detail}")
        for needle, hint in hints.items():
            if needle in detail:
                print(f"        -> {hint}")
                break
    print(f"\noverall: {body.get('status')}")
    return worst


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="envctl", description="One source of truth for SALTI8 configuration."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="check env/production.env against the manifest")

    p_diff = sub.add_parser("diff", help="compare local file to a deployed service")
    p_diff.add_argument("--target", default=RENDER_API_SERVICE,
                        choices=[RENDER_API_SERVICE, RENDER_WORKER])
    p_diff.add_argument("--service", default="layer8", help="Render service name")

    p_push = sub.add_parser("push", help="write the local file to a deployed service")
    p_push.add_argument("--target", default=RENDER_API_SERVICE,
                        choices=[RENDER_API_SERVICE, RENDER_WORKER])
    p_push.add_argument("--service", default="layer8", help="Render service name")
    p_push.add_argument("--yes", action="store_true", help="skip the confirmation")

    p_export = sub.add_parser("export", help="print the values a build target needs")
    p_export.add_argument("--target", default=HOSTINGER,
                          choices=[HOSTINGER, LOCAL, RENDER_API_SERVICE, RENDER_WORKER])

    p_tenant = sub.add_parser("tenant", help="map a Clerk organization to a tenant")
    p_tenant.add_argument("action", choices=["list", "create", "link"])
    p_tenant.add_argument("--id", help="Layer8 tenant id, e.g. tenant_salti8")
    p_tenant.add_argument("--name", help="human-readable tenant name")
    p_tenant.add_argument("--clerk-org", dest="clerk_org", help="Clerk org id, org_...")
    p_tenant.add_argument("--residency", help="optional data residency, e.g. us")

    sub.add_parser("doctor", help="read /readyz and explain each failure")

    args = parser.parse_args()

    if args.command == "tenant":
        if args.action == "create" and not (args.id and args.name and args.clerk_org):
            die("create needs --id, --name and --clerk-org")
        if args.action == "link" and not (args.id and args.clerk_org):
            die("link needs --id and --clerk-org")

    handlers = {
        "validate": cmd_validate,
        "diff": cmd_diff,
        "push": cmd_push,
        "export": cmd_export,
        "tenant": cmd_tenant,
        "doctor": cmd_doctor,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
