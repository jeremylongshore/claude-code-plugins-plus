# Performance Test Suite Plugin

Comprehensive load testing and performance benchmarking with intelligent metrics analysis, bottleneck identification, and actionable recommendations.

## Features

- **Load testing** - Gradual ramp-up, sustained load, peak capacity
- **Stress testing** - Breaking point identification, recovery validation
- **Spike testing** - Sudden traffic surges, flash sale scenarios
- **Endurance testing** - Long-running stability, memory leak detection
- **Metrics analysis** - Response times, throughput, error rates, resources
- **Bottleneck identification** - CPU, memory, database, network issues
- **Comprehensive reporting** - Percentiles, graphs, recommendations

## Installation

```bash
/plugin install performance-test-suite@claude-code-plugins-plus
```

## Usage

The performance testing agent activates automatically when discussing performance or load testing:

### Design load test

```
Create a load test for the API that ramps up to 500 concurrent users over 5 minutes
```

### Stress test to find limits

```
Design a stress test to find the breaking point of the checkout API
```

### Spike test for flash sales

```
Create a spike test simulating a flash sale with sudden 10x traffic increase
```

### Endurance test for stability

```
Design an endurance test running at 200 users for 4 hours to check for memory leaks
```

## Test Types

### 1. Load Testing

Gradually increase load to test normal operating conditions:

```javascript
// k6 load test
export let options = {
  stages: [
    { duration: '5m', target: 100 },   // Ramp up
    { duration: '10m', target: 100 },  // Sustain
    { duration: '5m', target: 0 },     // Ramp down
  ],
};
```

**Validates:**
- Normal performance under expected load
- Response times remain acceptable
- Error rates stay low
- Resources adequate for traffic

### 2. Stress Testing

Push system beyond normal load to find limits:

```javascript
// k6 stress test
export let options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 200 },
    { duration: '5m', target: 300 },
    { duration: '5m', target: 400 },
    { duration: '10m', target: 400 },
  ],
};
```

**Validates:**
- Maximum capacity before failure
- Graceful degradation under stress
- Recovery after overload
- Error handling at limits

### 3. Spike Testing

Sudden dramatic traffic increases:

```javascript
// k6 spike test
export let options = {
  stages: [
    { duration: '10s', target: 50 },    // Normal load
    { duration: '1m', target: 500 },    // Sudden spike
    { duration: '3m', target: 500 },    // Sustain spike
    { duration: '10s', target: 50 },    // Return to normal
  ],
};
```

**Validates:**
- Auto-scaling response
- Rate limiting effectiveness
- System stability during surge
- Recovery time after spike

### 4. Endurance Testing (Soak Test)

Extended duration at moderate load:

```javascript
// k6 endurance test
export let options = {
  stages: [
    { duration: '2m', target: 200 },
    { duration: '4h', target: 200 },    // Long soak
    { duration: '2m', target: 0 },
  ],
};
```

**Validates:**
- Memory leaks over time
- Resource exhaustion
- Connection pool issues
- Long-term stability

## Metrics Collected

### Response Time Metrics

- **Average** - Mean response time
- **Median (P50)** - Half of requests faster
- **P95** - 95% of requests faster (SLA metric)
- **P99** - 99% of requests faster (tail latency)
- **Max** - Slowest request

### Throughput Metrics

- **Requests/second** - Total throughput
- **Success rate** - Percentage successful
- **Error rate** - Percentage failed
- **Data transferred** - Bandwidth usage

### Resource Metrics

- **CPU usage** - Average and peak utilization
- **Memory usage** - Allocation and growth
- **Network I/O** - Bandwidth consumption
- **Disk I/O** - Read/write operations
- **Database connections** - Pool usage

## Bottleneck Identification

The agent identifies common performance issues:

### High CPU Usage
- Inefficient algorithms
- Missing caching
- Excessive computations
- Unoptimized loops

### High Memory Usage
- Memory leaks
- Large object retention
- Inefficient data structures
- Missing garbage collection

### Slow Database
- N+1 query problems
- Missing indexes
- Inefficient queries
- Connection pool exhaustion

### Network Saturation
- Large response payloads
- Missing compression
- Too many requests
- Inefficient protocols

## Example Report

```
Performance Test Report
=======================
Test: Load Test - API Endpoints
Date: 2025-10-11 14:30:00
Duration: 20 minutes
Max Virtual Users: 300

 Response Time Metrics
  Average: 145ms
  Median (P50): 120ms
  P95: 280ms  (Target: <300ms)
  P99: 450ms  (Target: <500ms)
  Max: 1,230ms

 Throughput
  Total Requests: 90,000
  Requests/sec: 75
  Success Rate: 99.4% 
  Error Rate: 0.6%

 Resource Utilization
  CPU: 68% avg, 87% peak
  Memory: 2.8 GB / 4 GB (70%)
  Network: 22 MB/s avg

 Bottlenecks Identified
  1. GET /api/users - P95: 850ms (database index needed)
  2. Database connection pool at 95% usage
  3. Memory climbing 50MB/hour (potential leak)

 Recommendations
  1. Add index on users.email column → -70% query time
  2. Increase connection pool: 20 → 50 connections
  3. Implement Redis caching for user list endpoint
  4. Investigate session manager memory leak
  5. Consider horizontal scaling at 350+ users

 Pass Criteria Met: 4/5
   P95 response time < 300ms
   P99 response time < 500ms
   Error rate < 1%
   Success rate > 99%
   No memory leaks detected
```

## Supported Tools

The agent generates tests for popular tools:

| Tool | Language | Best For |
|------|----------|----------|
| k6 | JavaScript | Modern API testing, great DX |
| Apache JMeter | Java | Enterprise, GUI-based |
| Gatling | Scala | High load, excellent reports |
| Locust | Python | Distributed testing, custom logic |
| Artillery | Node.js | Quick setup, YAML config |
| wrk | C | Raw HTTP benchmarking |

## Best Practices Applied

- **Realistic scenarios** - Simulate actual user behavior
- **Gradual ramp-up** - Don't spike from 0 to max instantly
- **Think time** - Pause between requests like real users
- **Data variation** - Use different data each request
- **Monitor everything** - Track all system resources
- **Production-like environment** - Match production as closely as possible
- **Baseline comparison** - Compare against previous tests
- **Clear success criteria** - Define thresholds before testing

## Requirements

- Claude Code CLI
- Performance testing tool (k6, Locust, JMeter, etc.)
- Monitoring tools (optional but recommended)
- Test environment matching production

## Tips

1. **Start small** - Begin with 10 users, scale up gradually
2. **Test one thing** - Isolate variables (don't change code during test)
3. **Monitor during tests** - Watch dashboards in real-time
4. **Use production data** - Test with realistic datasets
5. **Test regularly** - Performance regression detection
6. **Document findings** - Track improvements over time
7. **Fix bottlenecks** - Address issues in priority order

## License

MIT
