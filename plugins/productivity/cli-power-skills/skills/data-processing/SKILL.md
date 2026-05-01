---
name: data-processing
description: "Use when working with structured data files (CSV, JSON, YAML, TOML, Parquet) — querying, transforming, filtering, aggregating, or converting between formats"
allowed-tools: [Bash(jq*), Bash(yq*), Bash(gron*), Bash(mlr*), Bash(xsv*), Bash(duckdb*), Read, Glob, Grep]
version: 1.0.0
author: ykotik
license: MIT
---

# Data Processing

## When to Use
- Querying, filtering, or transforming JSON files
- Reading or converting YAML, TOML, or XML config files
- Analyzing, aggregating, or joining CSV/TSV/Parquet files
- Running SQL queries against local data files without a database server
- Converting between data formats (JSON to YAML, CSV to JSON, etc.)
- Exploring deeply nested JSON structures

## Tools

| Tool | Purpose | Structured output |
|------|---------|-------------------|
| **jq** | Query and transform JSON | Native JSON |
| **yq** | Query and transform YAML, TOML, XML | `-o json` for JSON output |
| **gron** | Flatten JSON into greppable `path.to.key = value` lines | `--ungron` to reverse back to JSON |
| **miller (mlr)** | Transform CSV/JSON/TSV records with awk-like verbs | `--json` for JSON output |
| **xsv** | Fast CSV slicing, searching, joining, statistics | CSV native (pipe to `xsv table` for display) |
| **DuckDB** | SQL queries on CSV, JSON, Parquet files | `-json` flag for JSON output |

## Patterns

### JSON: Filter array elements by field value
```bash
jq '.items[] | select(.status == "active")' data.json
```

### JSON: Extract specific fields from array
```bash
jq '[.users[] | {name: .name, email: .email}]' data.json
```

### JSON: Count items grouped by field
```bash
jq '[.events[] | .type] | group_by(.) | map({type: .[0], count: length})' data.json
```

### YAML: Read a nested value
```bash
yq '.spec.containers[0].image' deployment.yaml
```

### YAML: Convert entire file to JSON
```bash
yq -o json config.yaml
```

### TOML: Read a value
```bash
yq -p toml '.database.host' config.toml
```

### JSON: Explore unknown structure by grepping paths
```bash
gron data.json | grep -i "error"
```

### CSV: Column statistics (min, max, mean, stddev)
```bash
xsv stats data.csv | xsv table
```

### CSV: Search rows matching a pattern in a column
```bash
xsv search -s status "active" data.csv
```

### CSV: Select specific columns
```bash
xsv select name,email,created_at users.csv
```

### CSV: Sort by column
```bash
xsv sort -s revenue -R sales.csv
```

### SQL: Query a CSV file
```bash
duckdb -c "SELECT department, COUNT(*) as cnt, AVG(salary) as avg_sal FROM 'employees.csv' GROUP BY department ORDER BY avg_sal DESC"
```

### SQL: Query a JSON file
```bash
duckdb -c "SELECT * FROM read_json_auto('events.json') WHERE type = 'error' LIMIT 20"
```

### SQL: Query Parquet files
```bash
duckdb -c "SELECT * FROM 'data/*.parquet' WHERE created_at > '2026-01-01'"
```

### CSV/JSON: Transform records with miller
```bash
mlr --csv filter '$revenue > 1000' then sort-by -nr revenue sales.csv
```

### Format conversion: CSV to JSON
```bash
mlr --icsv --ojson cat data.csv
```

## Pipelines

### YAML config → JSON → SQL query
```bash
yq -o json config.yaml | duckdb -c "SELECT key, value FROM read_json_auto('/dev/stdin') WHERE env = 'production'"
```
Each stage: yq converts YAML to JSON, DuckDB runs SQL on the JSON stream.

### Grep nested JSON paths → reconstruct matching subset
```bash
gron large.json | grep "\.errors\[" | gron --ungron
```
Each stage: gron flattens JSON to paths, grep filters, ungron reconstructs valid JSON from matches.

### CSV filter → aggregate with SQL
```bash
xsv search -s region "EU" sales.csv | duckdb -c "SELECT product, SUM(revenue) as total FROM read_csv_auto('/dev/stdin') GROUP BY product ORDER BY total DESC"
```
Each stage: xsv filters rows by region, DuckDB aggregates the filtered stream.

### Join two CSV files with SQL
```bash
duckdb -c "SELECT u.name, u.email, o.total, o.date FROM 'users.csv' u JOIN 'orders.csv' o ON u.id = o.user_id ORDER BY o.date DESC"
```

### Multi-format pipeline: JSON → CSV → stats
```bash
jq -r '.records[] | [.name, .score] | @csv' data.json | xsv stats
```
Each stage: jq extracts fields to CSV format, xsv computes statistics.

## Prefer Over
- Prefer **DuckDB** over Python/pandas for ad-hoc SQL queries on files — single command, no script, handles large files
- Prefer **jq** over Python `json` module for one-off JSON transforms — single pipeline vs. multi-line script
- Prefer **xsv** over `awk`/`cut` for CSV operations — correct CSV parsing, handles quoted fields and escapes
- Prefer **miller** over `awk` for format-aware record transformations — understands CSV/JSON headers natively
- Prefer **yq** over custom parsers for config file reads — handles YAML, TOML, XML with consistent syntax

## Do NOT Use When
- Data is already in a running database — query the database directly
- File is under 10 lines — just use the Read tool and process in-context
- Task requires complex multi-step logic with conditionals — write a Python script instead
- JSON is simple enough to read by eye — use the Read tool, don't over-engineer
- Working with binary or non-structured data formats
