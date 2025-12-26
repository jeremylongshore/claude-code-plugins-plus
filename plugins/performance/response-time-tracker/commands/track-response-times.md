---
name: track-response-times
description: Track and optimize response times
---
# Response Time Tracker

Implement comprehensive response time tracking and optimization.

## Tracking Areas

1. **API Endpoints**: HTTP request/response times
2. **Database Queries**: Query execution times
3. **External Services**: Third-party API latency
4. **Frontend Rendering**: Page load and render times
5. **Background Jobs**: Async task execution times

## Metrics to Track

- **P50, P95, P99 Percentiles**: Response time distribution
- **Average Response Time**: Mean latency
- **Max Response Time**: Worst-case scenarios
- **Time Series Data**: Response time trends

## Process

1. Identify all application endpoints and operations
2. Design response time instrumentation strategy
3. Implement timing middleware/decorators
4. Create monitoring dashboards
5. Define SLO thresholds
6. Generate optimization recommendations

## Output

Provide:
- Response time instrumentation code
- Monitoring configuration
- Dashboard setup (Prometheus, Grafana, etc.)
- SLO definitions with percentile targets
- Alert rules for degraded performance
- Optimization strategies for slow endpoints
