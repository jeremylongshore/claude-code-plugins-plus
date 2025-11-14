---
name: validator-expert
description: |
  Production readiness validator for Vertex AI Agent Engine deployments (ADK agents ONLY).
  5-category validation: Security (IAM, VPC-SC, Model Armor), Monitoring (2025 dashboard, alerts, SLOs), Performance (auto-scaling, Code Execution TTL), Compliance (audit logs, data residency), Best Practices (Memory Bank, A2A protocol).
  Generates weighted production readiness score (0-100%) with PASS/WARNING/FAIL status.
  Triggers: "validate agent engine deployment", "production readiness", "security audit", "check compliance"
allowed-tools: Read, Grep, Glob, Bash
version: 1.0.1
---

## What This Skill Does

Production validator for Vertex AI deployments. Performs comprehensive checks on security, compliance, monitoring, performance, and best practices before approving production deployment.

## When This Skill Activates

Triggers: "validate deployment", "production readiness", "security audit vertex ai", "check compliance", "validate adk agent"

## Validation Checklist

### Security Validation
- ✅ IAM roles follow least privilege
- ✅ VPC Service Controls enabled
- ✅ Encryption at rest configured
- ✅ No hardcoded secrets
- ✅ Service accounts properly configured
- ✅ Model Armor enabled (for ADK)

### Monitoring Validation
- ✅ Cloud Monitoring dashboards configured
- ✅ Alerting policies set
- ✅ Token usage tracking enabled
- ✅ Error rate monitoring active
- ✅ Latency SLOs defined

### Performance Validation
- ✅ Auto-scaling configured
- ✅ Resource limits appropriate
- ✅ Caching strategy implemented
- ✅ Code Execution sandbox TTL set
- ✅ Memory Bank retention configured

### Compliance Validation
- ✅ Audit logging enabled
- ✅ Data residency requirements met
- ✅ Privacy policies implemented
- ✅ Backup/disaster recovery configured

## Tool Permissions

Read, Grep, Glob, Bash - Read-only analysis for security

## References

- Vertex AI Security: https://cloud.google.com/vertex-ai/docs/security
