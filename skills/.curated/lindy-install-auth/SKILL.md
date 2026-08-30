---
name: lindy-install-auth
description: 'Set up a Lindy account and authenticated webhook trigger.

  Use when onboarding to Lindy, configuring bearer authentication for webhook triggers,

  or connecting Lindy agents to your application.

  Trigger with phrases like "install lindy", "setup lindy",

  "lindy auth", "configure lindy webhook", "lindy webhook secret".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.17.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lindy
- api
- authentication
compatibility: Designed for Claude Code
---
# Lindy Install & Auth

## Overview

Lindy AI is a no-code/low-code AI agent platform. Agents ("Lindies") are built in
its web dashboard. This setup uses Lindy's documented webhook trigger: Lindy
provides the trigger URL, and the caller authenticates with a bearer secret.

## Prerequisites

- Lindy account with permission to create or edit an agent
- A secret manager for the trigger credential
- `curl` or another HTTP client for a synthetic connectivity check
- A non-production test payload that contains no customer data

## Instructions

### Step 1: Create the Webhook Trigger

1. Open the target agent in the Lindy dashboard.
2. Add a webhook trigger and copy its generated URL.
3. Store the complete URL as a secret because its unique path identifies the trigger.
4. Record only the host and a redacted path in setup receipts.

### Step 2: Configure Bearer Authentication

In the webhook trigger's authentication controls, click **Generate Secret** and
copy the Lindy-generated value into your secret manager. Store it separately
from any credential used by an HTTP Request action to call your application.

```bash
# Load the copied Lindy URL and generated secret from a secret manager.
export LINDY_TRIGGER_URL="https://public.lindy.ai/api/v1/webhooks/YOUR_WEBHOOK_ID"
export LINDY_TRIGGER_SECRET="replace-with-the-lindy-generated-secret"
```

Callers must include that generated value as bearer authentication in every
request.

### Step 3: Verify Authorized Connectivity

```bash
curl --fail-with-body -X POST "$LINDY_TRIGGER_URL" \
  -H "Authorization: Bearer $LINDY_TRIGGER_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"event":"setup.verify","fixture":"synthetic"}'
```

Confirm that exactly one task is created and retain its task ID.

### Step 4: Verify Rejection Without Authentication

```bash
status="$(curl -sS -o /dev/null -w '%{http_code}' \
  -X POST "$LINDY_TRIGGER_URL" \
  -H "Content-Type: application/json" \
  -d '{"event":"setup.reject","fixture":"synthetic"}')"
case "$status" in
  2??)
    echo "unauthenticated request unexpectedly succeeded with HTTP $status" >&2
    exit 1
    ;;
  *) echo "unauthenticated request rejected with HTTP $status" ;;
esac
```

Any non-2xx response proves only transport rejection. Also inspect task history;
do not continue if the unauthenticated request created a task.

## Output

Deliver a sanitized setup receipt naming the target workspace and environment,
the secret-manager references used for the trigger and callback credentials,
the webhook host with its unique path redacted, and the results of one
authorized and one unauthorized connectivity check. Never place credential
values or a complete private webhook URL in the receipt.

## Examples

Store the webhook credential under a development-only secret reference, send a
minimal test payload, and record the resulting task ID and HTTP status. Then
repeat the request without authorization and confirm it is rejected. A setup
that accepts both requests, uses a production credential in development, or
requires copying a secret into source code is incomplete.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Authorized request returns `401` | Trigger secret differs from caller secret | Replace the caller value from the correct secret reference |
| Unauthenticated request creates a task | Authentication is absent or misconfigured | Stop testing and require bearer authentication on the trigger |
| No task is created | Wrong URL, inactive agent, or trigger filter | Re-copy the trigger URL and inspect the agent's task history |
| Request times out | Network or Lindy service problem | Stop retries with real data and check the Lindy status page |

## Security Checklist

- [ ] Complete trigger URL and bearer secret stored in a secret manager
- [ ] Trigger and callback credentials are distinct
- [ ] `.env` files ignored and limited to development fixtures
- [ ] HTTPS used for trigger and callback traffic
- [ ] Authorized request creates one task; unauthenticated request creates none

## Resources

- [Lindy Documentation](https://docs.lindy.ai)
- [Lindy Academy](https://www.lindy.ai/academy-lessons/getting-started-101)
- [Lindy Status](https://status.lindy.ai)

## Next Steps

After successful auth, proceed to `lindy-hello-world` for your first AI agent.
