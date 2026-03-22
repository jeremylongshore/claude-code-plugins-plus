---
name: lindy-common-errors
description: |
  Troubleshoot common Lindy AI agent errors and workflow failures.
  Use when encountering errors, debugging agent failures,
  or resolving integration problems.
  Trigger with phrases like "lindy error", "lindy not working",
  "debug lindy", "lindy troubleshoot", "lindy agent failed".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, debugging]

---
# Lindy Common Errors

## Overview
Troubleshooting guide for Lindy AI agent errors. Lindy agents fail at specific
points in the workflow: trigger reception, action execution, condition evaluation,
or exit condition evaluation. This guide covers each failure class.

## Prerequisites
- Access to Lindy dashboard (https://app.lindy.ai)
- Ability to view agent Tasks tab for error details
- For webhook debugging: curl installed

## Trigger Errors

### Webhook Not Firing
**Symptoms**: No task created when webhook is sent
**Causes & Solutions**:
| Cause | Diagnostic | Fix |
|-------|-----------|-----|
| Wrong URL | Check webhook URL in agent config | Copy exact URL from trigger settings |
| Missing auth | `curl -v` shows 401 | Add `Authorization: Bearer <secret>` header |
| Agent inactive | Dashboard shows agent paused | Activate the agent |
| Filter blocking | Trigger filter too restrictive | Review filter conditions, test with broader filter |
| Wrong HTTP method | Using GET instead of POST | Lindy webhooks require POST |

```bash
# Diagnostic: Test webhook connectivity
curl -v -X POST "https://public.lindy.ai/api/v1/webhooks/YOUR_ID" \
  -H "Authorization: Bearer YOUR_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
# Expect: 200 OK
```

### Email Trigger Not Activating
**Symptoms**: Emails arrive but agent does not wake up
**Solutions**:
1. Verify Gmail/Outlook authorization is current (re-authorize if expired)
2. Check label filter — Lindy Email Received trigger can filter by label
3. Confirm email matches trigger filter conditions (sender, subject, etc.)
4. Check that agent is active, not paused

### Schedule Trigger Missed
**Symptoms**: Agent did not run at scheduled time
**Solutions**:
1. Verify timezone settings match your expectation
2. Check credit balance — agents stop if credits exhausted
3. Review schedule configuration (daily vs weekday vs custom)

## Action Errors

### Slack Send Failed
| Error | Cause | Fix |
|-------|-------|-----|
| Channel not found | Channel name wrong or private | Use exact channel name; ensure bot is invited |
| Not authorized | Slack token expired | Re-authorize Slack in Lindy integrations |
| Rate limited | Too many messages | Reduce trigger frequency or batch messages |

### Gmail Send Failed
| Error | Cause | Fix |
|-------|-------|-----|
| Authentication expired | OAuth token expired | Re-authorize Gmail in Settings |
| Recipient rejected | Invalid email address | Validate email format in prior step |
| Draft not found | Thread ID mismatch | Verify thread context in action config |

### HTTP Request Action Failed
| Error | Cause | Fix |
|-------|-------|-----|
| Connection refused | Target API down | Verify target URL is reachable |
| 401 Unauthorized | Auth header misconfigured | Check Authorization header value |
| Timeout | Target API slow | Increase timeout or optimize target endpoint |
| SSL error | Invalid certificate | Ensure target uses valid HTTPS cert |

```bash
# Diagnostic: Test target API independently
curl -v -X POST "https://api.yourapp.com/endpoint" \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

### Run Code Action Failed
| Error | Cause | Fix |
|-------|-------|-----|
| Import error | Library not available | Use only pre-installed libraries (pandas, numpy, etc.) |
| Type error | Input variable is string | Cast explicitly: `int(var)`, `json.loads(var)` |
| Timeout | Long-running computation | Optimize code; avoid infinite loops |
| Return value empty | No `return` statement | Add explicit `return` with result data |

### Knowledge Base Returns No Results
| Cause | Fix |
|-------|-----|
| Fuzziness at 0 (keyword only) | Increase to 100 for semantic search |
| Content not indexed | Trigger Resync Knowledge Base action |
| Query too vague | Switch field to AI Prompt mode with specific instructions |
| File too large (>20MB) | Split into smaller files |

## Agent Step Errors

### Agent Loops Indefinitely
**Cause**: Exit conditions never satisfied
**Fix**: Add measurable, achievable exit conditions:
```
Primary: "Found at least 3 relevant results"
Fallback: "Made 5 search attempts without finding results"
```

### Agent Picks Wrong Condition Branch
**Cause**: Ambiguous condition prompt
**Fix**: Make conditions mutually exclusive with clear criteria:
```
Branch A: "Go down this path if the email mentions billing, payment, or invoice"
Branch B: "Go down this path if the email mentions a technical issue, bug, or error"
Branch C: "Go down this path for all other topics"
```

### Credit Overrun Warning
**Symptom**: "Task using more resources than expected" pause
**Cause**: Agent step consuming too many credits (complex reasoning)
**Fix**: Simplify prompt, reduce available skills (2-4 max), use smaller model

## Debugging Checklist
1. [ ] Open agent **Tasks** tab — find the failed task
2. [ ] Click into the task — review each step's input/output
3. [ ] Identify the failing step (red indicator)
4. [ ] Check the step's error message and stack trace
5. [ ] Verify integration authorizations are current
6. [ ] Test the trigger independently (curl for webhooks)
7. [ ] Test the action independently (manual run)
8. [ ] Check credit balance — insufficient credits halt execution

## Error Handling

| Error Category | HTTP Status | Retry? | Notes |
|---------------|-------------|--------|-------|
| Auth failure | 401 | No | Re-authorize integration |
| Rate limited | 429 | Yes | Wait for credit reset |
| Agent not found | 404 | No | Verify agent exists and is active |
| Action timeout | 504 | Yes | Simplify step or increase timeout |
| Run Code error | 500 | Maybe | Fix code, then retry |
| Credit exhausted | 402 | No | Upgrade plan or wait for monthly reset |

## Resources
- [Lindy Documentation](https://docs.lindy.ai)
- [Lindy Community](https://community.lindy.ai)
- [Lindy Status](https://status.lindy.ai)

## Next Steps
Proceed to `lindy-debug-bundle` for comprehensive diagnostics.
