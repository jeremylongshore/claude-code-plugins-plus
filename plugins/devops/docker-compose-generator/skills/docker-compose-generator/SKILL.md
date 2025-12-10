---
name: generating-docker-compose-files
description: |
  Use when you need to work with Docker Compose.
  This skill provides Docker Compose file generation with comprehensive guidance and automation.
  Trigger with phrases like "generate docker-compose", "create compose file",
  or "configure multi-container app".
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(docker:*, kubectl:*)
version: 1.0.0
license: MIT
---

## Prerequisites

Before using this skill, ensure:
- Required credentials and permissions for the operations
- Understanding of the system architecture and dependencies
- Backup of critical data before making structural changes
- Access to relevant documentation and configuration files
- Monitoring tools configured for observability
- Development or staging environment available for testing

## Instructions

### Step 1: Assess Current State
1. Review current configuration, setup, and baseline metrics
2. Identify specific requirements, goals, and constraints
3. Document existing patterns, issues, and pain points
4. Analyze dependencies and integration points
5. Validate all prerequisites are met before proceeding

### Step 2: Design Solution
1. Define optimal approach based on best practices
2. Create detailed implementation plan with clear steps
3. Identify potential risks and mitigation strategies
4. Document expected outcomes and success criteria
5. Review plan with team or stakeholders if needed

### Step 3: Implement Changes
1. Execute implementation in non-production environment first
2. Verify changes work as expected with thorough testing
3. Monitor for any issues, errors, or performance impacts
4. Document all changes, decisions, and configurations
5. Prepare rollback plan and recovery procedures

### Step 4: Validate Implementation
1. Run comprehensive tests to verify all functionality
2. Compare performance metrics against baseline
3. Confirm no unintended side effects or regressions
4. Update all relevant documentation
5. Obtain approval before production deployment

### Step 5: Deploy to Production
1. Schedule deployment during appropriate maintenance window
2. Execute implementation with real-time monitoring
3. Watch closely for any issues or anomalies
4. Verify successful deployment and functionality
5. Document completion, metrics, and lessons learned

## Output

This skill produces:

**Implementation Artifacts**: Scripts, configuration files, code, and automation tools

**Documentation**: Comprehensive documentation of changes, procedures, and architecture

**Test Results**: Validation reports, test coverage, and quality metrics

**Monitoring Configuration**: Dashboards, alerts, metrics, and observability setup

**Runbooks**: Operational procedures for maintenance, troubleshooting, and incident response

## Error Handling

**Permission and Access Issues**:
- Verify credentials and permissions for all operations
- Request elevated access if required for specific tasks
- Document all permission requirements for automation
- Use separate service accounts for privileged operations
- Implement least-privilege access principles

**Connection and Network Failures**:
- Check network connectivity, firewalls, and security groups
- Verify service endpoints, DNS resolution, and routing
- Test connections using diagnostic and troubleshooting tools
- Review network policies, ACLs, and security configurations
- Implement retry logic with exponential backoff

**Resource Constraints**:
- Monitor resource usage (CPU, memory, disk, network)
- Implement throttling, rate limiting, or queue mechanisms
- Schedule resource-intensive tasks during low-traffic periods
- Scale infrastructure resources if consistently hitting limits
- Optimize queries, code, or configurations for efficiency

**Configuration and Syntax Errors**:
- Validate all configuration syntax before applying changes
- Test configurations thoroughly in non-production first
- Implement automated configuration validation checks
- Maintain version control for all configuration files
- Keep previous working configuration for quick rollback

## Resources

**Configuration Templates**: `{baseDir}/templates/docker-compose-generator/`

**Documentation and Guides**: `{baseDir}/docs/docker-compose-generator/`

**Example Scripts and Code**: `{baseDir}/examples/docker-compose-generator/`

**Troubleshooting Guide**: `{baseDir}/docs/docker-compose-generator-troubleshooting.md`

**Best Practices**: `{baseDir}/docs/docker-compose-generator-best-practices.md`

**Monitoring Setup**: `{baseDir}/monitoring/docker-compose-generator-dashboard.json`
