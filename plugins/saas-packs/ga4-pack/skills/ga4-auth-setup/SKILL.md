---
name: ga4-auth-setup
description: |
  Configure auth for the GA4 Data API — OAuth user credentials for interactive use,
  or a service account for automation / CI. Pick the right path, set the right scopes,
  grant the right property-level access. Trigger with "set up GA4 auth",
  "GA4 service account", "GA4 OAuth", "connect to Google Analytics".
allowed-tools: Bash(gcloud:*), Bash(curl:*), Bash(jq:*), Bash(python3:*), Bash(ls:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, analytics, google-analytics, ga4, auth]
compatibility: Designed for Claude Code
---

# GA4 Auth Setup

GA4 has two production-grade auth paths. Pick before you start; mixing them mid-flight is the most common failure mode.

| Path | When | Credential file |
|---|---|---|
| **Service account** | Automation, CI, server-side scripts. Token is long-lived, scoped, revocable. | `~/.config/gcloud/sa-ga4.json` (or any path you choose) |
| **OAuth user creds** | Interactive use, multiple GA4 properties, ad-hoc analyst work. Token refreshes from a `~/.config/gcloud/application_default_credentials.json` file. | ADC |

**Recommendation:** service account for any pipeline / report-runner / agent use. OAuth for a human poking around. Don't share OAuth user creds across machines — that's an audit-trail mess.

## Path A — Service account (recommended for automation)

### 1. Create the SA in GCP

```bash
PROJECT=your-gcp-project          # the project that will own the SA
SA_NAME=ga4-reader
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"

gcloud iam service-accounts create "$SA_NAME" \
  --display-name="GA4 read-only API access" \
  --project="$PROJECT"

# Generate a key (file lands locally)
gcloud iam service-accounts keys create ~/.config/gcloud/sa-ga4.json \
  --iam-account="$SA_EMAIL"
```

### 2. Grant the SA access to your GA4 property

This is the step everyone forgets. GA4 has **property-level** access control that lives in the Google Analytics web UI, NOT in GCP IAM. The service account email needs to be added there.

1. Open <https://analytics.google.com/>
2. Admin (bottom-left gear) → Property column → **Property Access Management**
3. Add user: paste `$SA_EMAIL` (e.g. `ga4-reader@your-project.iam.gserviceaccount.com`)
4. Role: **Viewer** (read-only — anything more is over-privilege)
5. Save

### 3. Enable the Data API in the SA's project

```bash
gcloud services enable analyticsdata.googleapis.com --project="$PROJECT"
```

### 4. Test the auth round-trip

```bash
GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/sa-ga4.json \
PROPERTY_ID=123456789 \
python3 -c "
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric, Dimension
import os
client = BetaAnalyticsDataClient()
req = RunReportRequest(
    property=f'properties/{os.environ[\"PROPERTY_ID\"]}',
    date_ranges=[DateRange(start_date='7daysAgo', end_date='today')],
    metrics=[Metric(name='activeUsers')],
    dimensions=[Dimension(name='date')],
)
resp = client.run_report(req)
for row in resp.rows:
    print(row.dimension_values[0].value, row.metric_values[0].value)
"
```

If you get rows back, auth works. If you get `PermissionDenied: 403`, the SA isn't added to the property (step 2). If you get `Disabled: 403`, the API isn't enabled (step 3).

## Path B — OAuth user credentials (interactive)

```bash
gcloud auth application-default login \
  --scopes='https://www.googleapis.com/auth/analytics.readonly,https://www.googleapis.com/auth/cloud-platform'
```

This opens a browser, you sign in with the Google account that has access to the GA4 property, and a refresh token lands at `~/.config/gcloud/application_default_credentials.json`. The Data API client picks it up automatically when `GOOGLE_APPLICATION_CREDENTIALS` is not set.

Same test as Path A step 4 — just omit the `GOOGLE_APPLICATION_CREDENTIALS=` prefix.

## Finding your `PROPERTY_ID`

GA4 property IDs are 9-digit numbers (not the `G-XXXXX` measurement ID, which is for the front-end tracker).

1. Open <https://analytics.google.com/>
2. Admin → Property column → **Property Details**
3. Top of the page: **Property ID** — copy the digits, e.g. `123456789`

## Secret hygiene

- **Never commit the SA JSON key.** Add to `.gitignore`:
  ```
  *-sa-*.json
  sa-ga4.json
  ```
- **Use SOPS+age** for the SA key in any repo it lives in. Per the IS standard: `cd <repo> && sops-init`, then `mv ~/.config/gcloud/sa-ga4.json .sops/ga4-sa.json.sops` and decrypt in-process when needed.
- **Rotate the SA key annually** at minimum: `gcloud iam service-accounts keys list --iam-account=$SA_EMAIL` shows the active keys; create a new one + delete the old one.
- **Grant Viewer-only** at the GA4 property level. Editor or Administrator gives the SA the power to delete the property — you don't want a CI pipeline with that blast radius.

## Common errors

| Error | Likely cause | Fix |
|---|---|---|
| `403 PermissionDenied: User does not have sufficient permissions for this property.` | SA email not added to GA4 property | Path A, step 2 |
| `403 SERVICE_DISABLED` | Data API not enabled in SA's GCP project | Path A, step 3 |
| `401 UNAUTHENTICATED` | `GOOGLE_APPLICATION_CREDENTIALS` points to a missing/unreadable file | `ls -la $GOOGLE_APPLICATION_CREDENTIALS` |
| `Invalid property ID: G-XXXX` | Using measurement ID instead of property ID | See "Finding your PROPERTY_ID" above |
| `Quota exceeded` | Default Data API quota is 200K tokens/day per property | Check Quotas in Cloud Console; raise quota or batch queries with broader date ranges |

## Related skills

- `ga4-data-api-query` — once auth works, build the actual `runReport` call
- `ga4-bigquery-export` — for unsampled event-level data via BigQuery instead of the Data API
