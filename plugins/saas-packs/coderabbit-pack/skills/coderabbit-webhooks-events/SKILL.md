---
name: coderabbit-webhooks-events
description: |
  Implement CodeRabbit webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling CodeRabbit event notifications securely.
  Trigger with phrases like "coderabbit webhook", "coderabbit events",
  "coderabbit webhook signature", "handle coderabbit events", "coderabbit notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# CodeRabbit Webhooks & Events

## Overview
Handle CodeRabbit events triggered through GitHub and GitLab integrations. CodeRabbit posts AI-powered code review comments on pull requests.

## Prerequisites
- CodeRabbit installed on your GitHub or GitLab repository
- GitHub webhook endpoint configured for PR events
- GitHub App or personal access token for API access
- `.coderabbit.yaml` configuration in repository root

## Event Types

| Event | Source | Payload |
|-------|--------|---------|
| `pull_request_review` | GitHub webhook | Review body, state (approved/changes_requested) |
| `pull_request_review_comment` | GitHub webhook | Line comment, diff position, file path |
| `check_run.completed` | GitHub Checks API | CodeRabbit analysis results, conclusion |
| `issue_comment.created` | GitHub webhook | Summary comment, walkthrough |
| `pull_request.labeled` | GitHub webhook | Labels applied by CodeRabbit |

## Instructions

### Step 1: Configure GitHub Webhook Receiver
```typescript
import express from "express";
import crypto from "crypto";

const app = express();

app.post("/webhooks/github",
  express.raw({ type: "application/json" }),
  async (req, res) => {
    const signature = req.headers["x-hub-signature-256"] as string;  # 256 bytes
    const secret = process.env.GITHUB_WEBHOOK_SECRET!;

    const expected = "sha256=" + crypto
      .createHmac("sha256", secret)
      .update(req.body)
      .digest("hex");

    if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
      return res.status(401).json({ error: "Invalid signature" });  # HTTP 401 Unauthorized
    }

    const event = req.headers["x-github-event"] as string;
    const payload = JSON.parse(req.body.toString());
    res.status(200).json({ received: true });  # HTTP 200 OK
    await routeCodeRabbitEvent(event, payload);
  }
);
```

### Step 2: Filter and Route CodeRabbit Events
```typescript
async function routeCodeRabbitEvent(event: string, payload: any) {
  const isCodeRabbit = payload?.sender?.login === "coderabbitai[bot]";

  if (!isCodeRabbit && event !== "check_run") return;

  switch (event) {
    case "pull_request_review":
      await handleCodeRabbitReview(payload);
      break;
    case "pull_request_review_comment":
      await handleReviewComment(payload);
      break;
    case "check_run":
      if (payload.check_run?.app?.slug === "coderabbitai") {
        await handleCheckRunComplete(payload);
      }
      break;
    case "issue_comment":
      await handleSummaryComment(payload);
      break;
  }
}
```

### Step 3: Process Review Results
```typescript
async function handleCodeRabbitReview(payload: any) {
  const { review, pull_request } = payload;
  const prNumber = pull_request.number;
  const state = review.state;

  if (state === "changes_requested") {
    const issues = parseReviewIssues(review.body);
    await notifyTeam({
      channel: "#code-reviews",
      message: `CodeRabbit found ${issues.length} issues in PR #${prNumber}`,
      prUrl: pull_request.html_url,
    });
  }

  if (state === "approved") {
    await checkAutoMergeEligibility(prNumber);
  }
}

function parseReviewIssues(body: string): string[] {
  return body.split("\n").filter(line =>
    line.match(/^[-*]\s+(Bug|Issue|Suggestion|Security)/i)
  );
}
```

### Step 4: Configure CodeRabbit Behavior
```yaml
# .coderabbit.yaml
reviews:
  auto_review:
    enabled: true
    drafts: false
  path_filters:
    - "!**/*.test.ts"
    - "!**/generated/**"
  review_instructions:
    - path: "src/api/**"
      instructions: "Focus on security and input validation"
chat:
  auto_reply: true
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No review posted | PR too large | Split PR or adjust `max_files` in config |
| Invalid signature | Wrong GitHub secret | Verify webhook secret in App settings |
| Bot not responding | App not installed | Check CodeRabbit GitHub App installation |
| Duplicate comments | Re-triggered workflow | CodeRabbit deduplicates automatically |

## Examples

### Track Review Metrics
```typescript
async function handleCheckRunComplete(payload: any) {
  const { check_run } = payload;
  await metricsDb.insert({
    prNumber: check_run.pull_requests?.[0]?.number,
    conclusion: check_run.conclusion,
    issuesFound: check_run.output?.annotations_count || 0,
    completedAt: check_run.completed_at,
  });
}
```

## Resources
- [CodeRabbit Documentation](https://docs.coderabbit.ai)
- [GitHub Webhooks Guide](https://docs.github.com/en/webhooks)
- [CodeRabbit Configuration](https://docs.coderabbit.ai/configuration)

## Next Steps
For deployment setup, see `coderabbit-deploy-integration`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale