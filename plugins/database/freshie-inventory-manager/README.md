# Freshie Inventory Manager

Unified command center for the freshie ecosystem inventory database. Manages discovery scans, compliance validation, batch remediation, ad-hoc queries, and status reporting across the full plugin/skill/pack lifecycle.

## Installation

```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
```

## Usage

Invoke with natural language:

- `freshie status` — dashboard with run counts, grades, staleness
- `run a discovery scan` — trigger rebuild-inventory.py
- `compliance check` — validate and populate DB with enterprise grading
- `remediate skills` — batch fix compliance issues
- `query freshie for stub skills` — ad-hoc SQLite queries
- `freshie report` — generate a status update summary
- `compare discovery runs` — delta analysis between runs
- `show pack coverage` — SaaS pack completeness metrics
- `find anomalies` — detect data quality issues
- `export grades to CSV` — export compliance data

## Features

- Pre-loaded DB status via dynamic context injection
- 10 distinct operations with automatic intent detection
- Pre-built query library for common investigations
- Delta reporting between discovery runs
- Dry-run-first remediation safety pattern

## Requirements

- `sqlite3` CLI
- `python3` with `pyyaml`
- Freshie database at `freshie/inventory.sqlite`

## Files

- `skills/freshie-inventory/SKILL.md` — Main skill definition
- `skills/freshie-inventory/references/common-queries.md` — Pre-built SQLite query library

## License

MIT
