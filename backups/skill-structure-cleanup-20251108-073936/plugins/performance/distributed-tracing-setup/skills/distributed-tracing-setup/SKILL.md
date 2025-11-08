---
name: setting-up-distributed-tracing
description: |
  This skill automates the setup of distributed tracing for microservices. It helps developers implement end-to-end request visibility by configuring context propagation, span creation, trace collection, and analysis. Use this skill when the user requests to set up distributed tracing, implement observability, or troubleshoot performance issues in a microservices architecture. The skill is triggered by phrases such as "setup tracing", "implement distributed tracing", "configure opentelemetry", or "add observability to microservices".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill streamlines the process of setting up distributed tracing in a microservices environment. It guides you through the key steps of instrumenting your services, configuring trace context propagation, and selecting a backend for trace collection and analysis, enabling comprehensive monitoring and debugging.

## How It Works

1. **Backend Selection**: Determines the preferred tracing backend (e.g., Jaeger, Zipkin, Datadog).
2. **Instrumentation Strategy**: Designs an instrumentation strategy for each service, focusing on key operations and dependencies.
3. **Configuration Generation**: Generates the necessary configuration files and code snippets to enable distributed tracing.

## When to Use This Skill

This skill activates when you need to:
- Implement distributed tracing in a microservices application.
- Gain end-to-end visibility into request flows across multiple services.
- Troubleshoot performance bottlenecks and latency issues.

## Examples

### Example 1: Adding Tracing to a New Microservice

User request: "setup tracing for the new payment service"

The skill will:
1. Prompt for the preferred tracing backend (e.g., Jaeger).
2. Generate code snippets for OpenTelemetry instrumentation in the payment service.

### Example 2: Troubleshooting Performance Issues

User request: "implement distributed tracing to debug slow checkout process"

The skill will:
1. Guide the user through instrumenting relevant services in the checkout flow.
2. Provide configuration examples for context propagation.

## Best Practices

- **Backend Choice**: Select a tracing backend that aligns with your existing infrastructure and monitoring tools.
- **Sampling Strategy**: Implement a sampling strategy to manage trace volume and cost, especially in high-traffic environments.
- **Context Propagation**: Ensure proper context propagation across all services to maintain trace continuity.

## Integration

This skill can be used in conjunction with other plugins to automate the deployment and configuration of tracing infrastructure. For example, it can integrate with infrastructure-as-code tools to provision Jaeger or Zipkin clusters.