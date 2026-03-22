---
name: fathom-upgrade-migration
description: |
  Handle Fathom API changes and version migrations.
  Trigger with phrases like "upgrade fathom", "fathom api changes", "fathom migration".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Upgrade & Migration

## Version Tracking

The Fathom API is at `/external/v1`. Monitor for changes:

```python
def validate_api_schema(client):
    meetings = client.list_meetings(limit=1)
    if meetings:
        expected_fields = {"id", "title", "created_at"}
        actual_fields = set(meetings[0].keys())
        new_fields = actual_fields - expected_fields
        if new_fields:
            print(f"New fields detected: {new_fields}")
```

## Resources

- [Fathom Product Updates](https://help.fathom.video/en/articles/6220097)

## Next Steps

For CI, see `fathom-ci-integration`.
