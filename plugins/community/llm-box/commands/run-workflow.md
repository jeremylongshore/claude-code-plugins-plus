---
name: run-workflow
description: Execute a YAML workflow file
usage: /aflare:run-workflow <workflow.yaml>
---

# Run Workflow

Execute a previously created YAML workflow file.

## Usage

```
/aflare:run-workflow <filename>
```

## Examples

```
/aflare:run-workflow my-workflow.yaml
/aflare:run-workflow news-summary.yaml
```

## Options

- **--safe-mode**: Run without execute node (safer)
- **--dry-run**: Show steps without executing
- **--verbose**: Show detailed output

## What it does

1. Loads the YAML workflow file
2. Executes each step in sequence
3. Shows progress and results
4. Handles errors and retries

## Exit codes

- `0`: Success
- `1`: Workflow failed
- `2`: Validation error