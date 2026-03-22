---
name: windsurf-prod-checklist
description: |
  Execute Windsurf production readiness checklist for team and enterprise deployments.
  Use when rolling out Windsurf to a team, preparing for enterprise deployment,
  or auditing production configuration.
  Trigger with phrases like "windsurf production", "windsurf team rollout",
  "windsurf go-live", "windsurf enterprise deploy", "windsurf checklist".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, deployment, enterprise, checklist]

---
# Windsurf Production Checklist

## Overview
Complete checklist for rolling out Windsurf to production teams. Covers workspace configuration, security hardening, team onboarding, and monitoring.

## Prerequisites
- Windsurf plan selected (Pro, Teams, or Enterprise)
- Admin access to Windsurf dashboard
- Git repositories identified for rollout
- Team agreement on AI usage policy

## Instructions

### Phase 1: Pre-Deployment Configuration

**Workspace Config (per repository):**
- [ ] `.windsurfrules` created with project stack, patterns, and constraints
- [ ] `.codeiumignore` excludes secrets, build artifacts, and large binaries
- [ ] `.windsurf/rules/` contains glob-triggered rules for file-type-specific patterns
- [ ] Workspace settings committed to `.windsurf/settings.json`

**Security:**
- [ ] Telemetry configured per company policy
- [ ] `.codeiumignore` covers all secret file patterns
- [ ] Autocomplete disabled for secret-containing file types (.env, .key)
- [ ] Enterprise: SSO/SAML configured and enforced
- [ ] Enterprise: zero-data-retention verified with Codeium

**Team Policy:**
- [ ] AI usage policy document created and shared
- [ ] Commit convention for AI-generated code established (e.g., `[cascade]` prefix)
- [ ] Code review requirements for AI-generated changes defined
- [ ] Competing AI extensions disabled (Copilot, TabNine)

### Phase 2: Team Onboarding

**Per-Developer Setup:**
```bash
#!/bin/bash
# scripts/setup-windsurf.sh — run on each developer machine

echo "Setting up Windsurf for this project..."

# Verify Windsurf is installed
windsurf --version || { echo "Install Windsurf first: https://windsurf.com/download"; exit 1; }

# Verify config files exist
[ -f .windsurfrules ] || echo "WARNING: .windsurfrules missing"
[ -f .codeiumignore ] || echo "WARNING: .codeiumignore missing"

# Install recommended extensions
windsurf --install-extension esbenp.prettier-vscode
windsurf --install-extension dbaeumer.vscode-eslint

# Disable conflicting extensions
windsurf --disable-extension github.copilot 2>/dev/null || true

echo "Setup complete. Open project folder (not monorepo root) for best AI context."
```

**Training Checklist:**
- [ ] Demo: Supercomplete (Tab) vs Cascade (Cmd+L) vs Command (Cmd+I)
- [ ] Demo: Write mode vs Chat mode
- [ ] Demo: @ mentions for file context
- [ ] Demo: Turbo mode with allow/deny lists
- [ ] Demo: Previews for UI development
- [ ] Demo: Git checkpoint before Cascade workflow
- [ ] Share: `.windsurfrules` explained
- [ ] Share: Credit system and model selection

### Phase 3: Monitoring and Optimization

**Admin Dashboard Monitoring:**
```yaml
# Metrics to track weekly (Admin Dashboard > Analytics)
metrics:
  adoption:
    - active_users_vs_total_seats    # target: >80%
    - daily_active_users             # trend: increasing
  quality:
    - completion_acceptance_rate     # target: >25%
    - cascade_success_rate           # target: >70%
  efficiency:
    - credits_consumed_per_user      # watch for outliers
    - tasks_completed_per_day        # proxy for productivity
```

**Quarterly Review:**
- [ ] Audit seat utilization -- downgrade inactive seats
- [ ] Review `.windsurfrules` -- update with new patterns
- [ ] Check for new Windsurf features in changelog
- [ ] Survey team satisfaction and pain points
- [ ] Analyze credit usage patterns

### Phase 4: Rollback Procedure

If Windsurf causes issues:
```
1. Disable Cascade for team: Admin Dashboard > Features > Cascade > Off
2. Developers can still use Supercomplete (non-agentic)
3. Switch to manual coding while investigating
4. Review recent Cascade-generated commits for issues
5. File support ticket with debug bundle (see windsurf-debug-bundle)
```

## Error Handling
| Issue | Severity | Mitigation |
|-------|----------|------------|
| Cascade generates broken code | Medium | Enforce tests-pass-before-merge policy |
| AI exposes secrets in suggestions | High | Audit `.codeiumignore`, rotate exposed secrets |
| Team not adopting | Low | Training session, share productivity data |
| Credits exhausted mid-sprint | Medium | Monitor usage, buy additional credits proactively |

## Examples

### Recommended Extension Set
```json
// .vscode/extensions.json (also works in Windsurf)
{
  "recommendations": [
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "biomejs.biome"
  ],
  "unwantedRecommendations": [
    "github.copilot",
    "tabnine.tabnine-vscode"
  ]
}
```

### Quick Compliance Check
```bash
set -euo pipefail
echo "Config: $([ -f .windsurfrules ] && echo 'OK' || echo 'MISSING')"
echo "Ignore: $([ -f .codeiumignore ] && echo 'OK' || echo 'MISSING')"
echo "Rules:  $([ -d .windsurf/rules ] && echo 'OK' || echo 'MISSING')"
```

## Resources
- [Windsurf Admin Guide](https://docs.windsurf.com/windsurf/guide-for-admins)
- [Windsurf Enterprise](https://windsurf.com/enterprise)
- [Windsurf Security](https://windsurf.com/security)

## Next Steps
For version upgrades, see `windsurf-upgrade-migration`.
