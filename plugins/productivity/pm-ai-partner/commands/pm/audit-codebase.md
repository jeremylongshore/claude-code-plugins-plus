---
name: audit-codebase
description: PM-focused codebase exploration and capability mapping
allowed-tools: Read, Glob, Grep
---

Help me understand the codebase for: $ARGUMENTS

## Instructions

Conduct a PM-focused codebase exploration. The goal is not to understand every line of code, but to map **what the system can do** and **what that means for the product**.

### Process

1. **Auto-detect structure** — Identify language, framework, repo layout, entry points
2. **Explore architecture** — Map services, components, data flows, and external dependencies
3. **Map capabilities** — What product capabilities does this code enable?
4. **Find the gaps** — What's claimed in docs but missing in code? What exists but isn't documented?
5. **Connect to product decisions** — What does this mean for what we can build, change, or promise?

### Tools to Use

- Search the codebase for key patterns, APIs, and data models
- Read configuration files, READMEs, and service definitions
- Trace user-facing flows from entry point to data store
- Compare implementation reality to documentation claims
- **GitHub MCP** (if available): Pull open issues, recent PRs, contributor activity for context on what's changing
- **Sentry MCP** (if available): Check for recurring errors or performance issues in this service

### Auto-Detection

Start by detecting the repo's characteristics:

```markdown
## Repo Profile
- **Language(s):** [auto-detect from file extensions and config]
- **Framework:** [detect from package.json, pom.xml, build.gradle, etc.]
- **Architecture:** [monolith / microservice / monorepo / library]
- **Entry points:** [main files, server startup, route definitions]
- **Data stores:** [databases, caches, queues detected from config/code]
- **External deps:** [APIs, services this code calls]
```

### Output Format

```markdown
# Codebase Audit: [System/Service Name]

## One-Sentence Summary
What this system does in plain language.

## Repo Profile
| Attribute | Value |
|-----------|-------|
| Language | [detected] |
| Framework | [detected] |
| Architecture | [type] |
| Size | [files/lines estimate] |

## Architecture Overview

[Mermaid diagram showing key components, data flow, and external dependencies]

## Capability Map
| Capability | Status | Evidence | Product Implication |
|------------|--------|----------|---------------------|
| [Feature] | Exists/Partial/Missing | [file/pattern] | [What this means for PM decisions] |

## API Surface
| Endpoint/Interface | Method | Purpose | Notes |
|--------------------|--------|---------|-------|
| [path or function] | [GET/POST/etc] | [what it does] | [rate limits, auth, quirks] |

## Data Model
| Entity | Key Fields | Relationships | PM Relevance |
|--------|-----------|---------------|--------------|
| [model] | [fields] | [links to other models] | [what this means for features] |

## Key Findings
1. **[Finding]** — [Evidence] → [Product implication]
2. **[Finding]** — [Evidence] → [Product implication]

## Gap Inventory
| Expected (from docs) | Reality (from code) | Impact |
|----------------------|---------------------|--------|

## Questions for Engineering
- [Things code can't answer alone]

## Recommendations
1. [Action item with evidence backing]
```

### Principles

- **Evidence over assumption** — Cite file paths and code patterns
- **Product language** — Translate technical findings into PM-relevant insights
- **Honest about limits** — Flag what you can't determine from code alone
- **Mermaid for diagrams** — Use Mermaid format for architecture diagrams, not ASCII art
- **Auto-detect first** — Don't ask the user for repo details you can discover by reading the code
