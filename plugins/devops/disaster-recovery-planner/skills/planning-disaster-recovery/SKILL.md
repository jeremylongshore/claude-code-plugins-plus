---
name: planning-disaster-recovery
description: |
  Execute use when you need to work with backup and recovery.
  This skill provides backup automation and disaster recovery with comprehensive guidance and automation.
  Trigger with phrases like "create backups", "automate backups",
  or "implement disaster recovery".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(tar:*), Bash(rsync:*), Bash(aws:s3:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Planning Disaster Recovery

## Overview

Design disaster recovery (DR) plans for cloud infrastructure covering RTO/RPO requirements, multi-region failover, data replication, and automated recovery procedures. Generate runbooks, Terraform for standby infrastructure, and automated failover scripts for databases, compute, and networking.

## Prerequisites

- Complete inventory of production infrastructure components and dependencies
- Defined RTO (Recovery Time Objective) and RPO (Recovery Point Objective) per service tier
- Cloud provider CLI authenticated with permissions for multi-region resource management
- Cross-region networking configured (VPC peering, Transit Gateway, or VPN)
- Backup and replication mechanisms already in place or planned

## Instructions

1. Catalog all production services with their criticality tier (Tier 1: < 15 min RTO, Tier 2: < 1 hour, Tier 3: < 24 hours)
2. Map dependencies between services to identify single points of failure and cascading failure paths
3. Design the DR strategy per tier: active-active for Tier 1, pilot light or warm standby for Tier 2, backup-restore for Tier 3
4. Generate Terraform for standby region infrastructure: VPC, subnets, security groups, and scaled-down compute
5. Configure database replication: RDS cross-region read replicas, DynamoDB global tables, or Cloud SQL cross-region replicas
6. Set up DNS failover using Route 53 health checks, Cloud DNS routing policies, or global load balancers
7. Create automated failover scripts: promote read replica to primary, update DNS records, scale up standby compute
8. Document the DR runbook with step-by-step procedures, responsible parties, and communication plans
9. Schedule quarterly DR drills: simulate region failure, execute the runbook, measure actual RTO/RPO, and document gaps
10. Set up monitoring for replication lag, backup freshness, and standby infrastructure health

## Output

- DR plan document with service tiers, RTO/RPO targets, and recovery procedures
- Terraform modules for standby region infrastructure
- Automated failover scripts (database promotion, DNS switching, compute scaling)
- DR drill checklist and post-drill assessment template
- Monitoring dashboards for replication lag and backup status

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `Replication lag exceeds RPO` | Network throughput insufficient or write volume too high | Increase replication instance size, enable compression, or implement write throttling during peak |
| `DNS failover not triggering` | Health check misconfigured or TTL too high | Verify health check endpoint returns proper status; reduce DNS TTL to 60 seconds before drill |
| `Standby database promotion failed` | Replication broken or standby in inconsistent state | Check replication status; if broken, restore from latest snapshot and re-establish replication |
| `Insufficient capacity in DR region` | Instance types unavailable in standby region | Pre-provision reserved capacity in DR region or use multiple instance type options |
| `Application cannot connect after failover` | Connection strings hardcoded to primary region endpoints | Use DNS-based endpoints (CNAME/Route 53) instead of direct IPs; parameterize region in config |

## Examples

- "Create a disaster recovery plan for a 3-tier web application on AWS with < 15 minute RTO for the API layer and < 1 hour for batch processing."
- "Generate Terraform for a warm standby in us-west-2 with RDS cross-region read replica, scaled-down ECS cluster, and Route 53 failover routing."
- "Design a DR drill that simulates primary region failure, executes automated failover, and validates data integrity in the standby region."

## Resources

- AWS Disaster Recovery: https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/
- GCP DR planning: https://cloud.google.com/architecture/dr-scenarios-planning-guide
- Azure Business Continuity: https://learn.microsoft.com/en-us/azure/reliability/
- DR strategy patterns: https://aws.amazon.com/blogs/architecture/disaster-recovery-dr-architecture-on-aws-part-i/