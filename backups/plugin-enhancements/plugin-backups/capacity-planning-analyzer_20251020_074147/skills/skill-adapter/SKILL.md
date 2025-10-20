---
name: Analyzing Capacity Planning
description: |
  This skill enables Claude to analyze capacity requirements and plan for future growth. It uses the capacity-planning-analyzer plugin to assess current utilization, forecast growth trends, and recommend scaling strategies. Use this skill when the user asks to "analyze capacity", "plan for growth", "forecast infrastructure needs", or requests a "capacity roadmap". It is also useful when the user mentions specific capacity metrics like CPU usage, memory, database storage, network bandwidth, or connection pool saturation. This skill is ideal for proactive infrastructure planning and preventing performance bottlenecks.
---

## Overview

This skill empowers Claude to analyze current resource utilization, predict future capacity needs, and provide actionable recommendations for scaling infrastructure. It generates insights into growth trends, identifies potential bottlenecks, and estimates costs associated with capacity expansion.

## How It Works

1. **Analyze Utilization**: The plugin analyzes current CPU, memory, database storage, network bandwidth, and request rate utilization.
2. **Forecast Growth**: Based on historical data, the plugin forecasts future growth trends for key capacity metrics.
3. **Generate Recommendations**: The plugin recommends scaling strategies, including vertical and horizontal scaling options, and estimates associated costs.

## When to Use This Skill

This skill activates when you need to:
- Analyze current infrastructure capacity and identify potential bottlenecks.
- Forecast future resource requirements based on projected growth.
- Develop a capacity roadmap to ensure optimal performance and availability.

## Examples

### Example 1: Planning for Database Growth

User request: "Analyze database capacity and plan for future growth."

The skill will:
1. Analyze current database storage utilization and growth rate.
2. Forecast future storage requirements based on historical trends.
3. Recommend scaling options, such as adding storage or migrating to a larger instance.

### Example 2: Identifying CPU Bottlenecks

User request: "Analyze CPU utilization and identify potential bottlenecks."

The skill will:
1. Analyze CPU utilization trends across different servers and applications.
2. Identify periods of high CPU usage and potential bottlenecks.
3. Recommend scaling options, such as adding more CPU cores or optimizing application code.

## Best Practices

- **Data Accuracy**: Ensure that the data used for analysis is accurate and up-to-date.
- **Metric Selection**: Choose the right capacity metrics to monitor based on your specific application requirements.
- **Regular Monitoring**: Regularly monitor capacity metrics to identify potential issues before they impact performance.

## Integration

This skill can be integrated with other monitoring and alerting tools to provide proactive capacity management. It can also be used in conjunction with infrastructure-as-code tools to automate scaling operations.