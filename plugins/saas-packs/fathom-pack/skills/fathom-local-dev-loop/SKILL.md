---
name: fathom-local-dev-loop
description: |
  Set up local development for Fathom API integrations with mock meeting data.
  Use when building meeting analytics tools, testing webhook handlers,
  or iterating on transcript processing pipelines.
  Trigger with phrases like "fathom dev setup", "fathom local testing",
  "develop with fathom", "fathom mock data".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(python3:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Local Dev Loop

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
