#!/usr/bin/env python3
"""Semantic learning detection using Claude Code CLI.

Uses `claude -p` (print mode) to semantically analyze user messages
and determine if they contain reusable learnings.
"""
import json
import subprocess
import sys
from typing import Optional, Dict, Any

# Default timeout for Claude CLI calls (seconds)
DEFAULT_TIMEOUT = 30

# Default model for semantic analysis — uses a cost-effective model
# to avoid burning expensive Opus tokens on classification tasks.
# Override via --model flag in /reflect or model parameter in API calls.
DEFAULT_MODEL = "sonnet"

# Semantic analysis prompt template
ANALYSIS_PROMPT = """Analyze this user message from a coding session. Determine if it contains
a reusable learning, correction, or preference that should be remembered for future sessions.

Message: "{text}"

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "is_learning": true or false,
  "type": "correction" or "positive" or "explicit" or null,
  "confidence": 0.0 to 1.0,
  "reasoning": "brief 1-sentence explanation",
  "extracted_learning": "concise actionable statement to add to CLAUDE.md, or null if not a learning"
}}

Guidelines:
- correction: User telling AI to do something differently ("use X not Y", "don't use Z")
- positive: User affirming good behavior ("perfect!", "exactly right", "great approach")
- explicit: User explicitly asking to remember ("remember: ...", "always do X")
- is_learning=true only if it's reusable across sessions (not one-time task instructions)
- confidence: How certain this is a genuine, reusable learning (0.6+ to be useful)
- extracted_learning: Should be actionable and concise (e.g., "Use gpt-5.1 for reasoning tasks")
- Works for ANY language - understand intent, not just English keywords
- Filter out: questions, greetings, one-time commands, context-specific requests"""


def semantic_analyze(
    text: str,
    timeout: int = DEFAULT_TIMEOUT,
    model: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Analyze text using Claude to determine if it's a learning.

    Args:
        text: The user message to analyze
        timeout: Timeout in seconds for the Claude CLI call
        model: Optional model override (e.g., "sonnet", "haiku")

    Returns:
        Dictionary with analysis results, or None on failure:
        {
            "is_learning": bool,
            "type": "correction" | "positive" | "explicit" | None,
            "confidence": float (0.0-1.0),
            "reasoning": str,
            "extracted_learning": str | None
        }
    """
    if not text or not text.strip():
        return None

    # Build the prompt
    prompt = ANALYSIS_PROMPT.format(text=text.replace('"', '\\"'))

    # Build command — use DEFAULT_MODEL if no explicit model specified
    effective_model = model or DEFAULT_MODEL
    cmd = ["claude", "-p", "--output-format", "json"]
    if effective_model:
        cmd.extend(["--model", effective_model])

    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        if result.returncode != 0:
            # Claude CLI failed
            return None

        # Parse the JSON output
        output = result.stdout.strip()
        if not output:
            return None

        # Claude -p --output-format json wraps the response
        # Try to extract the actual JSON from the response
        try:
            response = json.loads(output)
            # If it's wrapped in a "result" field, extract it
            if isinstance(response, dict) and "result" in response:
                content = response["result"]
            else:
                content = response
        except json.JSONDecodeError:
            # Try to find JSON in the output
            content = _extract_json_from_text(output)
            if content is None:
                return None

        # Validate and normalize the response
        return _validate_response(content)

    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        # Claude CLI not installed
        return None
    except Exception:
        return None


def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Try to extract JSON from text that may have surrounding content."""
    # Find JSON object boundaries
    start = text.find('{')
    if start == -1:
        return None

    # Find matching closing brace
    depth = 0
    for i, char in enumerate(text[start:], start):
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i+1])
                except json.JSONDecodeError:
                    return None
    return None


def _validate_response(content: Any) -> Optional[Dict[str, Any]]:
    """Validate and normalize the response from Claude."""
    if not isinstance(content, dict):
        return None

    # Check required fields
    if "is_learning" not in content:
        return None

    # Normalize boolean
    is_learning = content.get("is_learning")
    if isinstance(is_learning, str):
        is_learning = is_learning.lower() in ("true", "yes", "1")
    else:
        is_learning = bool(is_learning)

    # Normalize type
    learning_type = content.get("type")
    if learning_type not in ("correction", "positive", "explicit", None):
        learning_type = None

    # Normalize confidence
    try:
        confidence = float(content.get("confidence", 0.0))
        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
    except (TypeError, ValueError):
        confidence = 0.5 if is_learning else 0.0

    return {
        "is_learning": is_learning,
        "type": learning_type if is_learning else None,
        "confidence": confidence,
        "reasoning": str(content.get("reasoning", "")),
        "extracted_learning": content.get("extracted_learning") if is_learning else None,
    }


def validate_queue_items(
    items: list,
    timeout: int = DEFAULT_TIMEOUT,
    model: Optional[str] = None
) -> list:
    """
    Validate a list of queue items using semantic analysis.

    Items that fail semantic validation are filtered out.
    Items that pass have their confidence updated.

    Args:
        items: List of queue items from learnings-queue.json
        timeout: Timeout per item
        model: Optional model override

    Returns:
        Filtered and enhanced list of queue items
    """
    validated = []

    for item in items:
        message = item.get("message", "")
        if not message:
            continue

        # Run semantic analysis
        result = semantic_analyze(message, timeout=timeout, model=model)

        if result is None:
            # Fallback: keep original item if semantic fails
            validated.append(item)
            continue

        if not result.get("is_learning"):
            # Semantic says it's not a learning - filter out
            continue

        # Merge semantic analysis into item
        enhanced = {**item}
        enhanced["semantic_confidence"] = result["confidence"]
        enhanced["semantic_type"] = result["type"]
        enhanced["semantic_reasoning"] = result["reasoning"]

        if result.get("extracted_learning"):
            enhanced["extracted_learning"] = result["extracted_learning"]

        # Update confidence to be the higher of regex and semantic
        original_confidence = item.get("confidence", 0.6)
        enhanced["confidence"] = max(original_confidence, result["confidence"])

        validated.append(enhanced)

    return validated


# =============================================================================
# Tool error validation
# =============================================================================

# Prompt for converting tool errors into CLAUDE.md guidelines
ERROR_TO_GUIDELINE_PROMPT = """You are analyzing repeated tool execution errors to extract CLAUDE.md guidelines.

Error type: {error_type}
Sample error message: "{sample_error}"
Occurrences: {count}
Suggested guideline: "{suggested_guideline}"

Analyze this error pattern and determine:
1. Is this a project-specific issue that should go in CLAUDE.md?
2. Should the guideline be refined or improved?

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "is_learnable": true or false,
  "refined_guideline": "improved actionable guideline or original if fine",
  "confidence": 0.0 to 1.0,
  "reasoning": "brief explanation"
}}

Guidelines for classification:
- is_learnable=true: Error reveals project-specific context (env vars, paths, services)
- is_learnable=false: Error is generic Claude behavior (bash syntax, file handling)
- refined_guideline: Should mention specific services/paths if detected in error
- confidence: Higher if clearly project-specific (0.7+)"""


def validate_tool_error(
    error_type: str,
    sample_error: str,
    count: int,
    suggested_guideline: str,
    timeout: int = DEFAULT_TIMEOUT,
    model: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Validate a tool error pattern and refine its guideline using Claude.

    Args:
        error_type: The categorized error type
        sample_error: A sample error message
        count: Number of times this error occurred
        suggested_guideline: The initially suggested guideline
        timeout: Timeout in seconds
        model: Optional model override

    Returns:
        Dictionary with validation results, or None on failure:
        {
            "is_learnable": bool,
            "refined_guideline": str,
            "confidence": float,
            "reasoning": str
        }
    """
    prompt = ERROR_TO_GUIDELINE_PROMPT.format(
        error_type=error_type,
        sample_error=sample_error[:300].replace('"', '\\"'),
        count=count,
        suggested_guideline=suggested_guideline or "No suggestion"
    )

    # Build command — use DEFAULT_MODEL if no explicit model specified
    effective_model = model or DEFAULT_MODEL
    cmd = ["claude", "-p", "--output-format", "json"]
    if effective_model:
        cmd.extend(["--model", effective_model])

    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        if result.returncode != 0:
            return None

        output = result.stdout.strip()
        if not output:
            return None

        # Parse JSON response
        try:
            response = json.loads(output)
            if isinstance(response, dict) and "result" in response:
                content = response["result"]
            else:
                content = response
        except json.JSONDecodeError:
            content = _extract_json_from_text(output)
            if content is None:
                return None

        # Validate response
        if not isinstance(content, dict):
            return None

        is_learnable = content.get("is_learnable", False)
        if isinstance(is_learnable, str):
            is_learnable = is_learnable.lower() in ("true", "yes", "1")

        try:
            confidence = float(content.get("confidence", 0.7))
            confidence = max(0.0, min(1.0, confidence))
        except (TypeError, ValueError):
            confidence = 0.7 if is_learnable else 0.3

        return {
            "is_learnable": is_learnable,
            "refined_guideline": content.get("refined_guideline", suggested_guideline),
            "confidence": confidence,
            "reasoning": str(content.get("reasoning", "")),
        }

    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        return None
    except Exception:
        return None


def validate_tool_errors(
    aggregated_errors: list,
    timeout: int = DEFAULT_TIMEOUT,
    model: Optional[str] = None
) -> list:
    """
    Validate a list of aggregated tool errors using semantic analysis.

    Args:
        aggregated_errors: List from aggregate_tool_errors()
        timeout: Timeout per item
        model: Optional model override

    Returns:
        Filtered and enhanced list with refined guidelines
    """
    validated = []

    for error in aggregated_errors:
        error_type = error.get("error_type", "unknown")
        sample_errors = error.get("sample_errors", [])
        sample_error = sample_errors[0] if sample_errors else ""
        count = error.get("count", 1)
        suggested = error.get("suggested_guideline", "")

        # Run semantic validation
        result = validate_tool_error(
            error_type=error_type,
            sample_error=sample_error,
            count=count,
            suggested_guideline=suggested,
            timeout=timeout,
            model=model
        )

        if result is None:
            # Fallback: keep original if semantic fails
            validated.append(error)
            continue

        if not result.get("is_learnable"):
            # Not a learnable pattern - skip
            continue

        # Enhance with semantic results
        enhanced = {**error}
        enhanced["refined_guideline"] = result.get("refined_guideline", suggested)
        enhanced["semantic_confidence"] = result["confidence"]
        enhanced["semantic_reasoning"] = result["reasoning"]
        enhanced["confidence"] = max(error.get("confidence", 0.7), result["confidence"])

        validated.append(enhanced)

    return validated


# =============================================================================
# Contradiction detection
# =============================================================================

# Prompt for detecting contradictions in CLAUDE.md entries
CONTRADICTION_PROMPT = """Analyze these CLAUDE.md entries for contradictions.

Entries:
{entries}

Find pairs that give OPPOSITE advice about the same topic. A contradiction is when:
- Two entries give conflicting instructions (e.g., "use tabs" vs "use spaces")
- Two entries recommend opposite approaches for the same task
- Two entries have incompatible requirements

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "contradictions": [
    {{
      "entry1": "exact text of first entry",
      "entry2": "exact text of second entry",
      "conflict": "brief explanation of why these contradict"
    }}
  ]
}}

Rules:
- Only return ACTUAL contradictions, not just related entries
- Entries about different topics are NOT contradictions
- Return empty array if no contradictions found
- Maximum 10 contradictions"""


def detect_contradictions(
    entries: list,
    timeout: int = DEFAULT_TIMEOUT,
    model: Optional[str] = None
) -> list:
    """
    Find semantically contradicting entries in a list of CLAUDE.md entries.

    Args:
        entries: List of entry strings (bullet points from CLAUDE.md)
        timeout: Timeout in seconds for the Claude CLI call
        model: Optional model override (e.g., "sonnet", "haiku")

    Returns:
        List of contradiction dicts:
        [{"entry1": "...", "entry2": "...", "conflict": "reason"}]
        Returns empty list on failure or if no contradictions found.
    """
    if not entries or len(entries) < 2:
        return []

    # Format entries for the prompt
    entries_text = "\n".join(f"- {e}" for e in entries)
    prompt = CONTRADICTION_PROMPT.format(entries=entries_text)

    # Build command — use DEFAULT_MODEL if no explicit model specified
    effective_model = model or DEFAULT_MODEL
    cmd = ["claude", "-p", "--output-format", "json"]
    if effective_model:
        cmd.extend(["--model", effective_model])

    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        if result.returncode != 0:
            return []

        output = result.stdout.strip()
        if not output:
            return []

        # Parse JSON response
        try:
            response = json.loads(output)
            if isinstance(response, dict) and "result" in response:
                content = response["result"]
            else:
                content = response
        except json.JSONDecodeError:
            content = _extract_json_from_text(output)
            if content is None:
                return []

        # Extract contradictions
        if not isinstance(content, dict):
            return []

        contradictions = content.get("contradictions", [])
        if not isinstance(contradictions, list):
            return []

        # Validate each contradiction
        valid = []
        for c in contradictions:
            if isinstance(c, dict) and "entry1" in c and "entry2" in c:
                valid.append({
                    "entry1": str(c.get("entry1", "")),
                    "entry2": str(c.get("entry2", "")),
                    "conflict": str(c.get("conflict", "Conflicting instructions")),
                })

        return valid

    except subprocess.TimeoutExpired:
        return []
    except FileNotFoundError:
        return []
    except Exception:
        return []


if __name__ == "__main__":
    # Simple test when run directly
    if len(sys.argv) > 1:
        test_text = " ".join(sys.argv[1:])
    else:
        test_text = "no, use Python instead of JavaScript"

    print(f"Analyzing: {test_text!r}")
    result = semantic_analyze(test_text)
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Analysis failed or returned None")
