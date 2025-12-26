---
name: detect-regressions
description: Detect performance regressions in CI/CD
---
# Performance Regression Detector

Detect performance regressions early in the development cycle through automated testing.

## Detection Methods

1. **Baseline Comparison**: Compare against historical performance data
2. **Statistical Analysis**: Detect statistically significant changes
3. **Threshold Violations**: Check against performance budgets
4. **Trend Analysis**: Identify gradual degradation over time

## Metrics to Monitor

- Response time percentiles (p50, p95, p99)
- Throughput (requests per second)
- Resource utilization (CPU, memory)
- Bundle sizes and load times
- Database query performance

## Process

1. Define performance benchmarks
2. Set up automated performance testing in CI/CD
3. Implement regression detection logic
4. Configure notification and reporting
5. Create remediation workflows

## Output

Provide:
- Performance test suite setup
- Baseline performance data collection
- CI/CD integration configuration
- Regression detection thresholds
- Automated reporting setup
- Pull request comment integration
- Remediation workflow documentation
