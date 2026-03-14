---
name: plan-week
description: Plan the week with priorities, risks, and success criteria
allowed-tools: Read, Glob, Grep
---

Help me plan my week as a Product Manager.

## Context Gathering

Before generating a plan, pull context from all available sources:

### From the workspace
- Review CLAUDE.md, sandbox/, and product-catalog/ for current priorities and in-flight work
- Check recent git history (`git log --oneline -20`) for what shipped recently

### From MCP servers (if configured)
- **GitHub**: Pull open PRs and issues assigned to the user — `gh pr list --author @me`, `gh issue list --assignee @me`
- **Linear**: Check current sprint items, upcoming deadlines, and blocked issues
- **Slack**: Scan recent DMs or channels for pending requests or decisions
- **Google Drive**: Check for documents shared with the user in the past week that may need review
- **Memory**: Recall last week's plan (if stored) and check what was completed vs. carried over

If MCP servers aren't configured, skip those sources and work from workspace context + user input.

## Process

1. **Assess current state** — What's in progress? What shipped last week? What's blocked?
2. **Pull external context** — Open PRs, sprint items, pending requests, unread docs
3. **Identify priorities** — Based on all context, what are the top 3-5 things that need attention this week?
4. **Schedule key activities** — Map priorities to concrete actions (meetings to schedule, docs to write, decisions to make, people to talk to)
5. **Flag risks** — What could go sideways this week? What needs proactive attention?
6. **Set success criteria** — What does a good week look like?

## Output Format

```markdown
## Week of [Date] — Planning

### Last Week Recap
- [What shipped/completed]
- [What slipped and why]
- [Carryover items]

### Open Items (from tools)
| Source | Item | Status | Action Needed |
|--------|------|--------|---------------|
| GitHub PR | [title] | [review/merge/blocked] | [what to do] |
| Linear | [issue] | [in progress/blocked] | [what to do] |
| Slack | [thread/request] | [pending] | [respond/decide] |
| Google Doc | [doc title] | [shared/needs review] | [review by when] |

### This Week's Priorities
1. **[Priority 1]** — [Why it matters] → [Concrete action]
2. **[Priority 2]** — [Why it matters] → [Concrete action]
3. **[Priority 3]** — [Why it matters] → [Concrete action]

### Key Meetings & Prep Needed
| Meeting | Goal | Prep |
|---------|------|------|
| [Meeting] | [Outcome] | [What to prepare] |

### Risks to Watch
- [Risk 1] — [Mitigation]

### Success Criteria
- [ ] [What "done" looks like this week]
```

If you have MCP context available, pre-populate the plan as much as possible — the user should refine, not start from scratch. If no MCP context is available, ask me about current priorities and last week before generating.
