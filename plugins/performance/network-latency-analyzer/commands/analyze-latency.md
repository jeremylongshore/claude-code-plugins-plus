---
name: analyze-latency
description: Analyze network latency and request patterns
---
# Network Latency Analyzer

Analyze network request patterns and optimize for reduced latency.

## Analysis Focus

1. **Serial Requests**: Requests that could be parallelized
2. **Request Batching**: Opportunities to batch multiple requests
3. **Connection Pooling**: HTTP connection reuse
4. **Timeout Configuration**: Request timeout settings
5. **Retry Logic**: Exponential backoff implementation
6. **DNS Resolution**: DNS caching opportunities
7. **Request Size**: Payload optimization

## Process

1. Identify all network requests in codebase
2. Analyze request patterns and dependencies
3. Check for serial vs parallel execution
4. Evaluate timeout and retry strategies
5. Generate optimization recommendations

## Output

Provide markdown report with:
- Network request inventory
- Latency bottleneck identification
- Parallelization opportunities with code examples
- Connection pooling recommendations
- Timeout and retry strategy improvements
- Estimated latency reductions
