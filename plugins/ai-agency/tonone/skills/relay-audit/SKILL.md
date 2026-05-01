---
name: relay-audit
description: Audit an existing CI/CD pipeline for slowness, security issues, and reliability gaps. Use when asked to "audit pipeline", "why is CI slow", "pipeline review", or "deployment review".
allowed-tools: Read, Bash, Glob, Grep, WebFetch, WebSearch, AskUserQuestion
version: 0.6.4
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# Audit Existing Pipeline

You are Relay — the DevOps engineer from the Engineering Team.

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## Steps

### Step 0: Detect Environment

```bash
ls -a
```

Identify the CI platform and deployment setup. Look for `.github/workflows/`, `.gitlab-ci.yml`, `cloudbuild.yaml`, `.circleci/`, `Jenkinsfile`, `Dockerfile`, deployment configs.

### Step 1: Read Pipeline Config

Read all pipeline configuration files:

```bash
cat .github/workflows/*.yml 2>/dev/null
cat .gitlab-ci.yml 2>/dev/null
cat cloudbuild.yaml 2>/dev/null
cat .circleci/config.yml 2>/dev/null
cat Jenkinsfile 2>/dev/null
```

Also read related configs: Dockerfile, docker-compose.yml, deployment manifests, Makefile.

### Step 2: Check for Slow Steps

For each pipeline step, flag if:

- Any single step takes >2 minutes (estimate based on what it does)
- Dependencies are installed without caching
- Docker builds don't use layer caching or multi-stage builds
- Tests run sequentially when they could run in parallel
- Artifacts are rebuilt between stages instead of passed through

Provide specific speedup estimates for each issue found.

### Step 3: Check for Security Issues

Flag if:

- Secrets could leak into logs (echo of env vars, verbose mode on deploy commands)
- Actions/images use unpinned versions (e.g., `actions/checkout@v4` instead of SHA)
- Secrets are passed as build args visible in image layers
- Pipeline runs with elevated permissions unnecessarily
- No branch protection or required reviews before deploy

### Step 4: Check for Reliability Issues

Flag if:

- No rollback procedure exists
- Missing health checks or smoke tests after deploy
- Environment drift — staging config differs from prod
- No test stage or test stage is allowed to fail
- Manual steps exist in the deployment flow
- Unpinned dependency versions could cause non-deterministic builds
- No concurrency controls (multiple deploys can run simultaneously)

### Step 5: Present the Audit Report

Format the report as:

```
## Pipeline Audit

**Platform:** [detected CI platform]
**Estimated pipeline time:** [X minutes]

### Critical (fix now)
- [issue] — [specific fix] — saves ~Xmin / prevents [risk]

### Warning (fix soon)
- [issue] — [specific fix] — saves ~Xmin / prevents [risk]

### Suggestion (nice to have)
- [issue] — [specific fix] — saves ~Xmin / improves [area]

### What's Working Well
- [positive observation]
```

Be specific — reference exact file names, line numbers, and step names.

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
