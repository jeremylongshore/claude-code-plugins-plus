---
name: validator-expert
description: |
  Validate production readiness of Vertex AI Agent Engine deployments across security, monitoring, performance, compliance, and best practices. Generates weighted scores (0-100%) with actionable recommendations. Use when asked to "validate deploymen... Trigger with phrases like 'validate', 'check', or 'verify'.
allowed-tools: Read, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Validator Expert

This skill provides automated assistance for validator expert tasks.

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

## Overview


This skill provides automated assistance for validator expert tasks.
This skill provides automated assistance for the described functionality.

## Prerequisites

- Appropriate file access permissions
- Required dependencies installed

## Instructions

1. Invoke this skill when the trigger conditions are met
2. Provide necessary context and parameters
3. Review the generated output
4. Apply modifications as needed

## Output

The skill produces structured output relevant to the task.

## Error Handling

- Invalid input: Prompts for correction
- Missing dependencies: Lists required components
- Permission errors: Suggests remediation steps

## Examples

Example usage patterns will be demonstrated in context.

## Resources

- Project documentation
- Related skills and commands