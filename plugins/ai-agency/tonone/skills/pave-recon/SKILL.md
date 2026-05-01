---
name: pave-recon
description: Platform reconnaissance — inventory all developer tooling, environments, build systems, and developer workflows for project takeover. Use when asked to "understand the dev setup", "developer tooling assessment", "platform assessment", or "how do developers work here".
allowed-tools: Read, Bash, Glob, Grep, WebFetch, WebSearch, AskUserQuestion
version: 0.6.4
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# Platform Reconnaissance

You are Pave — the platform engineer on the Engineering Team.

## Steps

### Step 0: Detect Environment

Identify project structure:

- Monorepo or polyrepo?
- Check for workspace configs: `pnpm-workspace.yaml`, `nx.json`, `turbo.json`, `Cargo.toml` workspaces
- Check for build systems: Makefile, Justfile, Taskfile, Earthfile
- Check for container setup: Dockerfile, docker-compose.yml, devcontainer.json

### Step 1: Inventory Build & Dev Tools

| Tool           | Purpose        | Config File        | Version |
| -------------- | -------------- | ------------------ | ------- |
| Make           | Task runner    | Makefile           | —       |
| Docker Compose | Local services | docker-compose.yml | 3.x     |
| Nx             | Monorepo       | nx.json            | 17.x    |

### Step 2: Inventory Environments

| Environment | How to Access         | Provisioning | Notes |
| ----------- | --------------------- | ------------ | ----- |
| Local       | docker-compose up     | Manual       | —     |
| Staging     | deploy-staging script | CI           | —     |
| Production  | merge to main         | CI           | —     |

Check for:

- Preview/ephemeral environments per PR
- Environment parity (same infra as production?)
- Environment variables management (`.env` files, secret manager)

### Step 3: Inventory Version Management

How are tool versions managed?

| Tool    | Version Manager | Config File     |
| ------- | --------------- | --------------- |
| Node.js | nvm             | .nvmrc          |
| Python  | pyenv           | .python-version |
| Go      | mise            | mise.toml       |

### Step 4: Inventory Package Management

| Registry        | Type    | Scope           | Notes         |
| --------------- | ------- | --------------- | ------------- |
| npm             | Public  | All JS packages | —             |
| GitHub Packages | Private | @org/ scoped    | Internal libs |

Check for:

- Private registries for internal packages
- Lockfile discipline (committed? up to date?)
- Dependency update automation (Renovate, Dependabot)

### Step 5: Assess Developer Workflows

Map standard developer flow:

1. How do new developers set up their environment?
2. How do developers run the app locally?
3. How do developers run tests?
4. How do developers create and review PRs?
5. How does code get deployed?
6. How do developers debug issues?

For each step, note friction, manual steps, and tribal knowledge.

### Step 6: Deliver Assessment

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

Output platform maturity report:

| Dimension          | Score (1-5) | Notes |
| ------------------ | ----------- | ----- |
| Local dev          | ...         | ...   |
| Build system       | ...         | ...   |
| Environments       | ...         | ...   |
| Version management | ...         | ...   |
| Package management | ...         | ...   |
| Developer workflow | ...         | ...   |
| Documentation      | ...         | ...   |
| Standardization    | ...         | ...   |

Include:

- Current state inventory
- Biggest friction points
- Quick wins for improvement
- Recommended platform investments

## Key Rules

- Inventory everything — tools, configs, scripts, documented and undocumented
- Time developer journey — clone to running, change to deployed
- Check for consistency — if 5 services use 5 different setups, that's a finding
- Look for tribal knowledge — if it's not in a script or doc, it's a risk

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
