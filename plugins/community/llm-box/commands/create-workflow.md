---
name: create-workflow
description: Generate a YAML workflow from natural language
usage: /aflare:create-workflow "<description>"
---

# Create Workflow

Generate a YAML workflow file from a natural language description.

## Usage

```
/aflare:create-workflow "<description>"
```

## Examples

```
/aflare:create-workflow "Fetch the GitHub trending page and save to file"
/aflare:create-workflow "Read package.json and generate release notes"
/aflare:create-workflow "Fetch news from multiple sources and summarize with Ollama"
```

## What it does

1. Parses your natural language description
2. Generates a structured YAML workflow
3. Saves it to the current directory
4. Shows you the workflow steps

## Next steps

After creating a workflow, you can:
- Edit the YAML file manually to tweak things
- Run it with `/aflare:run-workflow <filename>`
- Validate it with `/aflare:validate-workflow <filename>`