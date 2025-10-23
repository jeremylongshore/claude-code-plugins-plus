---
name: managing-deployment-rollbacks
description: |
  This skill manages and executes deployment rollbacks with safety checks. It helps ensure smooth recovery from failed deployments by automating the rollback process. Use this skill when a deployment has issues, such as errors, performance degradation, or unexpected behavior. The skill is triggered by requests to "rollback deployment", "revert to previous version", or similar phrases related to deployment recovery. It prioritizes safe rollback procedures and provides options for verification.
---

## Overview

This skill enables Claude to manage and execute deployment rollbacks, ensuring a stable and reliable system. It automates the process of reverting to a previous, known-good deployment state, minimizing downtime and potential disruptions.

## How It Works

1. **Identifying the Issue**: Claude analyzes the user's request to confirm the need for a rollback due to a failed deployment.
2. **Executing Rollback**: Claude executes the rollback command, reverting the deployment to the previously known stable version.
3. **Verification**: Claude verifies the success of the rollback by checking the application's status, health checks, and logs.

## When to Use This Skill

This skill activates when you need to:
- Recover from a failed deployment.
- Revert to a previous version of an application.
- Address issues caused by a recent deployment.

## Examples

### Example 1: Rolling back a faulty deployment

User request: "Rollback deployment to the previous stable version due to errors."

The skill will:
1. Execute the `rollback-deploy` command.
2. Confirm the successful rollback to the previous version.

### Example 2: Reverting after performance degradation

User request: "Revert to the last known good deployment. Performance has degraded significantly since the last update."

The skill will:
1. Execute the `rollback-deploy` command.
2. Verify the application's performance returns to normal levels.

## Best Practices

- **Verification**: Always verify the success of the rollback by checking application health and performance.
- **Monitoring**: Implement continuous monitoring to detect deployment issues early.
- **Documentation**: Maintain clear documentation of deployment versions and rollback procedures.

## Integration

This skill can be used in conjunction with other monitoring and alerting tools to automatically trigger rollbacks when issues are detected. It also integrates with deployment pipelines for automated rollback execution.