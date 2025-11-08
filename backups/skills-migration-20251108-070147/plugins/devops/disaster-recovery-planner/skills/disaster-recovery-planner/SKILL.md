---
name: planning-disaster-recovery
description: |
  This skill enables Claude to plan and implement disaster recovery (DR) procedures. It generates configurations and setup code based on specific requirements and infrastructure. Use this skill when the user requests assistance with disaster recovery planning, business continuity, or related DevOps tasks. Trigger this skill when the user mentions "disaster recovery", "DR plan", "business continuity", or requests help with setting up a recovery strategy. It provides production-ready configurations, implements best practices, and supports multi-platform environments.
---

## Overview

This skill empowers Claude to generate disaster recovery plans tailored to specific infrastructure and business needs. It automates the creation of configurations and setup code, significantly reducing the manual effort required for DR implementation.

## How It Works

1. **Requirement Gathering**: Claude identifies the user's specific disaster recovery requirements, including platform, recovery time objective (RTO), and recovery point objective (RPO).
2. **Configuration Generation**: Based on the requirements, Claude generates production-ready configurations for the disaster recovery plan.
3. **Code Generation**: Claude generates the necessary setup code to implement the disaster recovery plan.

## When to Use This Skill

This skill activates when you need to:
- Create a disaster recovery plan for a specific environment.
- Generate configurations for disaster recovery infrastructure.
- Automate the setup of disaster recovery procedures.

## Examples

### Example 1: Creating a DR Plan for AWS

User request: "Create a disaster recovery plan for my AWS environment with an RTO of 1 hour and an RPO of 15 minutes."

The skill will:
1. Gather the AWS environment details, RTO, and RPO requirements.
2. Generate a disaster recovery plan configuration using AWS services like S3 replication, EC2 snapshots, and Route 53 failover.

### Example 2: Setting Up a Business Continuity Strategy

User request: "Help me set up a business continuity strategy using a multi-region deployment."

The skill will:
1. Analyze the existing infrastructure and application architecture.
2. Generate configurations for deploying the application across multiple regions, including database replication and load balancing.

## Best Practices

- **Security**: Always prioritize security when designing disaster recovery plans. Ensure that all data is encrypted and access is properly controlled.
- **Testing**: Regularly test the disaster recovery plan to ensure it functions as expected and meets the required RTO and RPO.
- **Documentation**: Maintain comprehensive documentation of the disaster recovery plan, including configuration details, procedures, and contact information.

## Integration

This skill can be integrated with other DevOps tools and plugins to automate the entire disaster recovery process, including infrastructure provisioning, configuration management, and monitoring.