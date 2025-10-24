---
name: optimizing-cloud-costs
description: |
  This skill enables Claude to analyze and optimize cloud costs. It identifies areas for potential savings, generates cost reports, and suggests configuration changes to reduce expenses. Use this skill when the user asks to "optimize cloud costs", "reduce cloud spending", "generate a cost report", or similar requests related to cloud resource expenses. It is especially useful when the user provides details about their cloud environment (e.g., AWS, Azure, GCP). The skill leverages best practices for cost optimization and provides production-ready configurations.
---

## Overview

This skill empowers Claude to be a FinOps expert, helping users identify and implement strategies to minimize their cloud expenditures. By analyzing current resource utilization and suggesting optimized configurations, it ensures efficient cloud spending.

## How It Works

1. **Analyzing Cost Data**: Claude analyzes the user's request to identify the scope and cloud provider (if specified).
2. **Generating Optimization Recommendations**: Claude formulates specific recommendations to reduce costs, such as rightsizing instances, identifying unused resources, or leveraging reserved instances.
3. **Creating Cost Report**: Claude generates a detailed cost report summarizing current spending and potential savings.

## When to Use This Skill

This skill activates when you need to:
- Reduce your AWS, Azure, or GCP cloud spending.
- Generate a report detailing current cloud costs.
- Identify underutilized or unused cloud resources.

## Examples

### Example 1: Reducing AWS EC2 Costs

User request: "Optimize my AWS EC2 costs. I'm running several t3.medium instances."

The skill will:
1. Analyze the usage patterns of the t3.medium instances.
2. Suggest rightsizing to t3.small or using reserved instances if utilization is consistently high.
3. Generate a cost report showing potential savings from the recommended changes.

### Example 2: Identifying Idle Azure Resources

User request: "Generate a report of idle resources in my Azure subscription."

The skill will:
1. Identify any virtual machines, storage accounts, or other resources that have been idle for a specified period.
2. Recommend terminating or deallocating the idle resources.
3. Provide a cost report detailing the savings achieved by removing the idle resources.

## Best Practices

- **Resource Utilization**: Regularly review resource utilization metrics to identify opportunities for rightsizing.
- **Reserved Instances**: Leverage reserved instances or committed use discounts for consistently used resources.
- **Cost Monitoring**: Implement continuous cost monitoring and alerting to track spending trends and identify anomalies.

## Integration

This skill can be used in conjunction with other DevOps plugins to automate the implementation of cost optimization recommendations. For example, it can integrate with infrastructure-as-code tools to automatically resize instances or terminate unused resources.