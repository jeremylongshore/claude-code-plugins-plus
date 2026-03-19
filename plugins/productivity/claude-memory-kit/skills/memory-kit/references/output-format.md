# MEMORY.md Output Format

memory-save writes MEMORY.md using this structure:

```markdown
## Memory Snapshot
saved: 2026-03-19T14:30:00Z
session_goal: Implementing auth middleware

### Active Tasks
- Refactor token validation
- Add rate limiting to /api/login

### Decisions Made
- Use JWT with 15min expiry (balances security vs UX)

### Patterns Discovered
- Auth tests require test DB seeded with fixtures

### Next Steps
- Write integration tests for token refresh

### Open Questions
- Should refresh tokens rotate on each use?
```

## Section Rules

| Section | When to include | When to skip |
|---------|----------------|--------------|
| Active Tasks | Always | Never |
| Decisions Made | At least one decision this session | No decisions made |
| Patterns Discovered | Found a reusable insight | Nothing new |
| Next Steps | Always | Never |
| Open Questions | Unresolved items exist | All resolved |

## Formatting

- ISO 8601 timestamps (`2026-03-19T14:30:00Z`)
- One bullet per item, concise (under 80 chars)
- Decisions include rationale in parentheses
- Patterns use `pattern: implication` format
