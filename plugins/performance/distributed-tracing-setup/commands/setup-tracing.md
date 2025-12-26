---
name: setup-tracing
description: Set up distributed tracing
---
# Distributed Tracing Setup

Implement distributed tracing for end-to-end request visibility in microservices.

## Tracing Components

1. **Trace Context Propagation**: Header-based context passing
2. **Span Creation**: Service and operation instrumentation
3. **Trace Collection**: Centralized trace aggregation
4. **Trace Analysis**: Latency breakdown and bottleneck detection
5. **Sampling Strategy**: Managing trace volume and cost

## Process

1. Choose tracing backend (Jaeger, Zipkin, Datadog APM, etc.)
2. Design instrumentation strategy
3. Implement OpenTelemetry or vendor SDK
4. Configure context propagation
5. Set up trace collection and storage
6. Create trace analysis dashboards

## Output

Provide:
- Tracing SDK integration code
- Instrumentation for key services
- Context propagation configuration
- Sampling strategy recommendations
- Backend setup instructions (Jaeger/Zipkin/etc.)
- Dashboard configuration for trace analysis
- Performance impact assessment
