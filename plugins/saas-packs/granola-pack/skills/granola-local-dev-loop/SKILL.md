---
name: granola-local-dev-loop
description: |
  Access Granola meeting data programmatically for developer workflows.
  Use when reading notes from the local cache, building MCP integrations,
  extracting action items into code, or syncing meeting outcomes to dev tools.
  Trigger: "granola dev workflow", "granola MCP", "granola local cache",
  "granola developer", "granola programmatic".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Bash(python3:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, workflow, developer]

---
# Granola Local Dev Loop

## Overview
Access Granola meeting data programmatically using three methods: the local cache file (zero-auth, offline), the MCP server (AI agent integration), or the Enterprise API (workspace-wide access). Build developer workflows that turn meeting outcomes into code tasks, documentation, and project artifacts.

## Prerequisites
- Granola installed with meetings captured
- Node.js 18+ or Python 3.10+ for scripts
- For MCP: Claude Code, Cursor, or another MCP-compatible client
- For Enterprise API: Business/Enterprise plan + API key

## Instructions

### Step 1 — Read the Local Cache (Zero Auth)

Granola stores meeting data in a local JSON cache file:

```bash
# macOS cache location
CACHE_FILE="$HOME/Library/Application Support/Granola/cache-v3.json"

# Check if cache exists and get size
ls -lh "$CACHE_FILE"
```

The cache has a double-JSON structure (JSON string inside JSON):

```python
#!/usr/bin/env python3
"""Extract meetings from Granola local cache."""
import json
from pathlib import Path

CACHE_PATH = Path.home() / "Library/Application Support/Granola/cache-v3.json"

def load_granola_cache():
    raw = json.loads(CACHE_PATH.read_text())
    # Cache contains a JSON string that needs secondary parsing
    state = json.loads(raw) if isinstance(raw, str) else raw
    data = state.get("state", state)
    return {
        "documents": data.get("documents", {}),
        "transcripts": data.get("transcripts", {}),
        "meetings_metadata": data.get("meetingsMetadata", {}),
    }

cache = load_granola_cache()
docs = cache["documents"]
print(f"Found {len(docs)} meetings in local cache")

# List recent meetings
for doc_id, doc in sorted(docs.items(),
                          key=lambda x: x[1].get("updated_at", ""),
                          reverse=True)[:10]:
    print(f"  {doc.get('title', 'Untitled')} — {doc.get('updated_at', 'N/A')}")
```

### Step 2 — Set Up Granola MCP Server

Granola's official MCP integration connects meeting context to AI tools:

```json
// claude_desktop_config.json or .mcp.json
{
  "mcpServers": {
    "granola": {
      "command": "npx",
      "args": ["-y", "granola-mcp-server"]
    }
  }
}
```

With MCP connected, Claude Code and Cursor can:
- Search across all your meetings by topic or person
- Pull context from specific meetings into coding sessions
- Create tickets based on discussed bugs or features
- Scaffold code based on architectural decisions from meetings

Community MCP servers with additional features:
- `pedramamini/GranolaMCP` — CLI + programmatic + MCP access, reads local cache
- `mishkinf/granola-mcp` — semantic search with LanceDB vector embeddings
- `proofgeist/granola-mcp-server` — lightweight local cache reader

### Step 3 — Extract Action Items to Dev Tools

```python
#!/usr/bin/env python3
"""Extract action items from Granola notes and create GitHub issues."""
import json, re, subprocess
from pathlib import Path

def extract_action_items(note_content: str) -> list[dict]:
    """Parse action items from enhanced Granola notes."""
    items = []
    # Matches: - [ ] @person: task description
    pattern = r'- \[ \] @?(\w+):?\s+(.+)'
    for match in re.finditer(pattern, note_content):
        items.append({
            "assignee": match.group(1),
            "task": match.group(2).strip(),
        })
    return items

def create_github_issue(repo: str, title: str, body: str, assignee: str):
    """Create a GitHub issue using gh CLI."""
    cmd = [
        "gh", "issue", "create",
        "--repo", repo,
        "--title", title,
        "--body", body,
        "--assignee", assignee,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  Created: {result.stdout.strip()}")
    else:
        print(f"  Error: {result.stderr.strip()}")

# Usage with cache data
cache = load_granola_cache()  # from Step 1
for doc_id, doc in cache["documents"].items():
    content = doc.get("last_viewed_panel", {})
    # ProseMirror content needs text extraction
    text = json.dumps(content)  # simplified — parse nodes for production
    actions = extract_action_items(text)
    for action in actions:
        print(f"[{action['assignee']}] {action['task']}")
```

### Step 4 — Sync Meeting Outcomes to Project Docs

```bash
#!/bin/bash
set -euo pipefail
# Sync latest Granola meeting notes to project documentation

NOTES_DIR="$HOME/dev/meeting-notes"
mkdir -p "$NOTES_DIR"

# Extract recent meeting titles and dates using Python
python3 -c "
import json
from pathlib import Path

cache_path = Path.home() / 'Library/Application Support/Granola/cache-v3.json'
if cache_path.exists():
    raw = json.loads(cache_path.read_text())
    state = json.loads(raw) if isinstance(raw, str) else raw
    data = state.get('state', state)
    docs = data.get('documents', {})
    for doc_id, doc in sorted(docs.items(),
                              key=lambda x: x[1].get('updated_at', ''),
                              reverse=True)[:5]:
        title = doc.get('title', 'Untitled').replace(' ', '-').lower()
        date = doc.get('created_at', 'unknown')[:10]
        print(f'{date}_{title}')
"
```

### Step 5 — Git Integration Pattern
Reference Granola meetings in commits and PRs:

```bash
# Reference meeting in commit message
git commit -m "feat: implement user onboarding flow

Per meeting 2026-03-22 'Sprint Planning Q1':
- Agreed on 3-step wizard approach
- Sarah approved the design mockups
- Due by April 15

Action items from Granola note: [link]"
```

## Output
- Local cache accessible for offline meeting data reads
- MCP server connected for AI-assisted meeting context
- Action item extraction pipeline ready
- Meeting-to-dev-tools sync established

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Cache file not found | Granola not installed or never launched | Install Granola and capture at least one meeting |
| JSON parse error | Double-JSON structure not handled | Parse the outer string first, then parse the inner object |
| MCP server not connecting | Wrong config path | Verify `claude_desktop_config.json` location for your OS |
| Empty transcripts | Transcript stored separately from document | Check `cache["transcripts"]` keyed by document ID |
| Stale cache data | Cache not refreshed | Restart Granola to force cache update |

## Resources
- [Granola MCP Announcement](https://www.granola.ai/blog/granola-mcp)
- [GranolaMCP (cache-based)](https://github.com/pedramamini/GranolaMCP)
- [Reverse-Engineered API Docs](https://github.com/getprobo/reverse-engineering-granola-api)
- [Granola Enterprise API](https://docs.granola.ai/introduction)

## Next Steps
Proceed to `granola-sdk-patterns` for Zapier automation workflows.
