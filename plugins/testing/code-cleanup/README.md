# Code Cleanup

Comprehensive codebase cleanup across **11 quality dimensions** with confidence scoring, build verification gates, and specialized agents.

Born from a real cleanup session — 25,000 lines removed, 4 bugs caught — packaged into a reusable Claude Code plugin.

## Quick Start

```bash
# Install
claude /plugin marketplace add jeremylongshore/claude-code-plugins

# Run full cleanup
/cleanup

# Target specific dimensions
/cleanup --dimensions dead,types,security

# Scope to directory
/cleanup src/api/

# Changed files only
/cleanup --changed
```

## The 11 Dimensions

Ordered by risk level (LOW → HIGH):

| # | Dimension | What It Finds | Risk |
|---|-----------|--------------|------|
| 1 | **Dead Code** | Unused exports, imports, variables, unreachable code | LOW |
| 2 | **AI Slop** | Low-value AI-generated comments restating obvious code | LOW |
| 3 | **Weak Types** | `any`, missing return types, overly broad generics | MED |
| 4 | **Security** | Hardcoded secrets, weak crypto, injection vectors | MED |
| 5 | **Legacy Code** | Deprecated APIs, old syntax, unnecessary polyfills | MED |
| 6 | **Type Consolidation** | Duplicate types, interfaces with 80%+ overlap | MED |
| 7 | **Defensive Code** | Unnecessary null checks, impossible error handling | MED |
| 8 | **Performance** | N+1 queries, blocking I/O, bundle bloat | MED |
| 9 | **DRY Deduplication** | Copy-pasted blocks (>=10 identical lines) | HIGH |
| 10 | **Async Patterns** | Floating promises, forEach+async, missing await | HIGH |
| 11 | **Circular Deps** | Module cycles causing init order issues | HIGH |

## Safety First

- **Never auto-applies** high-risk changes — always flags for review
- **Confidence scoring** on every finding (HIGH/MEDIUM/LOW)
- **Build verification gate** after each auto-applied dimension
- **One-command revert** if anything breaks
- Clean git state required before starting

## Agents

11 specialized agents, one per dimension:

- `dead-code-hunter` — finds unreachable and unused code
- `slop-remover` — identifies AI-generated comment noise
- `weak-type-eliminator` — strengthens type annotations
- `security-scanner` — flags secrets, injection vectors, weak crypto
- `legacy-code-remover` — modernizes deprecated patterns
- `type-consolidator` — merges duplicate type definitions
- `defensive-code-cleaner` — removes unnecessary guards
- `performance-optimizer` — spots N+1 queries, blocking I/O, bloat
- `dry-deduplicator` — detects copy-paste code blocks
- `async-pattern-fixer` — catches floating promises and race conditions
- `circular-dep-untangler` — maps and resolves module cycles

## Language Support

Primary: TypeScript, JavaScript, Python
Secondary: Go, Rust (via grep patterns)
Tool integrations: knip, madge, ruff, jscpd, dependency-cruiser, bandit, vulture

## How It Works

1. **Safety checkpoint** — verify clean git state, green tests, record baseline
2. **Scope determination** — full codebase, directory, or changed files
3. **Dimensional scan** — each dimension scans with tools + grep patterns
4. **Confidence scoring** — HIGH (auto-apply), MEDIUM (flag with fix), LOW (flag only)
5. **Build verification** — type check + tests after each auto-applied dimension
6. **Report generation** — summary table, applied changes, flagged items

## License

MIT

## Author

Jeremy Longshore — [Intent Solutions](https://intentsolutions.io)

## Contributors

- Jeremy Longshore ([@jeremylongshore](https://github.com/jeremylongshore))
