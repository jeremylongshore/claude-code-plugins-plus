# 500 Standalone Skills Initiative

**Purpose**: Generate 500 standalone Claude Code Agent Skills organized into 20 categories.

**Structure**: 20 categories × 25 skills = 500 total skills

---

## Quick Stats

| Metric | Value |
|--------|-------|
| Total Skills | 500 |
| Categories | 20 |
| Skills per Category | 25 |
| Batches | 20 |
| Status | **Planning** |

---

## Key Decision: Standalone Skills

These 500 skills will be **standalone** in `/skills/`, separate from the 239 plugin-embedded skills.

| Type | Location | Count |
|------|----------|-------|
| **Standalone Skills (NEW)** | `/skills/[category]/[skill]/SKILL.md` | 500 planned |
| Plugin-Embedded Skills | `/plugins/*/skills/*/SKILL.md` | 239 existing |
| **Total After Completion** | | **739 skills** |

---

## Directory Structure

```
planned-skills/
├── README.md                          # This file
├── generation-config.json             # Generation settings
│
├── categories/                        # 20 category definitions
│   ├── 01-devops-basics/
│   │   ├── category-config.json      # 25 skill definitions
│   │   └── skills/                   # Generated skills staging
│   ├── 02-devops-advanced/
│   ├── 03-security-fundamentals/
│   ├── 04-security-advanced/
│   ├── 05-frontend-dev/
│   ├── 06-backend-dev/
│   ├── 07-ml-training/
│   ├── 08-ml-deployment/
│   ├── 09-test-automation/
│   ├── 10-performance-testing/
│   ├── 11-data-pipelines/
│   ├── 12-data-analytics/
│   ├── 13-aws-skills/
│   ├── 14-gcp-skills/
│   ├── 15-api-development/
│   ├── 16-api-integration/
│   ├── 17-technical-docs/
│   ├── 18-visual-content/
│   ├── 19-business-automation/
│   └── 20-enterprise-workflows/
│
├── templates/
│   ├── skill-template.md             # SKILL.md template
│   ├── category-readme-template.md   # Category README template
│   └── gemini-prompt-template.md     # Vertex AI prompt
│
├── scripts/
│   ├── generate-batch.js             # Generate skills via Vertex AI
│   ├── validate-skill.js             # Validate against spec
│   └── deploy-skills.js              # Deploy to /skills/
│
├── batches/
│   ├── batch-001/ → batch-020/
│   │   ├── input/                    # Generation prompts
│   │   ├── output/                   # Raw generated skills
│   │   ├── validated/                # Validated skills
│   │   └── metadata.json             # Batch status
│
└── logs/
    ├── generation.log
    └── validation.log
```

---

## 20 Categories (500 Skills)

| # | Category | Skills | Priority | Description |
|---|----------|--------|----------|-------------|
| 01 | DevOps Basics | 25 | High | Git, Docker, basic CI/CD |
| 02 | DevOps Advanced | 25 | High | K8s, Terraform, Helm |
| 03 | Security Fundamentals | 25 | High | Auth, validation, OWASP |
| 04 | Security Advanced | 25 | High | Pentesting, compliance |
| 05 | Frontend Dev | 25 | Medium | React, Vue, CSS, a11y |
| 06 | Backend Dev | 25 | High | Node, Python, Go, APIs |
| 07 | ML Training | 25 | Medium | PyTorch, TensorFlow, sklearn |
| 08 | ML Deployment | 25 | Medium | MLOps, serving, monitoring |
| 09 | Test Automation | 25 | High | Jest, pytest, mocking |
| 10 | Performance Testing | 25 | Medium | k6, JMeter, profiling |
| 11 | Data Pipelines | 25 | Medium | Airflow, Spark, ETL |
| 12 | Data Analytics | 25 | Medium | SQL, visualization, BI |
| 13 | AWS Skills | 25 | High | Lambda, S3, CloudFormation |
| 14 | GCP Skills | 25 | High | Cloud Run, BigQuery, Vertex AI |
| 15 | API Development | 25 | High | REST, GraphQL, OpenAPI |
| 16 | API Integration | 25 | Medium | Webhooks, OAuth, SDKs |
| 17 | Technical Docs | 25 | Medium | README, API docs, tutorials |
| 18 | Visual Content | 25 | Low | Mermaid, diagrams, charts |
| 19 | Business Automation | 25 | Medium | Workflows, spreadsheets |
| 20 | Enterprise Workflows | 25 | Low | Jira, governance, PM |
| | **TOTAL** | **500** | | |

---

## Generation Workflow

### Phase 1: Define (Complete)
- [x] Create directory structure
- [x] Define 20 categories
- [x] Define 25 skills per category (in category-config.json)
- [x] Create templates and scripts

### Phase 2: Generate
- [ ] Batch 001: DevOps Basics (25 skills)
- [ ] Batch 002: DevOps Advanced (25 skills)
- [ ] ... (batches 003-020)

### Phase 3: Validate
- [ ] Run validation on each batch
- [ ] Fix any issues
- [ ] Move to validated/

### Phase 4: Deploy
- [ ] Deploy to /skills/ directory
- [ ] Update marketplace
- [ ] Release

---

## Commands

```bash
# Generate a batch
node scripts/generate-batch.js --category 01-devops-basics --batch 001

# Validate a batch
node scripts/validate-skill.js --batch 001

# Deploy validated skills
node scripts/deploy-skills.js --batch 001

# Dry run (show what would be deployed)
node scripts/deploy-skills.js --batch 001 --dry-run
```

---

## Enterprise Standard

All skills follow the enterprise standard:

```yaml
---
name: skill-name-kebab-case          # Required, max 64 chars
description: |                        # Required, max 1024 chars
  [Action verb] [capability].
  Use when [scenarios].
  Trigger with "[phrases]".
allowed-tools:                        # Enterprise required
  - Read
  - Write
  - Bash
version: 1.0.0                        # Enterprise required
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT                          # Enterprise required
tags:                                 # Recommended
  - category
  - domain
---
```

---

## Reference Documents

- `SKILLS-STANDARD-COMPLETE.md` - Master specification (65KB)
- `SKILLS-REFERENCE-MANUAL.md` - Quick reference (15KB)
- `STATUS-2025-12-19.md` - Progress tracking

---

## Production Directory

After deployment, skills will be in:

```
skills/
├── devops-basics/
│   ├── git-workflow-manager/SKILL.md
│   ├── docker-container-basics/SKILL.md
│   └── ... (25 total)
├── devops-advanced/
│   └── ... (25 total)
├── security-fundamentals/
│   └── ... (25 total)
└── ... (20 categories total)
```

---

**Last Updated**: 2025-12-19
**Maintained By**: Intent Solutions (Jeremy Longshore)
**Target**: 500 standalone skills + 239 embedded = 739 total
