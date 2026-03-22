---
name: klingai-content-policy
description: |
  Implement content policy compliance for Kling AI prompts and outputs. Use when filtering
  user prompts or handling moderation. Trigger with phrases like 'klingai content policy',
  'kling ai moderation', 'safe video generation', 'klingai content filter'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, content-policy, moderation]

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

## Resources

- [Kling AI Terms of Service](https://app.klingai.com/global/dev/document-api/protocols/paidServiceProtocol)
- [Developer Portal](https://app.klingai.com/global/dev)
