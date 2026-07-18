# Notion Known Pitfalls — Examples

## Quick Codebase Scan for Pitfalls

Run this from your project root to flag the most common Notion API mistakes before they ship.
Each check prints `FAIL`/`WARN` when it finds a suspect pattern, or `OK` when the tree is clean.

```bash
# Check for common pitfalls in your codebase
echo "=== Pitfall Scan ==="

# Wrong import
grep -rn "@notion/sdk\|from 'notion'" --include="*.ts" --include="*.js" src/ && \
  echo "FAIL: Wrong import (use @notionhq/client)" || echo "OK: Correct import"

# Unsafe array access on rich_text
grep -rn "rich_text\[0\]\|\.title\[0\]" --include="*.ts" src/ && \
  echo "WARN: Unsafe array access (check length first)" || echo "OK: No unsafe access"

# Hardcoded UUIDs
grep -rn "[a-f0-9]\{8\}-[a-f0-9]\{4\}-[a-f0-9]\{4\}-[a-f0-9]\{4\}-[a-f0-9]\{12\}" --include="*.ts" src/ && \
  echo "WARN: Possible hardcoded UUID (use env vars)" || echo "OK: No hardcoded UUIDs"

# Missing pagination
grep -rn "databases.query\|blocks.children.list" --include="*.ts" src/ | \
  grep -v "has_more\|start_cursor\|paginate" && \
  echo "WARN: Query without pagination check" || echo "OK: Pagination handled"
```

### Reading the output

| Line | Meaning | Fix |
| ------ | --------- | ----- |
| `FAIL: Wrong import` | Code imports a non-existent package | See Pitfall #10 in [implementation.md](implementation.md) |
| `WARN: Unsafe array access` | `rich_text[0]` without a length check | See Pitfall #3 |
| `WARN: Possible hardcoded UUID` | A database/page ID is baked into source | See Pitfall #12 |
| `WARN: Query without pagination` | A list call ignores `has_more` | See Pitfall #5 |
