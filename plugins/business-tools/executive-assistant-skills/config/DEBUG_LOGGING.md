# Debug Logging Convention

All executive assistant skills MUST log key steps for post-mortem debugging.

## Tool
```bash
python3 {user.workspace}/scripts/skill_log.py <skill_name> <level> "<message>" ['<details_json>']
```

## Levels
- **DEBUG**: Intermediate data (meeting lists, search results, task counts)
- **INFO**: Key milestones (step started, step completed, results summary)
- **WARN**: Recoverable issues (one source failed, falling back)
- **ERROR**: Failures that affect output (auth expired, command syntax error, no results)

## Mandatory Log Points
Every skill MUST log at minimum:
1. **Start**: `INFO "Starting <skill_name> run"`
2. **Config loaded**: `DEBUG "Config loaded" '{"user": "<name>", "accounts": [...]}'`
3. **Before each external call** (gog, mcporter, todoist-cli): `DEBUG "Calling <tool>" '{"command": "<cmd>"}'`
4. **After each external call**: `DEBUG "Result from <tool>" '{"status": "ok|error", "count": N}'` or `ERROR` if it failed
5. **Key decisions**: `INFO "Skipping meeting X (already processed)"` or `INFO "Drafting email for Y"`
6. **End**: `INFO "Completed <skill_name> run" '{"tasks_created": N, "drafts": N, "errors": N}'`

## Log Location
`{user.workspace}/logs/skills/<skill_name>-YYYY-MM-DD.log` (JSONL)

## Reviewing Logs
```bash
# Today's logs for a skill
cat logs/skills/action-items-$(date +%Y-%m-%d).log | python3 -m json.tool

# Errors only
grep '"level": "ERROR"' logs/skills/action-items-*.log

# Last run
tail -20 logs/skills/action-items-$(date +%Y-%m-%d).log
```
