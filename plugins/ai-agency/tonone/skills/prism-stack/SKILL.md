---
name: prism-stack
description: |
  Use when asked for framework-specific best practices, implementation guidelines
  for React/Vue/Svelte/Next.js, or stack-specific patterns. Examples: "React best
  practices", "Vue component patterns", "Next.js performance"
allowed-tools: Read, Bash, Glob, Grep
version: 0.6.6
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# prism-stack — Framework Best Practices

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## When to use

User asks about framework-specific patterns, component architecture, or stack guidelines.

## Workflow

1. **Detect stack** from project files (package.json, imports, config files)
   ```bash
   grep -r "\"react\"\|\"vue\"\|\"svelte\"\|\"next\"\|\"nuxt\"\|\"astro\"" package.json 2>/dev/null | head -5
   ```
2. **Search stack knowledge base:**
   ```bash
   python3 -m prism_agent.uiux search --domain stacks --query "{stack_name}" --limit 5
   ```
3. **Cross-reference version** — confirm guidelines match the detected major version
4. **Output** framework-specific guidelines with code examples

## Output format

```
┌─ Stack Guidelines — {stack_name} {version} ─────────────────────────┐
│ Category         │ Guideline                          │ Severity      │
├──────────────────┼────────────────────────────────────┼───────────────┤
│ {category}       │ {guideline}                        │ Critical      │
│ {category}       │ {guideline}                        │ High          │
│ {category}       │ {guideline}                        │ Medium        │
└──────────────────┴────────────────────────────────────┴───────────────┘

Code example:
{code_block}
```

## Anti-patterns

- Never apply guidelines from the wrong framework version (e.g., Vue 2 patterns on Vue 3)
- Never mix framework idioms (e.g., React hooks inside Vue components)
- Never skip version detection — always confirm before outputting guidelines
- Never output framework-agnostic advice when stack-specific guidance is available

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
