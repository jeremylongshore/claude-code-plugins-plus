# Jeremy Vertex Engine

Vertex AI Agent Engine expert inspector and orchestrator. Validates agent deployments, inspects runtime configurations, monitors health, and ensures production readiness.

## Overview

This plugin provides comprehensive inspection and validation capabilities for agents deployed to the Vertex AI Agent Engine managed runtime. It acts as a quality assurance layer ensuring agents are properly configured, secure, performant, and production-ready.

## Installation

```bash
/plugin install jeremy-vertex-engine@claude-code-plugins-plus
```

## Features

✅ **Runtime Configuration Inspection**: Validate model, tools, VPC settings
✅ **Code Execution Sandbox Validation**: Check security, state persistence, IAM
✅ **Memory Bank Configuration**: Verify retention, indexing, query performance
✅ **A2A Protocol Compliance**: Ensure AgentCard and API endpoints functional
✅ **Security Audits**: IAM, VPC-SC, encryption, Model Armor checks
✅ **Performance Monitoring**: Latency, error rates, token usage, costs
✅ **Production Readiness Scoring**: Comprehensive 28-point checklist
✅ **Health Monitoring**: Real-time metrics and alerting

## Components

### Agent
- **vertex-engine-inspector**: Comprehensive agent inspector with validation logic

### Skills (Auto-Activating)
- **vertex-engine-inspector**: Triggers on "inspect agent engine", "validate deployment"
  - **Tool Permissions**: Read, Grep, Glob, Bash (read-only)
  - **Version**: 1.0.0 (2025 schema compliant)

## Quick Start

### Natural Language Activation

Simply mention what you need:

```
"Inspect my Vertex AI Engine agent deployment"
"Validate the Code Execution Sandbox configuration"
"Check Memory Bank settings for my agent"
"Monitor agent health over the last 24 hours"
"Production readiness check for agent-id-123"
```

The skill auto-activates and performs comprehensive inspection.

### What Gets Inspected

1. **Runtime Configuration**
   - Model selection and settings
   - Enabled tools (Code Execution, Memory Bank)
   - VPC and networking configuration
   - Resource allocation and scaling

2. **Code Execution Sandbox**
   - Security isolation validation
   - State persistence TTL (1-14 days)
   - IAM least privilege verification
   - Performance settings

3. **Memory Bank**
   - Persistent memory configuration
   - Retention policies
   - Query performance (indexing, caching)
   - Storage backend validation

4. **A2A Protocol**
   - AgentCard availability and structure
   - Task API functionality
   - Status API accessibility
   - Protocol version compliance

5. **Security Posture**
   - IAM roles and permissions
   - VPC Service Controls
   - Model Armor (prompt injection protection)
   - Encryption at rest and in transit

6. **Performance Metrics**
   - Error rates and latency
   - Token usage and costs
   - Throughput and scaling
   - SLO compliance

7. **Production Readiness**
   - 28-point comprehensive checklist
   - Weighted scoring across 5 categories
   - Overall readiness status
   - Actionable recommendations

## Production Readiness Score

The plugin generates a production readiness score based on:

- **Security** (30%): 6 checks
- **Performance** (25%): 6 checks
- **Monitoring** (20%): 6 checks
- **Compliance** (15%): 5 checks
- **Reliability** (10%): 5 checks

### Status Levels

🟢 **PRODUCTION READY (85-100%)**: Safe to deploy
🟡 **NEEDS IMPROVEMENT (70-84%)**: Address issues first
🔴 **NOT READY (<70%)**: Critical failures present

## Integration with Other Plugins

### jeremy-adk-orchestrator
- Orchestrator deploys → Inspector validates
- Continuous feedback loop

### jeremy-vertex-validator
- Validator checks code → Inspector checks runtime
- Pre/post deployment validation

### jeremy-adk-terraform
- Terraform provisions → Inspector validates
- Infrastructure verification

## Use Cases

### Pre-Production Validation
Before deploying to production:
```
"Run production readiness check on staging agent"
```

### Post-Deployment Verification
After deployment:
```
"Validate agent-xyz deployment was successful"
```

### Ongoing Health Monitoring
Regular health checks:
```
"Monitor agent health for the last 7 days"
```

### Security Audits
Compliance validation:
```
"Perform security audit on production agents"
```

### Troubleshooting
When issues occur:
```
"Why is my agent responding slowly?"
"Investigate high error rate on agent-abc"
```

## Example Inspection Report

```
Agent: gcp-deployer-agent
Status: 🟢 PRODUCTION READY (87%)

✅ Code Execution: Enabled (TTL: 14 days)
✅ Memory Bank: Enabled (retention: 90 days)
✅ A2A Protocol: Fully compliant
✅ Security: 92% score
✅ Performance: Error rate 2.3%, Latency 1.8s (p95)

⚠️ Recommendations:
1. Enable multi-region deployment
2. Configure automated backups
3. Add circuit breaker pattern
```

## Requirements

- Google Cloud Project with Vertex AI enabled
- Deployed agents on Agent Engine
- Appropriate IAM permissions for inspection
- Cloud Monitoring enabled

## License

MIT

## Support

- Issues: https://github.com/jeremylongshore/claude-code-plugins/issues
- Discussions: https://github.com/jeremylongshore/claude-code-plugins/discussions

## Version

1.0.0 (2025) - Agent Engine GA support with comprehensive inspection capabilities
