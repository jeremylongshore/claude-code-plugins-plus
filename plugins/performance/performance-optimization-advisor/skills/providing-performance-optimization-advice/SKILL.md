---
name: providing-performance-optimization-advice
description: Provide comprehensive prioritized performance optimization recommendations for frontend, backend, and infrastructure. Use when analyzing bottlenecks or seeking improvement strategies. Trigger with phrases like "optimize performance", "improve speed", or "performance recommendations".
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(profiling:*), Bash(analysis:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Performance Optimization Advisor

This skill provides automated assistance for performance optimization advisor tasks.

## Overview

This skill empowers Claude to act as a performance optimization advisor, delivering a detailed report of potential improvements across various layers of a software application. It prioritizes recommendations based on impact and effort, allowing for a focused and efficient optimization strategy.

## How It Works

1. **Analyze Project**: Claude uses the plugin to analyze the project's codebase, infrastructure configuration, and architecture.
2. **Identify Optimization Areas**: The plugin identifies potential optimization areas in the frontend, backend, and infrastructure.
3. **Prioritize Recommendations**: The plugin prioritizes recommendations based on estimated performance gains and implementation effort.
4. **Generate Report**: Claude presents a comprehensive report with actionable advice, performance gain estimates, and a phased implementation roadmap.

## When to Use This Skill

This skill activates when you need to:
- Identify performance bottlenecks in a software application.
- Get recommendations for improving website loading speed.
- Optimize database query performance.
- Improve API response times.
- Reduce infrastructure costs.

## Examples

### Example 1: Optimizing a Slow Website

User request: "My website is loading very slowly. Can you help me optimize its performance?"

The skill will:
1. Analyze the website's frontend code, backend APIs, and infrastructure configuration.
2. Identify issues such as unoptimized images, inefficient database queries, and lack of CDN usage.
3. Generate a report with prioritized recommendations, including image optimization, database query optimization, and CDN implementation.

### Example 2: Improving API Response Time

User request: "The API response time is too slow. What can I do to improve it?"

The skill will:
1. Analyze the API code, database queries, and caching strategies.
2. Identify issues such as inefficient database queries, lack of caching, and slow processing logic.
3. Generate a report with prioritized recommendations, including database query optimization, caching implementation, and asynchronous processing.

## Best Practices

- **Specificity**: Provide specific details about the project and its performance issues to get more accurate and relevant recommendations.
- **Context**: Explain the context of the performance problem, such as the expected user load or the specific use case.
- **Iteration**: Review the recommendations and provide feedback to refine the optimization strategy.

## Integration

This skill integrates well with other plugins that provide code analysis, infrastructure management, and deployment automation capabilities. For example, it can be used in conjunction with a code linting plugin to identify code-level performance issues or with an infrastructure-as-code plugin to automate infrastructure optimization tasks.

## Prerequisites

- Access to application codebase in {baseDir}/
- Infrastructure configuration files
- Performance profiling tools
- Current performance metrics and baselines

## Instructions

1. Analyze frontend code for rendering and asset optimization
2. Review backend code for query and processing efficiency
3. Examine infrastructure for scaling and resource usage
4. Identify high-impact optimization opportunities
5. Prioritize recommendations by effort vs impact
6. Generate phased implementation roadmap

## Output

- Comprehensive optimization report by layer (frontend/backend/infra)
- Prioritized recommendations with impact estimates
- Code examples for suggested improvements
- Performance gain projections
- Implementation effort estimates and timeline

## Error Handling

If optimization analysis fails:
- Verify codebase access permissions
- Check profiling tool installation
- Validate configuration file formats
- Ensure sufficient analysis resources
- Review project structure completeness

## Resources

- Web performance optimization guides
- Database query optimization best practices
- Infrastructure scaling patterns
- Caching strategies and CDN usage