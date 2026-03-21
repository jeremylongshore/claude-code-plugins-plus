# Severity1 Marketplace

Severity level classification and prompt improvement for Claude Code marketplace plugins.

## Features

- **Severity Classification**: Assigns severity ratings (S1-Critical, S2-High, S3-Medium, S4-Low) to security findings, bugs, and issues
- **Prompt Improver**: Analyzes and enhances plugin prompts for clarity, safety, effectiveness, and best-practice adherence
- **Triage Agent**: Automated severity triage for incoming issues and vulnerability reports

## Severity Levels

| Level | Label | Description |
|-------|-------|-------------|
| S1 | Critical | System-down, data loss, security breach — immediate action required |
| S2 | High | Major functionality broken, security vulnerability — urgent resolution |
| S3 | Medium | Degraded functionality, workaround available — scheduled fix |
| S4 | Low | Minor issue, cosmetic, enhancement request — backlog |

## Commands

- `/severity-classify` — Classify an issue or finding by severity level
- `/prompt-improve` — Analyze and improve a plugin prompt or skill definition

## Skills

- **prompt-improver** — Auto-activates when users ask to improve, review, or enhance prompts, skill definitions, or command instructions

## Agents

- **severity-triage** — Automated severity triage agent for issues and vulnerabilities

## Installation

```bash
claude plugin marketplace add severity1/severity1-marketplace
```

## Usage

```
/severity-classify "Users can bypass authentication by..."
/prompt-improve
```

## Contributors

- severity1

## License

MIT
