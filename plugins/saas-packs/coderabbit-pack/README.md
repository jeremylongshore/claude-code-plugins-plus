# CodeRabbit Skill Pack

> Claude Code skill pack for CodeRabbit AI code review (24 skills)

## Installation

```bash
/plugin install coderabbit-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `coderabbit-install-auth` | Install CodeRabbit GitHub/GitLab App, configure CLI, verify setup |
| `coderabbit-hello-world` | Minimal .coderabbit.yaml config and first AI review quickstart |
| `coderabbit-local-dev-loop` | CodeRabbit CLI for local pre-commit reviews, git hooks, IDE integration |
| `coderabbit-sdk-patterns` | GitHub API automation patterns for processing CodeRabbit review data |
| `coderabbit-core-workflow-a` | Primary review workflow: .coderabbit.yaml config, path instructions, review lifecycle |
| `coderabbit-core-workflow-b` | Review tuning: learnings, code guidelines, tone, noise reduction |
| `coderabbit-common-errors` | Troubleshoot CodeRabbit issues: no reviews, config errors, noise |
| `coderabbit-debug-bundle` | Collect diagnostic info for CodeRabbit support tickets |
| `coderabbit-rate-limits` | Handle GitHub API and CodeRabbit command rate limits in automation |
| `coderabbit-security-basics` | Security-focused review config: secret detection, vulnerability scanning |
| `coderabbit-prod-checklist` | Production readiness checklist for enforcing CodeRabbit as a merge gate |
| `coderabbit-upgrade-migration` | Adopt new CodeRabbit features, upgrade plans, update config schema |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `coderabbit-ci-integration` | CodeRabbit as a CI gate with GitHub Actions and branch protection |
| `coderabbit-deploy-integration` | Multi-repo org rollout, shared config, team onboarding |
| `coderabbit-webhooks-events` | GitHub webhook handling for CodeRabbit review events and notifications |
| `coderabbit-performance-tuning` | Optimize review speed, relevance, and signal-to-noise ratio |
| `coderabbit-cost-tuning` | Seat management, repo scoping, and billing optimization |
| `coderabbit-reference-architecture` | Production-grade reference .coderabbit.yaml with full path instructions |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `coderabbit-multi-env-setup` | Per-branch review config for dev, staging, and production |
| `coderabbit-observability` | Review metrics dashboards, coverage tracking, alerting |
| `coderabbit-incident-runbook` | Emergency procedures when CodeRabbit blocks PRs or stops reviewing |
| `coderabbit-data-handling` | Sensitive file exclusion, PII protection, secret detection rules |
| `coderabbit-enterprise-rbac` | Enterprise access control, seat management, org-level policies |
| `coderabbit-migration-deep-dive` | Migrate from other review tools (Codacy, SonarCloud, DeepSource) |

## Usage

Skills trigger automatically when you discuss CodeRabbit topics. For example:

- "Help me set up CodeRabbit" triggers `coderabbit-install-auth`
- "Configure CodeRabbit for my project" triggers `coderabbit-core-workflow-a`
- "Debug CodeRabbit not reviewing PRs" triggers `coderabbit-common-errors`
- "Set up CodeRabbit as a required check" triggers `coderabbit-ci-integration`
- "Reduce CodeRabbit costs" triggers `coderabbit-cost-tuning`
- "Migrate from Codacy to CodeRabbit" triggers `coderabbit-migration-deep-dive`

## What is CodeRabbit?

[CodeRabbit](https://coderabbit.ai) is an AI-powered code review platform that installs as a GitHub/GitLab App. It automatically reviews pull requests, posting walkthrough summaries and line-level suggestions. Configuration is done via `.coderabbit.yaml` in your repository root.

## License

MIT
