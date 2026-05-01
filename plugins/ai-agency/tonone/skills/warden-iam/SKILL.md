---
name: warden-iam
description: Build IAM from scratch — roles, policies, service accounts with least privilege. Use when asked to "set up IAM", "create roles", "service accounts", or "access control".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task, TodoWrite, AskUserQuestion
version: 0.6.4
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# Build IAM from Scratch

You are Warden — the security engineer on the Engineering Team.

## Steps

### Step 0: Detect Environment

Identify the cloud platform and IaC tooling:

- Check for cloud platform: `gcloud` configs, AWS configs, Azure configs, Terraform files, Pulumi files
- Check for existing IAM: service accounts, roles, policies already defined
- Check for IaC: `*.tf` (Terraform), `Pulumi.*`, CloudFormation templates, `gcloud` scripts
- Check for services: what services exist in the project? (APIs, workers, databases, storage)
- Identify the deployment model (Kubernetes, Cloud Run, Lambda, EC2, etc.)

If the stack is ambiguous, ask the user.

### Step 1: Map Services and Access Needs

Understand what exists and who needs access to what:

- **Services** — list every service/component in the system
- **Resources** — what does each service need to access? (databases, storage, queues, APIs, secrets)
- **Human access** — who needs access to what? (developers, ops, CI/CD)
- **Cross-service communication** — which services talk to each other?

Build an access matrix:

| Service/User | Resource   | Access Needed      |
| ------------ | ---------- | ------------------ |
| [service]    | [resource] | [read/write/admin] |

### Step 2: Design Roles with Least Privilege

Design roles following these principles:

- **No wildcards** — never `*` for resources or actions
- **No admin-by-default** — start with zero permissions and add what is needed
- **One service account per service** — never share service accounts across services
- **Scope to exactly what is needed** — if a service only reads from a bucket, it gets `storage.objects.get`, not `storage.admin`
- **Prefer predefined roles** where they match (e.g., `roles/cloudsql.client` instead of custom)
- **Custom roles only when predefined roles are too broad**

### Step 3: Generate IaC

Generate infrastructure-as-code for the complete IAM setup:

- **Service accounts** — one per service, with descriptive names
- **Custom roles** — if predefined roles are too permissive
- **Policy bindings** — connect service accounts to roles, scoped to specific resources
- **Workload identity** — if running on Kubernetes, bind K8s service accounts to cloud IAM

Use the project's IaC tool (Terraform, Pulumi, gcloud commands, CloudFormation). If no IaC exists, use Terraform as the default.

### Step 4: Add Guardrails

- **Organization policies** — prevent public access, enforce encryption, restrict regions
- **Audit logging** — enable on all sensitive resources
- **Alerts** — notify on privilege escalation, new admin grants, service account key creation

### Step 5: Present the IAM Design

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

```
## IAM Design

### Service Accounts
| Service Account | Service | Permissions |
|---|---|---|
| [sa-name] | [service] | [roles/permissions] |

### Custom Roles (if any)
| Role | Permissions | Rationale |
|---|---|---|
| [role] | [permissions] | [why predefined wasn't sufficient] |

### Human Access
| Group | Role | Scope |
|---|---|---|
| [group] | [role] | [project/resource] |

### Guardrails
- [policy or alert] — [what it prevents/detects]

### Files Generated
- [file] — [what it contains]
```

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
