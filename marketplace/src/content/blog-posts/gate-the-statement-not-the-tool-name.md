---
title: "Gate the Statement, Not the Tool Name"
description: "When one MCP tool carries every SQL verb, allowlisting tool names is theater. The safety boundary has to read the statement — here's how that gate was built."
date: "2026-06-29"
tags: ["ai-agents", "claude-code", "security", "mcp", "architecture"]
featured: false
---
The original safety gate on the Dolt-over-MCP plugin tried to keep a Claude Code agent harmless by excluding "history-affecting tools" from its MCP grant. It was the wrong granularity, and it did nothing.

MCP exposes the entire database through one tool — `query` / `exec` — and that tool carries every SQL verb. `SELECT` rides it. So does `CALL DOLT_PUSH`, `CALL DOLT_RESET('--hard')`, `DROP DATABASE`, and `CALL DOLT_BRANCH('-D', 'main')`. Excluding "dangerous tools" from the grant accomplishes nothing, because the dangerous verbs live *inside* the one tool you already granted. The destructive operations were never separate tools to exclude.

This is the reframe the whole Phase 0 hardening pass turned on: **a tool-name allowlist is meaningless for any tool that carries a sub-language.** SQL is a sub-language. So is the shell behind a `Bash` tool. So is anything behind an `eval`. If the tool can run arbitrary statements in some grammar, the only boundary that means anything is one that reads the statement. It is the move from tool-name allowlisting to capability-based security: the grant stops being "you may call the `query` tool" and becomes "you may run these statement classes inside it."

## Why not just allowlist the safe tools?

Because there is exactly one tool, and it is not safe or unsafe — it is whatever statement you hand it. You cannot partition a single door into a safe door and a dangerous door by naming. The same logic kills the next-obvious fix: a denylist of dangerous verbs. Blacklist `DOLT_PUSH`, `DOLT_RESET`, `DROP`... and miss `DOLT_REBASE`, or the proc Dolt ships next quarter, or a `CALL` whose name your regex didn't anticipate. A denylist is only as good as your imagination on the day you wrote it.

The fix inverts that. **You add safety by enumerating what is safe, not by blacklisting what is dangerous.** Anything you cannot positively classify as safe is treated as the most dangerous thing it could be. Default-deny the unknown. It's least privilege applied to a grammar: the agent gets only the verbs it can prove it needs.

## The classifier: three verb classes, decided before the server sees it

`scripts/sql_classifier.py` is 259 lines of pure stdlib. No import side effects, so the 22 unit tests in `tests/test_sql_classifier.py` import it directly and hammer it in isolation. `scripts/dolt-mcp-client.py` makes it the chokepoint — every statement is classified *before* it reaches the dolt-mcp server, into one of three classes:

- **read** — `SELECT` / `SHOW` / `DESCRIBE` / `EXPLAIN` / read-only table functions → executes freely.
- **safe-write** — `INSERT` / `UPDATE` / `DELETE` / `CREATE TABLE` / `CALL DOLT_COMMIT` / `DOLT_CHECKOUT` / `DOLT_BRANCH` (create) → executes **only** on an agent-owned branch (never `main`) and **only** under `--allow-mutation`. On pre-GA / alpha database flavors it's refused entirely — read-only there.
- **history-affecting** — `CALL DOLT_PUSH` / `DOLT_PULL` / `DOLT_MERGE` / `DOLT_REBASE` / `DOLT_RESET('--hard')` / branch-or-tag delete / `DROP DATABASE` / `GRANT` / any unknown `CALL …` → **always refused.** The classifier is recommend-only here: it surfaces the exact command it would have run and a human runs it.

The agent gets to mutate its own scratch branch. It never gets to rewrite shared history. That line is drawn by reading the verb, not by trusting a tool grant.

## The fail-safe details are the whole point

A statement-level gate is really an input-validation boundary — every statement is validated before it executes — and a classifier is only as good as its failure mode. This one fails closed, and the details are where a naive regex gate quietly gets it wrong.

**Default-deny the unknown.** Any `CALL` with no resolvable procedure name, and any unrecognized `CALL DOLT_*`, is classified history-affecting — refused. When Dolt ships a new stored proc, it lands on the deny side automatically, with no code change. That's the enumerate-the-safe principle paying rent.

**Batch = max severity.** A multi-statement batch is classified at the severity of its most dangerous statement. A read prefix cannot smuggle a write past the gate:

```python
# A batch is as dangerous as its worst statement.
# "SELECT 1; CALL DOLT_PUSH(...)" classifies as history-affecting, not read.
return max(
    (classify_statement(s) for s in split_statements(sql)),
    key=lambda c: SEVERITY[c],
    default="read",
)
```

**Comment-stripping is quote-aware.** `/* */`, `--`, and `#` comments are stripped before classification, so a verb hidden behind a comment can't mask the real leading verb. But string literals are preserved — which matters more than it looks. The `--hard` inside `CALL DOLT_RESET('--hard')` must *not* be mistaken for the start of a `--` line comment. Get that wrong and a hard reset reads as a soft one. The contract:

```python
def strip_sql_comments(sql: str) -> str:
    """Remove -- , # , and /* */ comments. Quote-aware.

    Inside a '...' or "..." string literal, comment markers are
    inert: the --hard in CALL DOLT_RESET('--hard') survives intact.
    Backslash and doubled-quote escapes are honored so a quote inside
    a literal doesn't prematurely end it.
    """
```

**`DOLT_RESET` is severity-split on its argument.** Soft reset is safe-write. `--hard` is history-affecting. Same proc name, two classes, decided by reading the argument the literal preserved above.

**Cannot prove it's a read → at least safe-write.** Ambiguity loses. A `WITH` (CTE) resolves to whatever it ultimately wraps — `WITH x AS (...) SELECT` is read; `WITH x AS (...) DELETE` is safe-write. The classifier never guesses in the agent's favor.

## The Bash door: the §10 union gate

Hardening the MCP path left a second door open. The original safety check inspected only `mcp__*` grants. It was blind to the fact that an agent could still be handed `Bash(dolt:*)` or `Bash(bash:*)` and reach `dolt push` — or anything — straight through the shell. Same destructive operation, different surface, completely unguarded.

`scripts/check-agent-safety.sh` is the CI gate that closes it. It asserts the mutation-verb taxonomy across **both** surfaces — every agent `.md` and the core `SKILL.md`:

1. No `Bash(<cmd>:*)` wildcard that can reach a history-affecting op. `bash`/`sh` are arbitrary by definition; `dolt`/`bd`/`bd-sync`/`git` reach `push` / `reset` / `branch -D` / `killall`. Banned.
2. No granted MCP tool outside the read/safe set — so a *future* `…__exec` / `…__merge` / `…__push` / `…__reset` grant fails the build the moment someone adds it.

The subtlety that makes it correct: **it scans the allowlist only, never the denylist.** A destructive pattern in `disallowedTools` is the mitigation, not a violation — flagging it would be backwards. The gate only cares what a config *permits*.

```bash
# Scan ALLOWED grants only. A destructive pattern under
# disallowedTools is the fix, not the finding.
grep -oE 'Bash\(([^):]+):\*\)' "$agent_md" | while read -r grant; do
  cmd=$(printf '%s' "$grant" | sed -E 's/Bash\(([^):]+):\*\)/\1/')
  case "$cmd" in
    bash|sh|dolt|bd|bd-sync|git)
      fail "$agent_md grants Bash($cmd:*) — reaches a history-affecting op" ;;
  esac
done
```

That landed by replacing `Bash(bash|dolt|bd:*)` wildcards in 5 agents plus the `SKILL.md` with explicit read-only subcommand allowlists. Wildcards are an unbounded grant; an enumerated subcommand list is a bounded one.

## Invariants become mechanisms, not comments

A second blocker had the same shape at a smaller scale: `scripts/dolt-push-dolthub.sh` *documented* its safety invariants in comments and trusted them. A safety invariant written only in a comment is not enforced. So the comments became mechanisms:

- A failed `bd export` used to be swallowed with `|| true`. Now a failed flush **aborts the push** — you never push on an unverified flush.
- A `flock` idempotency guard makes overlapping scheduled runs a no-op, so a double-fire can't double-apply.
- On an ambiguous push failure, it polls the DoltHub SQL API for the real terminal state instead of blind-retrying into a possible double-push.

And the supply chain got pinned: `dolt-mcp-server@v0.3.6` plus a Go module checksum, consistent across README / SKILL / client. No `@latest` in anything security-sensitive — `@latest` means "I'll run whatever you publish next," which is not a thing you say to a binary that can rewrite a database.

## The general lesson

Tool-name allowlisting works when each tool is a single, fixed capability. It collapses the instant one tool carries a grammar. SQL over MCP is the case here, but a `Bash` tool over a shell is the same hole, and so is any `eval`-style tool that takes a string and runs it. For those, the tool name tells you nothing about what's about to happen. Only the statement does.

So gate the statement. Enumerate the safe verbs, default-deny everything you can't prove safe, classify batches at max severity, and make sure your parser is honest about quotes and comments — because the one place a lazy gate breaks is the `--hard` it mistook for a comment.

## Also shipped

- **governed-second-brain** — `/teamkb-compile`, a nightly job that compiles the day's work into the governed team brain (auto-graduates itself, fixed a tenant-mismatch bug); a follow-up review locked down the scratch dir and made paths portable with glob/dir guards.
- **intent-mail** — migrated to React 19 + Ink 7, removed a dead `@anthropic-ai/claude-agent-sdk` integration, batch-adopted 11 gate-passing Dependabot bumps, and made the OSV scan report-only to kill a phantom red check.
- **claude-code-plugins** — databricks-pack was the Killer Skill of the Week (W27); the `dolt-mcp-vcs` rename landed as a non-breaking install-slug alias, so the old `beads-dolt` slug still resolves.

## Related posts

- [The LLM Should Never Do the Math](/posts/llm-never-does-the-math/)
- [When LLM Output Lies Instead of Crashing](/posts/when-llm-output-lies-instead-of-crashing/)
- [Coverage vs Mutation Testing](/posts/coverage-vs-mutation-testing-rules-engine/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Gate the Statement, Not the Tool Name",
  "description": "When one MCP tool carries every SQL verb, allowlisting tool names is theater. The safety boundary has to read the statement — here's how that gate was built.",
  "datePublished": "2026-06-29T08:00:00-05:00",
  "author": {
    "@type": "Person",
    "name": "Jeremy Longshore",
    "url": "https://startaitools.com/about/"
  },
  "publisher": {
    "@type": "Organization",
    "name": "StartAITools",
    "url": "https://startaitools.com"
  },
  "articleSection": "Technical Deep-Dive",
  "keywords": "ai-agents, claude-code, security, mcp, architecture",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://startaitools.com/posts/gate-the-statement-not-the-tool-name/"
  }
}
</script>
