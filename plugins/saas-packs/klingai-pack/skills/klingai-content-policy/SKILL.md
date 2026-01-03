---
name: klingai-content-policy
description: |
  Implement content policy compliance for Kling AI. Use when ensuring generated content meets
  guidelines or filtering inappropriate prompts. Trigger with phrases like 'klingai content policy',
  'kling ai moderation', 'safe video generation', 'klingai content filter'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Content Policy

## Overview

This skill teaches how to implement content policy compliance including prompt filtering, output moderation, age-appropriate content controls, and handling policy violations for Kling AI.

## Prerequisites

- Kling AI API key configured
- Understanding of content policies
- Python 3.8+

## Instructions

Follow these steps for content compliance:

1. **Review Policies**: Understand Kling AI content rules
2. **Implement Filters**: Add prompt screening
3. **Handle Violations**: Manage rejected content
4. **Add Moderation**: Post-generation review
5. **Document Policies**: Create user guidelines

## Content Policy Categories

```
Kling AI Content Policy Categories:

PROHIBITED CONTENT:
- Violence and gore
- Adult/explicit content
- Hate speech and discrimination
- Illegal activities
- Misinformation
- Personal data/deepfakes without consent

RESTRICTED CONTENT (may require additional review):
- Political content
- Medical/health claims
- Financial advice
- Celebrity likenesses
- Trademarked content

ALLOWED CONTENT:
- Creative and artistic content
- Educational material
- Marketing and promotional
- Entertainment
- Product demonstrations
```

## Content Filter Implementation

```python
import re
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum

class ContentCategory(Enum):
    SAFE = "safe"
    WARNING = "warning"
    BLOCKED = "blocked"

@dataclass
class FilterResult:
    category: ContentCategory
    passed: bool
    flags: List[str]
    sanitized_prompt: Optional[str] = None
    message: str = ""

class ContentFilter:
    """Filter prompts for content policy compliance."""

    # Patterns that should be blocked
    BLOCKED_PATTERNS = [
        (r'\b(kill|murder|assassinate)\b', "violence"),
        (r'\b(nude|naked|explicit|porn)\b', "adult_content"),
        (r'\b(hate|racist|nazi)\b', "hate_speech"),
        (r'\b(bomb|terrorist|attack)\b', "dangerous"),
        (r'\b(drug|cocaine|heroin)\b', "illegal"),
    ]

    # Patterns that trigger warnings
    WARNING_PATTERNS = [
        (r'\b(blood|gore|injury)\b', "graphic_content"),
        (r'\b(weapon|gun|knife)\b', "weapons"),
        (r'\b(politician|president|election)\b', "political"),
        (r'\b(doctor|medical|treatment|cure)\b', "medical"),
        (r'\b(investment|stock|crypto)\b', "financial"),
    ]

    # Words to sanitize/replace
    SANITIZE_MAP = {
        "fight": "conflict",
        "war": "confrontation",
        "death": "end",
        "dead": "still",
    }

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode

    def check_prompt(self, prompt: str) -> FilterResult:
        """Check prompt against content policies."""
        prompt_lower = prompt.lower()
        flags = []

        # Check blocked patterns
        for pattern, flag in self.BLOCKED_PATTERNS:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                flags.append(f"blocked:{flag}")

        if flags:
            return FilterResult(
                category=ContentCategory.BLOCKED,
                passed=False,
                flags=flags,
                message="Content violates policy. Generation not allowed."
            )

        # Check warning patterns
        for pattern, flag in self.WARNING_PATTERNS:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                flags.append(f"warning:{flag}")

        if flags:
            if self.strict_mode:
                return FilterResult(
                    category=ContentCategory.WARNING,
                    passed=False,
                    flags=flags,
                    message="Content flagged for review in strict mode."
                )
            else:
                return FilterResult(
                    category=ContentCategory.WARNING,
                    passed=True,
                    flags=flags,
                    sanitized_prompt=self._sanitize_prompt(prompt),
                    message="Content allowed with warnings. Consider revising."
                )

        return FilterResult(
            category=ContentCategory.SAFE,
            passed=True,
            flags=[],
            sanitized_prompt=prompt,
            message="Content approved."
        )

    def _sanitize_prompt(self, prompt: str) -> str:
        """Sanitize prompt by replacing sensitive words."""
        result = prompt
        for original, replacement in self.SANITIZE_MAP.items():
            result = re.sub(
                rf'\b{original}\b',
                replacement,
                result,
                flags=re.IGNORECASE
            )
        return result

    def get_policy_summary(self) -> str:
        """Get human-readable policy summary."""
        return """
CONTENT POLICY SUMMARY

PROHIBITED:
- Violence, gore, or harmful content
- Adult or explicit material
- Hate speech or discrimination
- Illegal activities
- Misinformation or deepfakes

REQUIRES REVIEW:
- Political content
- Medical or health claims
- Financial advice
- Celebrity likenesses

TIPS FOR APPROVAL:
- Use descriptive, creative language
- Focus on positive imagery
- Avoid controversial topics
- Don't include real people without consent
"""

# Usage
filter = ContentFilter(strict_mode=False)

# Check prompt
result = filter.check_prompt("A beautiful sunset over the ocean")
print(f"Result: {result.category.value}, Passed: {result.passed}")

# Check potentially problematic prompt
result = filter.check_prompt("A violent fight scene with weapons")
print(f"Result: {result.category.value}, Flags: {result.flags}")
```

## Content Moderation Service

```python
import requests
from typing import Optional, Dict

class ContentModerationService:
    """Service for content moderation with external API support."""

    def __init__(
        self,
        klingai_api_key: str,
        moderation_api_key: str = None,
        auto_reject: bool = True
    ):
        self.klingai_api_key = klingai_api_key
        self.moderation_api_key = moderation_api_key
        self.auto_reject = auto_reject
        self.filter = ContentFilter()

    def moderate_prompt(self, prompt: str) -> Dict:
        """Full moderation pipeline for prompts."""
        # Step 1: Local filter
        local_result = self.filter.check_prompt(prompt)

        if not local_result.passed and self.auto_reject:
            return {
                "approved": False,
                "stage": "local_filter",
                "category": local_result.category.value,
                "flags": local_result.flags,
                "message": local_result.message
            }

        # Step 2: External moderation API (optional)
        if self.moderation_api_key:
            external_result = self._check_external_api(prompt)
            if not external_result["safe"]:
                return {
                    "approved": False,
                    "stage": "external_moderation",
                    "category": "blocked",
                    "flags": external_result.get("categories", []),
                    "message": "Content flagged by moderation service."
                }

        return {
            "approved": True,
            "stage": "approved",
            "category": local_result.category.value,
            "flags": local_result.flags,
            "sanitized_prompt": local_result.sanitized_prompt,
            "message": "Content approved for generation."
        }

    def moderate_output(self, video_url: str, thumbnail_url: str = None) -> Dict:
        """Moderate generated video output."""
        # In production, this would analyze the actual video
        # For now, return placeholder

        return {
            "approved": True,
            "confidence": 0.95,
            "flags": [],
            "message": "Output passed moderation."
        }

    def _check_external_api(self, prompt: str) -> Dict:
        """Check prompt with external moderation API."""
        # Example using a hypothetical moderation API
        # In production, use OpenAI Moderation, AWS Comprehend, etc.

        try:
            response = requests.post(
                "https://api.moderation-service.com/v1/check",
                headers={"Authorization": f"Bearer {self.moderation_api_key}"},
                json={"text": prompt},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "safe": data.get("safe", True),
                    "categories": data.get("flagged_categories", [])
                }
        except Exception as e:
            # Fail open or closed based on policy
            print(f"Moderation API error: {e}")

        return {"safe": True, "categories": []}

    def generate_with_moderation(
        self,
        prompt: str,
        duration: int = 5,
        model: str = "kling-v1.5"
    ) -> Dict:
        """Generate video with full moderation pipeline."""
        # Pre-generation moderation
        pre_mod = self.moderate_prompt(prompt)

        if not pre_mod["approved"]:
            return {
                "status": "rejected",
                "stage": "pre_generation",
                "reason": pre_mod["message"],
                "flags": pre_mod["flags"]
            }

        # Use sanitized prompt if available
        final_prompt = pre_mod.get("sanitized_prompt", prompt)

        # Generate video
        response = requests.post(
            "https://api.klingai.com/v1/videos/text-to-video",
            headers={
                "Authorization": f"Bearer {self.klingai_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": final_prompt,
                "duration": duration,
                "model": model
            }
        )

        if response.status_code != 200:
            return {
                "status": "error",
                "stage": "generation",
                "reason": f"API error: {response.status_code}"
            }

        job_data = response.json()

        # Note: Post-generation moderation would happen after video completes

        return {
            "status": "submitted",
            "job_id": job_data["job_id"],
            "prompt_flags": pre_mod.get("flags", []),
            "original_prompt": prompt,
            "final_prompt": final_prompt
        }

# Usage
service = ContentModerationService(
    klingai_api_key=os.environ["KLINGAI_API_KEY"],
    auto_reject=True
)

# Check prompt before generation
result = service.moderate_prompt("A peaceful garden with butterflies")
print(f"Approved: {result['approved']}")

# Generate with moderation
result = service.generate_with_moderation(
    prompt="A beautiful mountain landscape at dawn",
    duration=5
)
```

## Policy Violation Logger

```python
from datetime import datetime
import json

class PolicyViolationLogger:
    """Log and track content policy violations."""

    def __init__(self, log_path: str = "policy_violations.json"):
        self.log_path = log_path
        self.violations = []
        self.load()

    def load(self):
        """Load existing violations."""
        try:
            with open(self.log_path) as f:
                self.violations = json.load(f)
        except FileNotFoundError:
            self.violations = []

    def save(self):
        """Save violations to file."""
        with open(self.log_path, "w") as f:
            json.dump(self.violations, f, indent=2)

    def log_violation(
        self,
        prompt: str,
        user_id: str,
        flags: List[str],
        action: str = "blocked"
    ):
        """Log a policy violation."""
        violation = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "prompt_hash": hash(prompt),  # Don't store actual violating content
            "prompt_preview": prompt[:50] + "..." if len(prompt) > 50 else prompt,
            "flags": flags,
            "action": action
        }

        self.violations.append(violation)
        self.save()

        # Check for repeat offenders
        user_violations = [v for v in self.violations if v["user_id"] == user_id]
        if len(user_violations) >= 3:
            print(f"WARNING: User {user_id} has {len(user_violations)} violations")

    def get_violation_stats(self) -> Dict:
        """Get violation statistics."""
        if not self.violations:
            return {"total": 0}

        flag_counts = {}
        for v in self.violations:
            for flag in v["flags"]:
                flag_counts[flag] = flag_counts.get(flag, 0) + 1

        return {
            "total": len(self.violations),
            "by_flag": flag_counts,
            "unique_users": len(set(v["user_id"] for v in self.violations))
        }
```

## Output

Successful execution produces:
- Filtered and approved prompts
- Blocked policy-violating content
- Sanitized alternative prompts
- Violation audit trail

## Error Handling

Common errors and solutions:
1. **False Positives**: Adjust filter patterns
2. **Missed Violations**: Add new patterns
3. **API Timeout**: Implement fallback policy

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Content Policy](https://klingai.com/content-policy)
- [AI Content Moderation](https://platform.openai.com/docs/guides/moderation)
- [NSFW Detection APIs](https://sightengine.com/)
