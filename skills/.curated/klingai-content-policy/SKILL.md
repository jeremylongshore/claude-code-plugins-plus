---
name: klingai-content-policy
description: 'Implement content policy compliance for Kling AI prompts and outputs.
  Use when filtering

  user prompts or handling moderation. Trigger with phrases like ''klingai content
  policy'',

  ''kling ai moderation'', ''safe video generation'', ''klingai content filter''.

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.18.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- kling-ai
- content-policy
- moderation
compatibility: Designed for Claude Code
---
# Kling AI Content Policy

## Overview

Kling AI enforces content policies server-side. Tasks with policy-violating prompts return `task_status: "failed"` with a content policy message. This skill covers pre-submission filtering to avoid wasted credits and API calls.

## Restricted Content Categories

Kling AI prohibits prompts that generate:

| Category | Examples |
|----------|---------|
| Violence/gore | Graphic injuries, torture, weapons used violently |
| Adult/sexual | Explicit nudity, sexual acts, suggestive content |
| Hate/discrimination | Slurs, targeted harassment, supremacist imagery |
| Illegal activity | Drug manufacturing, terrorism, fraud instructions |
| Real people | Deepfakes of identifiable individuals without consent |
| Copyrighted characters | Trademarked characters (Mickey Mouse, Spider-Man) |
| Misinformation | Fake news, fabricated events presented as real |
| Self-harm | Suicide, eating disorders, self-injury instructions |

## Pre-Submission Prompt Filter

```python
import re

class PromptFilter:
    """Filter prompts before sending to Kling AI to save credits."""

    BLOCKED_PATTERNS = [
        r"\b(nude|naked|explicit|nsfw|porn)\b",
        r"\b(gore|dismember|torture|mutilat)\b",
        r"\b(bomb|terroris|weapon|firearm)\b",
        r"\b(suicide|self.harm|kill.yourself)\b",
        r"\b(deepfake|impersonat)\b",
    ]

    BLOCKED_TERMS = {
        "blood splatter", "graphic violence", "child abuse",
        "drug manufacturing", "hate speech",
    }

    def __init__(self):
        self._patterns = [re.compile(p, re.IGNORECASE) for p in self.BLOCKED_PATTERNS]

    def check(self, prompt: str) -> tuple[bool, str]:
        """Returns (is_safe, reason)."""
        lower = prompt.lower()

        for term in self.BLOCKED_TERMS:
            if term in lower:
                return False, f"Blocked term: '{term}'"

        for pattern in self._patterns:
            match = pattern.search(prompt)
            if match:
                return False, f"Blocked pattern: '{match.group()}'"

        if len(prompt) > 2500:
            return False, "Prompt exceeds 2500 character limit"

        if len(prompt.strip()) < 5:
            return False, "Prompt too short"

        return True, "OK"

    def sanitize(self, prompt: str) -> str:
        """Remove problematic terms and return cleaned prompt."""
        for pattern in self._patterns:
            prompt = pattern.sub("[removed]", prompt)
        return prompt.strip()
```

## Safe Negative Prompts

Always include safety-related negative prompts:

```python
DEFAULT_NEGATIVE_PROMPT = (
    "violence, gore, blood, nudity, sexual content, "
    "weapons, drugs, hate symbols, distorted faces, "
    "watermark, text overlay, low quality, blurry"
)

def safe_request(prompt: str, negative_prompt: str = ""):
    """Build request with safety defaults."""
    combined_negative = f"{DEFAULT_NEGATIVE_PROMPT}, {negative_prompt}".strip(", ")
    return {
        "model_name": "kling-v2-master",
        "prompt": prompt,
        "negative_prompt": combined_negative,
        "duration": "5",
        "mode": "standard",
    }
```

## Integration with Client

```python
class SafeKlingClient:
    """Kling client with pre-submission content filtering."""

    def __init__(self, base_client):
        self.client = base_client
        self.filter = PromptFilter()

    def text_to_video(self, prompt: str, **kwargs):
        is_safe, reason = self.filter.check(prompt)
        if not is_safe:
            raise ValueError(f"Content policy violation: {reason}")

        # Add safety negative prompt
        kwargs.setdefault("negative_prompt", "")
        kwargs["negative_prompt"] = (
            f"{DEFAULT_NEGATIVE_PROMPT}, {kwargs['negative_prompt']}".strip(", ")
        )

        return self.client.text_to_video(prompt, **kwargs)
```

## Handling Server-Side Rejections

```python
def handle_policy_rejection(task_id: str, result: dict):
    """Handle content policy rejections gracefully."""
    status_msg = result["data"].get("task_status_msg", "")

    if "content policy" in status_msg.lower() or "policy violation" in status_msg.lower():
        return {
            "error": "content_policy_violation",
            "message": "Your prompt was rejected by Kling AI's content policy. "
                      "Please revise to remove restricted content.",
            "task_id": task_id,
            "credits_consumed": False,  # policy rejections typically don't consume credits
        }
    return {"error": "generation_failed", "message": status_msg, "task_id": task_id}
```

## User-Facing Guidelines

When building apps with user-submitted prompts:

1. **Filter before API call** -- saves credits on obvious violations
2. **Explain rejections clearly** -- tell users what to change
3. **Log violations** -- track patterns for filter improvement
4. **Rate limit prompt submissions** -- prevent abuse
5. **Review flagged content** -- human review for edge cases

## Prerequisites

- A versioned policy configuration, an owner for escalation, a review queue, and a documented retention/deletion schedule.
- A synthetic or rights-cleared fixture set for tests. Likeness, voice, and other identifiable-person inputs require documented consent; do not rely on a prompt filter as proof of rights.
- A bounded credit budget and a private, watermarked draft destination. Public distribution requires a separate approval record after policy and quality checks.

## Instructions

1. Normalize the prompt and provenance metadata, then run the local filter before creating a task. Preserve only a redacted reason code for rejected content.
2. Check violence, sexual content, hate, illegal activity, self-harm, misinformation, likeness/deepfake, and copyrighted-character risk. Route ambiguous cases to human review rather than trying to evade the policy with sanitization.
3. Confirm that every image, mask, tail frame, and reference asset is synthetic or rights-cleared and that the requested destination and audience are approved.
4. Submit only a short, watermarked sandbox canary within the credit budget. Keep it private until the policy result, visual review, consent record, and owner approval are complete.
5. If the provider rejects the task or a reviewer withdraws approval, do not retry the same request. Quarantine and remove staged media, revoke temporary links, and restore the previous approved version.
6. Retain a redacted receipt with policy version, reason code, opaque task digest, approval state, budget state, retention deadline, and rollback reference; exclude prompts, images, identities, and credentials.

## Output

Return one of `approved_for_draft`, `needs_human_review`, or `blocked`, together with an opaque request digest, policy version, reason codes, rights/provenance result, canary state, budget result, and retention/rollback instructions. A `blocked` result must not create a public artifact or expose the submitted content in logs.

## Error Handling

Reject locally when a known restricted pattern, missing consent, unknown
provenance, disallowed destination, or budget breach is detected. Treat provider
policy failures as final for that request and report a user-safe revision hint; do
not claim that sanitization makes an unsafe request permissible. For classifier
outages or ambiguous results, fail closed into human review. Quarantine any output
that later receives a complaint, remove its distribution links, preserve only the
redacted audit receipt, and record the rollback owner.

## Examples

An internal canary decision can be recorded as:

```text
fixture=synthetic-product-v4; rights=cleared; likeness=none;
policy=pass-v3; destination=staging-private; canary=watermarked;
budget=within-limit; approval=pending; decision=approved_for_draft
```

An identifiable-person image without a consent record must instead return `blocked` and create no generation task.

## Resources

- [Kling AI Terms of Service](https://app.klingai.com/global/dev/document-api/protocols/paidServiceProtocol)
- [Developer Portal](https://app.klingai.com/global/dev)
