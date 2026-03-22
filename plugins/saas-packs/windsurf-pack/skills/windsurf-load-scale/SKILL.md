---
name: windsurf-load-scale
description: |
  Scale Windsurf adoption across large organizations with workspace strategies and performance tuning.
  Use when rolling out Windsurf to 50+ developers, managing large monorepo workspaces,
  or planning enterprise-scale deployment.
  Trigger with phrases like "windsurf at scale", "windsurf large team",
  "windsurf monorepo", "windsurf organization", "windsurf 100 developers".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, scaling, enterprise, large-team]

---
# Windsurf Load & Scale

## Overview
Strategies for deploying Windsurf AI IDE across large organizations (50-1000+ developers). Covers workspace partitioning for monorepos, configuration distribution, credit budgeting, and performance at scale.

## Prerequisites
- Windsurf Teams or Enterprise plan
- Admin dashboard access
- Understanding of team structure and repository layout
- Network/IT involvement for enterprise features

## Instructions

### Step 1: Workspace Strategy for Large Codebases

```yaml
# Windsurf performance degrades with workspace size
# Cascade context quality inversely correlates with file count

workspace_sizing:
  optimal: "<5,000 files — fast indexing, precise Cascade context"
  acceptable: "5,000-20,000 files — add .codeiumignore, expect slower indexing"
  problematic: "20,000+ files — must partition into sub-workspaces"
  unworkable: "100,000+ files at root — Cascade context diluted, indexing very slow"

# Strategy: one Windsurf window per service/package
# Each developer opens their assigned service directory
```

### Step 2: Monorepo Partitioning

```
# Large monorepo (100K+ files)
company-monorepo/
├── .windsurfrules              # Brief shared conventions only
├── .codeiumignore              # Aggressive: exclude EVERYTHING except src
├── apps/
│   ├── web-app/                # Developer A opens this window
│   │   ├── .windsurfrules      # Next.js-specific AI context
│   │   └── .codeiumignore      # Local exclusions
│   ├── mobile-app/             # Developer B opens this window
│   │   ├── .windsurfrules      # React Native context
│   │   └── .codeiumignore
│   └── admin-portal/           # Developer C opens this window
│       ├── .windsurfrules
│       └── .codeiumignore
├── services/
│   ├── api-gateway/            # Backend team opens individual services
│   ├── auth-service/
│   ├── payment-service/
│   └── notification-service/
├── packages/
│   └── shared-types/           # Library maintainer opens this
└── infrastructure/
    └── terraform/              # DevOps opens this
```

**Rule:** Never open the monorepo root in Windsurf. Each developer opens their service directory.

### Step 3: Configuration Distribution at Scale

```yaml
# Central config repo for team-wide standards
windsurf-config/
├── templates/
│   ├── windsurfrules/
│   │   ├── nextjs.md           # Template for Next.js projects
│   │   ├── fastify.md          # Template for Fastify APIs
│   │   ├── react-native.md     # Template for mobile apps
│   │   └── shared-library.md   # Template for shared packages
│   ├── codeiumignore/
│   │   ├── node-project.ignore
│   │   ├── python-project.ignore
│   │   └── go-project.ignore
│   └── workflows/
│       ├── deploy-staging.md
│       ├── pr-review.md
│       └── quality-check.md
├── scripts/
│   ├── setup-windsurf.sh       # Onboarding script
│   └── sync-config.sh          # Distribute updates
└── README.md
```

**Sync script:**
```bash
#!/bin/bash
set -euo pipefail
# scripts/sync-config.sh — run from monorepo root

TEMPLATE_DIR="/path/to/windsurf-config/templates"

for service_dir in apps/*/  services/*/; do
  [ -d "$service_dir" ] || continue
  SERVICE=$(basename "$service_dir")

  # Copy .codeiumignore if missing
  [ -f "$service_dir/.codeiumignore" ] || \
    cp "$TEMPLATE_DIR/codeiumignore/node-project.ignore" "$service_dir/.codeiumignore"

  # Copy shared workflows
  mkdir -p "$service_dir/.windsurf/workflows"
  cp "$TEMPLATE_DIR/workflows/"*.md "$service_dir/.windsurf/workflows/" 2>/dev/null || true

  echo "Synced: $SERVICE"
done
```

### Step 4: Credit Budgeting at Scale

```yaml
# Credit planning for large teams
credit_budget:
  team_size: 100

  tier_allocation:
    power_users: 20       # Pro: heavy Cascade users (senior devs, architects)
    regular_users: 50     # Pro: daily Supercomplete + occasional Cascade
    light_users: 20       # Free: reviewers, designers, PMs with code access
    contractors: 10       # Free: temporary, limited AI needs

  monthly_cost:
    pro_seats: 70 x $30 = $2,100
    free_seats: 30 x $0 = $0
    total: $2,100/month

  vs_alternative:
    cursor_equivalent: 70 x $20 = $1,400  # But fewer features
    copilot_equivalent: 100 x $19 = $1,900  # No agentic features

  optimization:
    quarterly_review: "Audit usage, downgrade inactive seats"
    training_program: "Monthly 30-min workshop for new features"
    workflow_investment: "Build team workflows to reduce per-user credit waste"
```

### Step 5: Enterprise Network Configuration

```yaml
# IT/Network team requirements
network_config:
  endpoints_to_whitelist:
    - "*.codeium.com"          # AI inference
    - "*.windsurf.com"         # Auth, updates, admin portal
    - "windsurf.com"           # Downloads, documentation

  proxy_support:
    http_proxy: "${HTTP_PROXY}"
    https_proxy: "${HTTPS_PROXY}"
    no_proxy: "localhost,127.0.0.1,.internal.company.com"
    # Set via Windsurf Settings or environment variables

  deployment_modes:
    cloud: "Standard — code context sent to Codeium cloud"
    hybrid: "Code stays local, only prompts sent to cloud"
    self_hosted: "Everything on-prem (Enterprise plan required)"
```

### Step 6: Onboarding Automation

```bash
#!/bin/bash
set -euo pipefail
# Large-team onboarding script

echo "=== Windsurf Team Onboarding ==="

# 1. Install Windsurf
if ! command -v windsurf &>/dev/null; then
  echo "Installing Windsurf..."
  brew install --cask windsurf 2>/dev/null || {
    echo "Download from: https://windsurf.com/download"
    exit 1
  }
fi

# 2. Import existing editor settings
echo "Importing VS Code settings..."
windsurf 2>/dev/null &  # First launch imports settings
sleep 3
kill %1 2>/dev/null || true

# 3. Install approved extensions
EXTENSIONS=(
  "esbenp.prettier-vscode"
  "dbaeumer.vscode-eslint"
  "biomejs.biome"
)
for ext in "${EXTENSIONS[@]}"; do
  windsurf --install-extension "$ext" 2>/dev/null
done

# 4. Disable conflicting extensions
CONFLICTS=("github.copilot" "tabnine.tabnine-vscode")
for ext in "${CONFLICTS[@]}"; do
  windsurf --disable-extension "$ext" 2>/dev/null || true
done

# 5. Set team config
echo "Configuring team settings..."
echo ""
echo "Complete. Next steps:"
echo "1. Open your service directory in Windsurf (not monorepo root)"
echo "2. Sign in with company SSO when prompted"
echo "3. Verify .windsurfrules exists in your service directory"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Indexing slow across team | Large workspaces | Partition into sub-workspaces per service |
| Config drift between services | No central templates | Implement sync-config.sh script |
| Credit overspend | No budgeting | Implement tier allocation, quarterly review |
| Network blocking Windsurf | Firewall rules | Whitelist *.codeium.com and *.windsurf.com |
| Inconsistent AI suggestions | Different .windsurfrules | Use central template repository |

## Examples

### Quick Team Health Dashboard
```bash
echo "=== Team Windsurf Health ==="
echo "Services with .windsurfrules:"
find . -maxdepth 3 -name ".windsurfrules" | wc -l
echo "Services with .codeiumignore:"
find . -maxdepth 3 -name ".codeiumignore" | wc -l
echo "Services without config (needs fix):"
for d in apps/* services/*; do
  [ -d "$d" ] || continue
  [ -f "$d/.windsurfrules" ] || echo "  MISSING: $d/.windsurfrules"
done
```

## Resources
- [Windsurf Enterprise](https://windsurf.com/enterprise)
- [Windsurf Admin Guide](https://docs.windsurf.com/windsurf/guide-for-admins)

## Next Steps
For reliability patterns, see `windsurf-reliability-patterns`.
