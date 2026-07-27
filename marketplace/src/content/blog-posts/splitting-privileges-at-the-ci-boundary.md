---
title: "Splitting Privileges at the CI Boundary"
description: "Fork CI privilege separation in GitHub Actions prevents secret exfiltration. Run untrusted fork code and trusted deterministic steps safely."
date: "2026-07-24"
tags: ["ci-cd", "devops", "automation", "claude-code"]
featured: false
---
## The Fork Privilege Split

Fork PRs and main-repo PRs need different CI guardrails. A fork can't read repository secrets. The main repo can. GitHub Actions knows the difference. The move is to use pull_request_target for the privileged half and pull_request for the unprivileged half.

This is the whole game. If you run secret-reading steps against fork code, those secrets leak. If you run untrusted fork code with base-repo secrets available, game over. Split the workflow. Run the trusted half against the merge base only. Let the untrusted fork code run sandboxed.

```yaml
on:
  pull_request_target:
    # Runs in base-repo context, can read secrets
    # Only run deterministic, audited steps here
    
  pull_request:
    # Runs in fork context, no secrets
    # Fork code goes here
```

PR #1126 split claude-code-plugins prescreen into this two-trigger pattern. Also switched the LLM to MiniMax. Related CI improvements: #1124 filtered redundant automated reviews, #1123 quieted failed prescreen LLM summaries, #1127 added a UIZZE skill source.

## Reject Bad State at the Boundary

intent-os B1.2d landed a zero-unexplained-delta reconciliation validator (PR #224). Every delta between discovered state and governed state must be explained or the validator fails closed. Committed a registry. Added a read-only status page so anyone can see what is out of sync and why.

Same thread, collector hardening (PR #222). If a prior snapshot is corrupt, refuse to guess. If a scope only partially enumerates, keep the partial truth and mark it degraded instead of pretending it is complete. State machines that reject silence are more reliable than systems that invent.

MXroute DNS migration prep (PR #225) wrapped the API family and captured the key in SOPS. Pre-seed the domain-verify TXT record via Porkbun before any deploy touches it. State gets written and audited before it ships.

## Database Migration Discipline

now-lms OSS contribution hit column migrations. Renamed a column to csrf_seed with a robust migration path. Widened programa nombre and codigo to handle edge cases. Added precision and scale to a monetary column so MySQL doesn't round money during a read. Multi-database test stability fixes so migrations pass on PostgreSQL and SQLite, not just MySQL. Schema changes that work everywhere reduce the likelihood of production surprises.

## Boundary Theme

The pattern across three repos on one day: fork CI (trust boundary), reconciliation validation (state boundary), collector degradation (partial-truth boundary), database migrations (schema boundary). Every gate says the same thing. Reject bad state before it becomes durable state. Do not invent. Do not guess. Do not pretend. Fail closed. Preserve what you know. This is the discipline that prevents Friday 3 AM incidents.

## Related Posts

- [Wrong Mode Green is Not a Gate](/posts/wrong-mode-green-is-not-a-gate/)
- [Temporary is Not a Plan](/posts/temporary-is-not-a-plan/)
- [Passing is Not Validating](/posts/passing-is-not-validating/)
