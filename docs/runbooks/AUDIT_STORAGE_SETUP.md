# Audit storage setup (S3 + SQS)

**Purpose:** provision the six `salti8-audit-storage` values that `render.yaml`
declares as `sync: false`, so `/readyz` returns `200`.
**Time:** ~10 minutes.
**Cost at pilot volume:** effectively zero. SQS gives 1M requests/month free
permanently; S3 storage for audit JSON will be cents.

---

## 0. What this is and is not

Every request already writes an audit row to PostgreSQL (`RequestAudit` in
`app/services/audit.py`). That row is the system of record and it works today.

S3 and SQS add a **second, durable archive**: the API pushes the full response
payload onto a queue, and `app/workers/tasks.py` drains that queue and writes
each payload to object storage. This is what survives a database restore and
what an external auditor can be given without database access.

`app/services/readiness.py` checks all four dependencies — Postgres, Redis, S3,
queue — and `/readyz` reports `error` if any one fails. That is why the endpoint
currently returns `503`.

## 0.1 Why AWS specifically

`render.yaml` deliberately uses one credential pair for both storage and queue:

```yaml
# The API and worker intentionally use one IAM identity for S3 and SQS.
- name: salti8-audit-storage
```

`AUDIT_QUEUE_URL` is consumed by `boto3.client("sqs", ...)`, which speaks the
real SQS API. Cloudflare R2, Cloudflare Queues, and Backblaze B2 do not provide
an SQS-compatible endpoint, so a mixed setup would need two credential pairs and
a code change. Use AWS for both unless you are prepared to make that change.

---

## 1. Create the S3 bucket

AWS console → **S3** → **Create bucket**.

| Field | Value |
| --- | --- |
| Bucket name | `salti8-audit-prod` (globally unique — add a suffix if taken) |
| Region | **US East (N. Virginia) `us-east-1`** — must match `AWS_REGION` in `render.yaml` |
| Block Public Access | **Leave all four boxes checked** |
| Bucket Versioning | **Enable** — an audit archive you can overwrite is not an audit archive |
| Default encryption | SSE-S3 (the default) |

→ **`S3_BUCKET=salti8-audit-prod`**

Optional but recommended: **Management → Lifecycle rule** → transition objects
to Glacier Instant Retrieval after 90 days.

## 2. Create the SQS queue

AWS console → **SQS** → **Create queue**.

| Field | Value |
| --- | --- |
| Type | **Standard** (not FIFO) |
| Name | `salti8-audit` |
| Visibility timeout | 60 seconds |
| Message retention | 14 days (maximum) |
| Region | `us-east-1` — same as the bucket |

After creation the detail page shows the **URL**:

```text
https://sqs.us-east-1.amazonaws.com/123456789012/salti8-audit
```

→ **`AUDIT_QUEUE_URL=`** that exact string. The 12-digit number is your AWS
account ID; note it for the next step.

## 3. Create a scoped IAM user

AWS console → **IAM** → **Users** → **Create user**.

- User name: `salti8-render`
- **Do not** tick "Provide user access to the AWS Management Console"
- Permissions: **Attach policies directly** → **Create policy** → **JSON**

Paste this, replacing `123456789012` with your account ID and the bucket name if
you changed it:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AuditBucketObjects",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::salti8-audit-prod/*"
    },
    {
      "Sid": "AuditBucketMetadata",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::salti8-audit-prod"
    },
    {
      "Sid": "AuditQueue",
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:GetQueueUrl"
      ],
      "Resource": "arn:aws:sqs:us-east-1:123456789012:salti8-audit"
    }
  ]
}
```

Name it `salti8-audit-access` and attach it to the user.

`s3:ListBucket` and `s3:GetBucketLocation` are required because
`readiness.py` calls `head_bucket`, which fails without bucket-level
permission even when object permissions are correct.

Do not attach `AmazonS3FullAccess` or `AmazonSQSFullAccess`. Those grant access
to every bucket and queue in the account.

## 4. Create the access key

IAM → Users → `salti8-render` → **Security credentials** → **Create access key**.

- Use case: **Application running outside AWS**
- Copy both values. **The secret is displayed once and cannot be retrieved
  again** — if you lose it, delete the key and create a new one.

→ **`AWS_ACCESS_KEY_ID`** and **`AWS_SECRET_ACCESS_KEY`**

## 5. The two endpoint variables

```text
S3_ENDPOINT_URL=     (leave completely empty)
AWS_ENDPOINT_URL=    (leave completely empty)
```

These exist only to point boto3 at MinIO or ElasticMQ during local development.
A validator in `app/core/config.py` converts an empty string to `None`, which is
what tells boto3 to use the real AWS endpoints. **Setting these to an AWS URL
will break the connection.**

## 6. Enter the values in Render

Render dashboard → **Env Groups** → `salti8-audit-storage`. Editing the group
updates both `salti8-api` and `salti8-audit-worker`.

| Key | Value |
| --- | --- |
| `AWS_REGION` | `us-east-1` (already set) |
| `S3_BUCKET` | `salti8-audit-prod` |
| `AWS_ACCESS_KEY_ID` | from step 4 |
| `AWS_SECRET_ACCESS_KEY` | from step 4 |
| `S3_ENDPOINT_URL` | *(empty)* |
| `AWS_ENDPOINT_URL` | *(empty)* |
| `AUDIT_QUEUE_URL` | from step 2 |

## 7. Verify

```text
GET https://api.salti8.com/readyz
```

Expected:

```json
{
  "status": "ok",
  "backend_mode": "self_hosted",
  "checks": {
    "postgres": {"status": "ok"},
    "redis":    {"status": "ok"},
    "s3":       {"status": "ok"},
    "queue":    {"status": "ok"}
  }
}
```

Each check reports its own failure detail, so a `503` tells you exactly which
dependency is wrong.

| Symptom | Cause |
| --- | --- |
| `s3: 403 Forbidden` | Policy is missing `s3:ListBucket` on the bucket ARN (no `/*`) |
| `s3: 404` | Bucket name typo, or bucket is in a different region than `AWS_REGION` |
| `queue: NonExistentQueue` | `AUDIT_QUEUE_URL` typo, or queue in a different region |
| `queue: InvalidClientTokenId` | Access key was deleted or belongs to another account |
| Either: connection timeout | `S3_ENDPOINT_URL` or `AWS_ENDPOINT_URL` was set when it should be empty |

## 8. End-to-end proof

`readyz` proves the credentials work. It does not prove the pipeline works.

1. Send one authenticated inference request through the API.
2. Confirm a new row in the `request_audits` table.
3. Confirm the queue's **Messages available** count rises, then falls as the
   worker drains it.
4. Confirm a new object appears in the bucket.

Only then is release gate 11 in `DEPLOYED_BUILD_BLUEPRINT.md` satisfied.

## 9. Key rotation

Access keys are long-lived credentials in a third-party dashboard. Rotate every
90 days: create a second access key, update the Render env group, confirm
`/readyz` is still `ok`, then delete the old key in IAM. Never delete first.

## 10. Related documents

- `../architecture/DEPLOYED_BUILD_BLUEPRINT.md` — release gates and current state
- `HOSTINGER_DEPLOYMENT.md` — static web deployment and DNS
- `SEO_AND_INDEXING.md` — public site indexing policy
