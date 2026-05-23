# Content Filter Implementation

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
