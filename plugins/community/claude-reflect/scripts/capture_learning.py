#!/usr/bin/env python3
"""Detect and capture correction patterns from user prompts. UserPromptSubmit hook.

Cross-platform compatible (Windows, macOS, Linux).
This script is called by Claude Code's UserPromptSubmit hook to detect
correction patterns, positive feedback, and explicit "remember:" markers.
"""
import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.reflect_utils import (
    get_queue_path,
    load_queue,
    save_queue,
    detect_patterns,
    create_queue_item,
    should_include_message,
    MAX_CAPTURE_PROMPT_LENGTH,
)


def main() -> int:
    """Main entry point."""
    # Read JSON from stdin
    input_data = sys.stdin.read()
    if not input_data:
        return 0

    try:
        data = json.loads(input_data)
    except json.JSONDecodeError:
        return 0

    # Extract prompt from JSON - handle different possible field names
    prompt = data.get("prompt") or data.get("message") or data.get("text")
    if not prompt:
        return 0

    # Filter out system content (XML tags, tool results, session continuations)
    if not should_include_message(prompt):
        return 0

    # Skip very long prompts — real user corrections are short.
    # Exception: explicit "remember:" markers are always processed.
    if len(prompt) > MAX_CAPTURE_PROMPT_LENGTH and "remember:" not in prompt.lower():
        return 0

    # Initialize queue if doesn't exist
    queue_path = get_queue_path()
    if not queue_path.exists():
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        queue_path.write_text("[]", encoding="utf-8")

    # Detect patterns
    item_type, patterns, confidence, sentiment, decay_days = detect_patterns(prompt)

    # If we found something, queue it
    if item_type:
        queue_item = create_queue_item(
            message=prompt,
            item_type=item_type,
            patterns=patterns,
            confidence=confidence,
            sentiment=sentiment,
            decay_days=decay_days,
        )

        items = load_queue()
        items.append(queue_item)
        save_queue(items)

        # Output feedback for Claude to acknowledge the capture
        # UserPromptSubmit hooks with exit code 0 add stdout as context
        preview = prompt[:40] + "..." if len(prompt) > 40 else prompt
        print(f"📝 Learning captured: '{preview}' (confidence: {confidence:.0%})")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # Never block on errors - just log and exit 0
        print(f"Warning: capture_learning.py error: {e}", file=sys.stderr)
        sys.exit(0)
