# Environment management

One file holds every configuration value. One command pushes it. No dashboard
typing.

- Source of truth: `env/production.env` (gitignored, never committed)
- Template: `env/production.env.example` (committed, no secrets)
- Tool: `scripts/envctl.py` (standard library only, no install)

## First-time setup

    cp env/production.env.example env/production.env

Fill in the blanks, then:

    export RENDER_API_KEY=rnd_your_key_here
    python3 scripts/envctl.py validate
    python3 scripts/envctl.py diff
    python3 scripts/envctl.py push

Get a Render API key at <https://dashboard.render.com/u/settings#api-keys>.
Put the export line in `~/.zshrc` so it persists.

## Commands

| Command | What it does |
| --- | --- |
| `validate` | Checks every value against the manifest. Nothing else runs until this passes. |
| `diff` | Shows what would change on Render. Values are compared by hash, never printed. |
| `push` | Writes the file to Render. Shows the diff and asks first. |
| `export --target hostinger` | Prints the five public build values to paste into Hostinger. |
| `doctor` | Reads `/readyz` and explains each failure in plain terms. |

Add `--target render-worker --service <name>` to operate on the worker instead
of the API.

## Why the manifest exists

`scripts/envctl.py` carries a `MANIFEST` describing every variable: which
services need it, whether it is secret, whether Render manages it, and what a
valid value looks like. The rules encode failures already paid for:

- **`S3_ENDPOINT_URL` and `AWS_ENDPOINT_URL` must be present and empty.**
  `app/core/config.py` converts an empty string to `None`, and `None` is what
  tells boto3 to use real AWS. Setting these to an AWS URL produces a
  connection timeout instead of a clear error.
- **`AWS_ACCESS_KEY_ID` must be non-empty and match `AKIA…`.** `readiness.py`
  does `aws_access_key_id or None`, so an empty string silently becomes no
  credentials at all, and botocore reports `Unable to locate credentials` —
  which reads like a missing variable rather than a blank one.
- **`ADMIN_API_TOKEN` must be at least 32 characters.** Empty makes `/admin`
  return `503 admin auth is not configured` instead of `401`, which means the
  gate is not fitted.
- **`CORS_ALLOWED_ORIGINS` must be explicit https origins.** `config.py`
  rejects a wildcard outright.
- **Secrets cannot be routed to a public target.** `NEXT_PUBLIC_*` values are
  compiled into JavaScript that anyone can read. `validate` fails hard rather
  than warning.

## Managed values

`DATABASE_URL` and `REDIS_URL` are marked `managed`. Render injects them from a
linked database or Key Value service, so `push` reads the current value and
writes it back untouched. It never overwrites them from the local file, and it
never deletes them.

If `REDIS_URL` is absent from Render entirely, no amount of pushing will fix it
— the Key Value service has to exist first. `doctor` says so explicitly when it
sees the `localhost:6379` fallback.

## Push semantics

Render's env-var API replaces the **entire set** for a service. Anything on
Render but not in `env/production.env` is deleted. `diff` marks those with `-`
before anything happens, and `push` shows the same list and asks for
confirmation.

This is deliberate. A source of truth that tolerates unexplained extra values
on the server is not a source of truth.

## Hostinger

Hostinger has no API for build environment variables, so those stay manual —
but only five values, printed ready to paste:

    python3 scripts/envctl.py export --target hostinger

`NEXT_PUBLIC_*` values are compiled in at build time. Changing them in
Hostinger does nothing until the site rebuilds.

## Secrets handling

`env/production.env` is gitignored via `env/*.env`. It is the only plaintext
copy on disk — back it up in a password manager, not in the repo, not in cloud
storage.

`envctl` never prints a value. `diff` compares SHA-256 prefixes so you can see
*that* something differs without seeing what.

## Related

- `AUDIT_STORAGE_SETUP.md` — provisioning the S3 bucket, SQS queue, and IAM user
- `HOSTINGER_DEPLOYMENT.md` — static web deployment and DNS
- `../architecture/DEPLOYED_BUILD_BLUEPRINT.md` — release gates
