---
name: fathom-local-dev-loop
description: 'Set up local development for Fathom API integrations with mock meeting
  data.

  Use when building meeting analytics tools, testing webhook handlers,

  or iterating on transcript processing pipelines.

  Trigger with phrases like "fathom dev setup", "fathom local testing",

  "develop with fathom", "fathom mock data".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(python3:*), Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- meeting-intelligence
- ai-notes
- fathom
compatibility: Designed for Claude Code
---
# Fathom Local Dev Loop

## Overview

Use Fathom integrations in the normal local development loop: narrow change, synthetic validation, review, focused tests, and reversible commit.

## Prerequisites

- A clean or recoverable branch, development credential, synthetic meeting/CRM fixtures, repository rules, and test commands.

## Instructions

1. Make one scoped integration/configuration change using development-only data and identity.
2. Inspect the diff, run focused mock/unit checks, and execute a bounded synthetic workflow test.
3. Commit reviewed changes separately and promote only through normal protected workflow.

## Output

- A small reviewed change with test evidence and a normal rollback path, without production meeting or contact data.

## Error Handling

| Condition | Safe response |
|---|---|
| Synthetic test exposes real data | Stop, restrict access, and follow the data procedure. |
| CRM mapping/test fails | Revert or correct within scope; do not use production records to diagnose. |
| Working tree is mixed | Separate unrelated changes before committing. |

## Examples

Update one mapping using a synthetic meeting/action, run its focused test, inspect the redacted result, and commit it separately. If the test fails or unrelated files change, revert/split the work rather than disabling checks or pointing local tooling at production.

## Project Structure

```
fathom-integration/
├── src/
│   ├── fathom_client.py
│   ├── transcript_processor.py
│   └── webhook_handler.py
├── tests/
│   ├── fixtures/
│   │   ├── meeting.json
│   │   └── transcript.json
│   └── test_processor.py
├── .env.local
└── requirements.txt
```

## Mock Meeting Data

```python
MOCK_MEETING = {
    "id": "mtg-123",
    "title": "Product Review Q1",
    "created_at": "2026-03-20T14:00:00Z",
    "duration_seconds": 1800,
    "participants": ["alice@example.com", "bob@example.com"],
    "summary": "Discussed Q1 roadmap priorities. Agreed to focus on API improvements.",
    "action_items": [
        {"text": "Alice to draft API spec by Friday", "assignee": "alice@example.com"},
        {"text": "Bob to review competitor analysis", "assignee": "bob@example.com"}
    ]
}

MOCK_TRANSCRIPT = {
    "segments": [
        {"speaker": "Alice", "text": "Let us review the Q1 priorities.", "start_time": 0.0},
        {"speaker": "Bob", "text": "I think the API work should come first.", "start_time": 5.2},
    ]
}
```

## Development Script

```bash
# Run with mock data (no API calls)
FATHOM_MOCK=true python3 src/transcript_processor.py

# Run with real API
python3 src/transcript_processor.py
```

## Resources

- [Fathom API Docs](https://developers.fathom.ai)

## Next Steps

See `fathom-sdk-patterns` for production API wrappers.
