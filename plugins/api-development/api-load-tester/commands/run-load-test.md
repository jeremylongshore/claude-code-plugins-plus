---
description: Run API load tests with k6, Artillery, or Gatling to measure performance under load
shortcut: loadtest
---

# Run API Load Test

Execute comprehensive load tests to measure API performance, identify bottlenecks, and validate scalability under realistic traffic patterns.

## Design Decisions

This command supports multiple load testing tools to accommodate different testing scenarios and team preferences:

- **k6**: Chosen for developer-friendly JavaScript API, excellent CLI output, and built-in metrics
- **Artillery**: Selected for YAML configuration simplicity and scenario-based testing
- **Gatling**: Included for enterprise-grade reporting and Scala DSL power users

Alternative approaches considered:
- **JMeter**: Excluded due to GUI-heavy approach and XML configuration complexity
- **Locust**: Considered but not included to limit Python dependencies
- **Custom solutions**: Avoided to leverage battle-tested tools with proven metrics accuracy

## When to Use This Command

**USE WHEN:**
- Validating API performance before production deployment
- Establishing baseline performance metrics for SLAs
- Testing autoscaling behavior under load
- Identifying memory leaks or resource exhaustion issues
- Comparing performance across API versions
- Simulating Black Friday or high-traffic events

**DON'T USE WHEN:**
- Testing production APIs without permission (use staging environments)
- You need functional correctness testing (use integration tests instead)
- Testing third-party APIs you don't control
- During active development (use unit/integration tests first)

## Prerequisites

**Required:**
- Node.js 18+ (for k6 and Artillery)
- Java 11+ (for Gatling)
- Target API endpoint accessible from your machine
- API authentication credentials (if required)

**Recommended:**
- Monitoring tools configured (Prometheus, Grafana, DataDog)
- Baseline metrics from previous test runs
- Staging environment that mirrors production capacity

**Install Tools:**
```bash
# k6 (recommended for most use cases)
brew install k6  # macOS
sudo apt-get install k6  # Ubuntu

# Artillery
npm install -g artillery

# Gatling
wget https://repo1.maven.org/maven2/io/gatling/highcharts/gatling-charts-highcharts-bundle/3.9.5/gatling-charts-highcharts-bundle-3.9.5.zip
unzip gatling-charts-highcharts-bundle-3.9.5.zip
```

## Detailed Process

### Step 1: Define Test Objectives
Establish clear performance targets before running tests:
- **Response time**: p95 < 200ms, p99 < 500ms
- **Throughput**: 1000 requests/second sustained
- **Error rate**: < 0.1% under normal load
- **Concurrent users**: Support 500 simultaneous users

Document expected behavior under different load levels:
- Normal load: 100-500 RPS
- Peak load: 1000-2000 RPS
- Stress test: 3000+ RPS until failure

### Step 2: Configure Test Scenario
Create test scripts matching realistic user behavior patterns:

**k6 test script** (`load-test.js`):
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp-up
    { duration: '5m', target: 100 },  // Sustained load
    { duration: '2m', target: 200 },  // Scale up
    { duration: '5m', target: 200 },  // Sustained peak
    { duration: '2m', target: 0 },    // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200', 'p(99)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get('https://api.example.com/v1/products');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
  sleep(1);
}
```

**Artillery config** (`artillery.yml`):
```yaml
config:
  target: 'https://api.example.com'
  phases:
    - duration: 60
      arrivalRate: 10
      name: "Warm up"
    - duration: 300
      arrivalRate: 50
      name: "Sustained load"
    - duration: 120
      arrivalRate: 100
      name: "Peak load"
  processor: "./flows.js"
scenarios:
  - name: "Product browsing flow"
    flow:
      - get:
          url: "/v1/products"
          capture:
            - json: "$.products[0].id"
              as: "productId"
      - get:
          url: "/v1/products/{{ productId }}"
      - think: 3
```

### Step 3: Execute Load Test
Run tests with appropriate parameters and monitor system resources:

```bash
# k6 test execution with custom parameters
k6 run load-test.js \
  --vus 100 \
  --duration 10m \
  --out json=results.json \
  --summary-export=summary.json

# Artillery with real-time reporting
artillery run artillery.yml \
  --output report.json

# Gatling test execution
./gatling.sh -s com.example.LoadTest \
  -rf results/
```

Monitor system metrics during execution:
- CPU utilization (should stay below 80%)
- Memory consumption (watch for leaks)
- Network I/O (bandwidth saturation)
- Database connections (connection pool exhaustion)

### Step 4: Analyze Results
Review metrics to identify performance bottlenecks:

**Response Time Analysis:**
```bash
# k6 summary shows percentile distribution
  http_req_duration..............: avg=156ms  p(95)=289ms p(99)=456ms
  http_req_failed................: 0.12% (12 failures / 10000 requests)
  http_reqs......................: 10000  166.67/s
  vus............................: 100    min=0 max=100
```

Key metrics to examine:
- **p50 (median)**: Typical user experience
- **p95**: Worst case for 95% of users
- **p99**: Tail latency affecting 1% of requests
- **Error rate**: Percentage of failed requests
- **Throughput**: Successful requests per second

### Step 5: Generate Reports and Recommendations
Create actionable reports with findings and optimization suggestions:

**Performance Report Structure:**
```markdown
# Load Test Results - 2025-10-11

## Test Configuration
- Duration: 10 minutes
- Virtual Users: 100
- Target: https://api.example.com/v1/products

## Results Summary
- Total Requests: 10,000
- Success Rate: 99.88%
- Avg Response Time: 156ms
- p95 Response Time: 289ms
- Throughput: 166.67 RPS

## Findings
1. Database query optimization needed (p99 spikes to 456ms)
2. Connection pool exhausted at 150 concurrent users
3. Memory leak detected after 8 minutes

## Recommendations
1. Add database indexes on product_id and category
2. Increase connection pool from 20 to 50
3. Fix memory leak in image processing service
```

## Output Format

The command generates structured performance reports:

**Console Output:**
```
Running load test with k6...

  execution: local
    script: load-test.js
    output: json (results.json)

  scenarios: (100.00%) 1 scenario, 200 max VUs, 17m0s max duration

  data_received..................: 48 MB   80 kB/s
  data_sent......................: 2.4 MB  4.0 kB/s
  http_req_blocked...............: avg=1.23ms   p(95)=3.45ms  p(99)=8.91ms
  http_req_connecting............: avg=856µs    p(95)=2.34ms  p(99)=5.67ms
  http_req_duration..............: avg=156.78ms p(95)=289.45ms p(99)=456.12ms
  http_req_failed................: 0.12%
  http_req_receiving.............: avg=234µs    p(95)=567µs   p(99)=1.23ms
  http_req_sending...............: avg=123µs    p(95)=345µs   p(99)=789µs
  http_req_tls_handshaking.......: avg=0s       p(95)=0s      p(99)=0s
  http_req_waiting...............: avg=156.42ms p(95)=288.89ms p(99)=455.34ms
  http_reqs......................: 10000   166.67/s
  iteration_duration.............: avg=1.16s    p(95)=1.29s   p(99)=1.46s
  iterations.....................: 10000   166.67/s
  vus............................: 100     min=0 max=200
  vus_max........................: 200     min=200 max=200
```

**JSON Report:**
```json
{
  "metrics": {
    "http_req_duration": {
      "avg": 156.78,
      "p95": 289.45,
      "p99": 456.12
    },
    "http_req_failed": 0.0012,
    "http_reqs": {
      "count": 10000,
      "rate": 166.67
    }
  },
  "root_group": {
    "checks": {
      "status is 200": {
        "passes": 9988,
        "fails": 12
      }
    }
  }
}
```

## Code Examples

### Example 1: Basic Load Test with k6

Test a REST API endpoint with gradual ramp-up and threshold validation:

```javascript
// basic-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

export const options = {
  // Ramp-up pattern: 0 -> 50 -> 100 -> 50 -> 0
  stages: [
    { duration: '1m', target: 50 },   // Ramp-up to 50 users
    { duration: '3m', target: 50 },   // Stay at 50 users
    { duration: '1m', target: 100 },  // Spike to 100 users
    { duration: '3m', target: 100 },  // Stay at 100 users
    { duration: '1m', target: 50 },   // Scale down to 50
    { duration: '1m', target: 0 },    // Ramp-down to 0
  ],

  // Performance thresholds (test fails if exceeded)
  thresholds: {
    'http_req_duration': ['p(95)<300', 'p(99)<500'],
    'http_req_failed': ['rate<0.01'],  // Less than 1% errors
    'errors': ['rate<0.1'],
  },
};

export default function () {
  // Test parameters
  const baseUrl = 'https://api.example.com';
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${__ENV.API_TOKEN}`,
    },
  };

  // API request
  const res = http.get(`${baseUrl}/v1/products?limit=20`, params);

  // Validation checks
  const checkRes = check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 300ms': (r) => r.timings.duration < 300,
    'has products': (r) => r.json('products').length > 0,
    'valid JSON': (r) => {
      try {
        JSON.parse(r.body);
        return true;
      } catch (e) {
        return false;
      }
    },
  });

  // Track custom error metric
  errorRate.add(!checkRes);

  // Simulate user think time
  sleep(Math.random() * 3 + 1); // 1-4 seconds
}

// Teardown function (runs once at end)
export function teardown(data) {
  console.log('Load test completed');
}
```

**Run command:**
```bash
# Set API token and execute
export API_TOKEN="your-token-here"
k6 run basic-load-test.js \
  --out json=results.json \
  --summary-export=summary.json

# Generate HTML report from JSON
k6-reporter results.json --output report.html
```

### Example 2: Stress Testing with Artillery

Test API breaking point with gradual load increase until failure:

```yaml
# stress-test.yml
config:
  target: 'https://api.example.com'
  phases:
    # Gradual ramp-up to find breaking point
    - duration: 60
      arrivalRate: 10
      name: "Phase 1: Baseline (10 RPS)"
    - duration: 60
      arrivalRate: 50
      name: "Phase 2: Moderate (50 RPS)"
    - duration: 60
      arrivalRate: 100
      name: "Phase 3: High (100 RPS)"
    - duration: 60
      arrivalRate: 200
      name: "Phase 4: Stress (200 RPS)"
    - duration: 60
      arrivalRate: 400
      name: "Phase 5: Breaking point (400 RPS)"

  # Environment variables
  variables:
    api_token: "{{ $processEnvironment.API_TOKEN }}"

  # HTTP settings
  http:
    timeout: 10
    pool: 50

  # Custom plugins
  plugins:
    expect: {}
    metrics-by-endpoint: {}

  # Success criteria
  ensure:
    p95: 500
    p99: 1000
    maxErrorRate: 1

# Test scenarios
scenarios:
  - name: "Product CRUD operations"
    weight: 70
    flow:
      # List products
      - get:
          url: "/v1/products"
          headers:
            Authorization: "Bearer {{ api_token }}"
          expect:
            - statusCode: 200
            - contentType: json
            - hasProperty: products
          capture:
            - json: "$.products[0].id"
              as: "productId"

      # Get product details
      - get:
          url: "/v1/products/{{ productId }}"
          headers:
            Authorization: "Bearer {{ api_token }}"
          expect:
            - statusCode: 200
            - hasProperty: id

      # Think time (user reading)
      - think: 2

      # Search products
      - get:
          url: "/v1/products/search?q=laptop"
          headers:
            Authorization: "Bearer {{ api_token }}"
          expect:
            - statusCode: 200

  - name: "User authentication flow"
    weight: 20
    flow:
      - post:
          url: "/v1/auth/login"
          json:
            email: "test@example.com"
            password: "password123"
          expect:
            - statusCode: 200
            - hasProperty: token
          capture:
            - json: "$.token"
              as: "userToken"

      - get:
          url: "/v1/users/me"
          headers:
            Authorization: "Bearer {{ userToken }}"
          expect:
            - statusCode: 200

  - name: "Shopping cart operations"
    weight: 10
    flow:
      - post:
          url: "/v1/cart/items"
          headers:
            Authorization: "Bearer {{ api_token }}"
          json:
            productId: "{{ productId }}"
            quantity: 1
          expect:
            - statusCode: 201

      - get:
          url: "/v1/cart"
          headers:
            Authorization: "Bearer {{ api_token }}"
          expect:
            - statusCode: 200
            - hasProperty: items
```

**Run with custom processor:**
```javascript
// flows.js - Custom logic for Artillery
module.exports = {
  // Before request hook
  setAuthToken: function(requestParams, context, ee, next) {
    requestParams.headers = requestParams.headers || {};
    requestParams.headers['X-Request-ID'] = `req-${Date.now()}-${Math.random()}`;
    return next();
  },

  // After response hook
  logResponse: function(requestParams, response, context, ee, next) {
    if (response.statusCode >= 400) {
      console.log(`Error: ${response.statusCode} - ${requestParams.url}`);
    }
    return next();
  },

  // Custom function to generate dynamic data
  generateTestData: function(context, events, done) {
    context.vars.userId = `user-${Math.floor(Math.random() * 10000)}`;
    context.vars.timestamp = new Date().toISOString();
    return done();
  }
};
```

**Execute stress test:**
```bash
# Run with environment variable
API_TOKEN="your-token" artillery run stress-test.yml \
  --output stress-results.json

# Generate HTML report
artillery report stress-results.json \
  --output stress-report.html

# Run with custom config overrides
artillery run stress-test.yml \
  --config config.phases[0].duration=30 \
  --config config.phases[0].arrivalRate=20
```

### Example 3: Performance Testing with Gatling (Scala DSL)

Enterprise-grade load test with complex scenarios and detailed reporting:

```scala
// LoadSimulation.scala
package com.example.loadtest

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class ApiLoadSimulation extends Simulation {

  // HTTP protocol configuration
  val httpProtocol = http
    .baseUrl("https://api.example.com")
    .acceptHeader("application/json")
    .authorizationHeader("Bearer ${accessToken}")
    .userAgentHeader("Gatling Load Test")
    .shareConnections

  // Feeders for test data
  val userFeeder = csv("users.csv").circular
  val productFeeder = csv("products.csv").random

  // Custom headers
  val sentHeaders = Map(
    "X-Request-ID" -> "${requestId}",
    "X-Client-Version" -> "1.0.0"
  )

  // Scenario 1: Browse products
  val browseProducts = scenario("Browse Products")
    .feed(userFeeder)
    .exec(session => session.set("requestId", java.util.UUID.randomUUID.toString))
    .exec(
      http("List Products")
        .get("/v1/products")
        .headers(sentHeaders)
        .check(status.is(200))
        .check(jsonPath("$.products[*].id").findAll.saveAs("productIds"))
    )
    .pause(2, 5)
    .exec(
      http("Get Product Details")
        .get("/v1/products/${productIds.random()}")
        .check(status.is(200))
        .check(jsonPath("$.id").exists)
        .check(jsonPath("$.price").ofType[Double].saveAs("price"))
    )
    .pause(1, 3)

  // Scenario 2: Search and filter
  val searchProducts = scenario("Search Products")
    .exec(session => session.set("requestId", java.util.UUID.randomUUID.toString))
    .exec(
      http("Search Products")
        .get("/v1/products/search")
        .queryParam("q", "laptop")
        .queryParam("minPrice", "500")
        .queryParam("maxPrice", "2000")
        .headers(sentHeaders)
        .check(status.is(200))
        .check(jsonPath("$.total").ofType[Int].gt(0))
    )
    .pause(2, 4)
    .exec(
      http("Apply Filters")
        .get("/v1/products/search")
        .queryParam("q", "laptop")
        .queryParam("brand", "Dell")
        .queryParam("sort", "price")
        .check(status.is(200))
    )

  // Scenario 3: Checkout flow
  val checkout = scenario("Checkout Flow")
    .feed(userFeeder)
    .feed(productFeeder)
    .exec(session => session.set("requestId", java.util.UUID.randomUUID.toString))
    .exec(
      http("Add to Cart")
        .post("/v1/cart/items")
        .headers(sentHeaders)
        .body(StringBody("""{"productId": "${productId}", "quantity": 1}"""))
        .asJson
        .check(status.is(201))
        .check(jsonPath("$.cartId").saveAs("cartId"))
    )
    .pause(1, 2)
    .exec(
      http("Get Cart")
        .get("/v1/cart/${cartId}")
        .check(status.is(200))
        .check(jsonPath("$.total").ofType[Double].saveAs("total"))
    )
    .pause(2, 4)
    .exec(
      http("Create Order")
        .post("/v1/orders")
        .body(StringBody("""{"cartId": "${cartId}", "paymentMethod": "credit_card"}"""))
        .asJson
        .check(status.in(200, 201))
        .check(jsonPath("$.orderId").saveAs("orderId"))
    )
    .exec(
      http("Get Order Status")
        .get("/v1/orders/${orderId}")
        .check(status.is(200))
        .check(jsonPath("$.status").is("pending"))
    )

  // Load profile: Realistic production traffic pattern
  setUp(
    // 70% users browse products
    browseProducts.inject(
      rampUsersPerSec(1) to 50 during (2 minutes),
      constantUsersPerSec(50) during (5 minutes),
      rampUsersPerSec(50) to 100 during (3 minutes),
      constantUsersPerSec(100) during (5 minutes),
      rampUsersPerSec(100) to 0 during (2 minutes)
    ).protocols(httpProtocol),

    // 20% users search
    searchProducts.inject(
      rampUsersPerSec(1) to 15 during (2 minutes),
      constantUsersPerSec(15) during (10 minutes),
      rampUsersPerSec(15) to 0 during (2 minutes)
    ).protocols(httpProtocol),

    // 10% users complete checkout
    checkout.inject(
      rampUsersPerSec(1) to 10 during (3 minutes),
      constantUsersPerSec(10) during (10 minutes),
      rampUsersPerSec(10) to 0 during (2 minutes)
    ).protocols(httpProtocol)
  ).protocols(httpProtocol)
   .assertions(
     global.responseTime.max.lt(2000),
     global.responseTime.percentile3.lt(500),
     global.successfulRequests.percent.gt(99)
   )
}
```

**Supporting data files:**

`users.csv`:
```csv
userId,accessToken
user-001,eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
user-002,eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
user-003,eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

`products.csv`:
```csv
productId,category
prod-001,electronics
prod-002,clothing
prod-003,books
```

**Run Gatling simulation:**
```bash
# Using Gatling Maven plugin
mvn gatling:test -Dgatling.simulationClass=com.example.loadtest.ApiLoadSimulation

# Using standalone Gatling
./gatling.sh -s com.example.loadtest.ApiLoadSimulation \
  -rf results/

# Generate report only (from previous run)
./gatling.sh -ro results/apisimulation-20251011143022456
```

**Gatling configuration** (`gatling.conf`):
```hocon
gatling {
  core {
    outputDirectoryBaseName = "api-load-test"
    runDescription = "Production load simulation"
    encoding = "utf-8"
    simulationClass = ""
  }
  charting {
    indicators {
      lowerBound = 100      # Lower bound for response time (ms)
      higherBound = 500     # Higher bound for response time (ms)
      percentile1 = 50      # First percentile
      percentile2 = 75      # Second percentile
      percentile3 = 95      # Third percentile
      percentile4 = 99      # Fourth percentile
    }
  }
  http {
    ahc {
      pooledConnectionIdleTimeout = 60000
      readTimeout = 60000
      requestTimeout = 60000
      connectionTimeout = 30000
      maxConnections = 200
      maxConnectionsPerHost = 50
    }
  }
  data {
    writers = [console, file]
  }
}
```

## Error Handling

Common errors and solutions:

**Connection Refused:**
```
Error: connect ECONNREFUSED 127.0.0.1:8080
```
Solution: Verify API is running and accessible. Check network connectivity and firewall rules.

**Timeout Errors:**
```
http_req_failed: 45.2% (4520 failures / 10000 requests)
```
Solution: Increase timeout values or reduce concurrent users. API may be overwhelmed.

**SSL/TLS Errors:**
```
Error: x509: certificate signed by unknown authority
```
Solution: Add `insecureSkipTLSVerify: true` or configure proper CA certificates.

**Rate Limiting:**
```
HTTP 429 Too Many Requests
```
Solution: Reduce request rate or increase rate limits on API server. Add backoff logic.

**Memory Exhaustion:**
```
JavaScript heap out of memory
```
Solution: Increase Node.js memory limit: `NODE_OPTIONS=--max-old-space-size=4096 k6 run test.js`

**Authentication Failures:**
```
HTTP 401 Unauthorized
```
Solution: Verify API tokens are valid and not expired. Check authorization headers.

## Configuration Options

### k6 Options

```bash
--vus N                    # Number of virtual users (default: 1)
--duration Xm              # Test duration (e.g., 10m, 30s)
--iterations N             # Total iterations across all VUs
--stage "Xm:N"            # Add load stage (duration:target)
--rps N                    # Max requests per second
--max-redirects N          # Max HTTP redirects (default: 10)
--batch N                  # Max parallel batch requests
--batch-per-host N         # Max parallel requests per host
--http-debug              # Enable HTTP debug logging
--no-connection-reuse     # Disable HTTP keep-alive
--throw                   # Throw errors on failed HTTP requests
--summary-trend-stats     # Custom summary stats (e.g., "avg,p(95),p(99)")
--out json=file.json      # Export results to JSON
--out influxdb=http://... # Export to InfluxDB
--out statsd              # Export to StatsD
```

### Artillery Options

```bash
--target URL               # Override target URL
--output FILE              # Save results to JSON file
--overrides FILE           # Override config with JSON file
--variables FILE           # Load variables from JSON
--config KEY=VALUE         # Override single config value
--environment ENV          # Select environment from config
--solo                     # Run test without publishing
--quiet                    # Suppress output
--plugins                  # List installed plugins
--dotenv FILE              # Load environment from .env file
```

### Gatling Options

```bash
-s CLASS                   # Simulation class to run
-rf FOLDER                 # Results folder
-rd DESC                   # Run description
-nr                        # No reports generation
-ro FOLDER                 # Generate reports only
```

## Best Practices

### DO:
- Start with baseline test (low load) to verify test scripts work correctly
- Ramp up load gradually to identify inflection points
- Monitor backend resources (CPU, memory, database) during tests
- Use realistic think times (1-5 seconds) to simulate user behavior
- Test in staging environment that mirrors production capacity
- Run tests multiple times to establish consistency
- Document test configuration and results for historical comparison
- Use connection pooling and HTTP keep-alive for realistic scenarios
- Set appropriate timeouts (30-60 seconds for most APIs)
- Clean up test data after runs (especially for write-heavy tests)

### DON'T:
- Don't load test production without explicit permission and monitoring
- Don't ignore warmup period (JIT compilation, cache warming)
- Don't test from same datacenter as API (unrealistic latency)
- Don't use default test data (create realistic, varied datasets)
- Don't skip cool-down period (observe resource cleanup)
- Don't test only happy paths (include error scenarios)
- Don't ignore database connection limits
- Don't run tests during production deployments
- Don't compare results across different network conditions
- Don't test third-party APIs without permission

### TIPS:
- Use distributed load generation for tests > 1000 VUs
- Export metrics to monitoring systems (Prometheus, DataDog) for correlation
- Create custom dashboards showing load test progress in real-time
- Use percentiles (p95, p99) instead of averages for SLA targets
- Test cache warm vs cold scenarios separately
- Include authentication overhead in realistic flows
- Validate response bodies, not just status codes
- Use unique IDs per virtual user to avoid data conflicts
- Schedule tests during low-traffic periods
- Keep test scripts in version control with API code

## Related Commands

- `/api-mock-server` - Create mock API for testing without backend
- `/api-monitoring-dashboard` - Set up real-time monitoring during load tests
- `/api-cache-manager` - Configure caching to improve performance under load
- `/api-rate-limiter` - Implement rate limiting to protect APIs
- `/deployment-pipeline-orchestrator` - Integrate load tests into CI/CD pipeline
- `/kubernetes-deployment-creator` - Configure autoscaling based on load test findings

## Performance Considerations

### Test Environment Sizing
- **Client machine**: 1 VU ≈ 1-10 MB RAM, 0.01-0.1 CPU cores
- **Network bandwidth**: 1000 VUs ≈ 10-100 Mbps depending on payload size
- **k6 limits**: Single instance handles 30,000-40,000 VUs (depends on script complexity)
- **Artillery limits**: Single instance handles 5,000-10,000 RPS
- **Gatling limits**: Single instance handles 50,000+ VUs (JVM-based)

### Backend Resource Planning
- **Database connections**: Plan for peak concurrent users + connection pool overhead
- **CPU utilization**: Keep below 80% under sustained load (leave headroom for spikes)
- **Memory**: Monitor for leaks (heap should stabilize after warmup)
- **Network I/O**: Ensure network bandwidth exceeds expected throughput by 50%

### Optimization Strategies
- **HTTP keep-alive**: Reduces connection overhead by 50-80%
- **Response compression**: Reduces bandwidth by 60-80% for text responses
- **CDN caching**: Offloads 70-90% of static asset requests
- **Database indexing**: Can improve query performance by 10-100x
- **Connection pooling**: Reduces latency by 20-50ms per request

## Security Notes

### Testing Permissions
- Obtain written approval before load testing any environment
- Verify testing is allowed by API terms of service
- Use dedicated test accounts with limited privileges
- Test in isolated environments to prevent data corruption

### Credential Management
- Never hardcode API keys or passwords in test scripts
- Use environment variables: `export API_TOKEN=$(vault read -field=token secret/api)`
- Rotate test credentials regularly
- Use short-lived tokens (JWT with 1-hour expiry)
- Store sensitive data in secrets managers (Vault, AWS Secrets Manager)

### Data Privacy
- Use synthetic test data (never real customer PII)
- Anonymize logs and results before sharing
- Clean up test data immediately after test completion
- Encrypt results files containing sensitive information

### Network Security
- Run tests from trusted networks (avoid public WiFi)
- Use VPN when testing internal APIs
- Implement IP whitelisting for test traffic
- Monitor for anomalous traffic patterns during tests

## Troubleshooting Guide

### Issue: Inconsistent Results Between Runs
**Symptoms:** Response times vary by > 50% between identical test runs
**Diagnosis:**
- Check for background jobs or cron tasks running during test
- Verify database wasn't backed up during test
- Ensure no other load tests running concurrently
**Solution:**
- Schedule tests during known quiet periods
- Disable background tasks during test window
- Run multiple iterations and take median results

### Issue: Low Throughput Despite Low CPU/Memory
**Symptoms:** API handling only 100 RPS despite 20% CPU usage
**Diagnosis:**
- Check network bandwidth utilization
- Examine database connection pool exhaustion
- Look for synchronous I/O blocking (file system, external API calls)
**Solution:**
- Increase connection pool size
- Implement async I/O for external calls
- Add caching layer (Redis) for frequently accessed data

### Issue: Error Rate Increases Under Load
**Symptoms:** 0.1% errors at 100 RPS, 5% errors at 500 RPS
**Diagnosis:**
- Database deadlocks or lock contention
- Race conditions in concurrent code paths
- Resource exhaustion (file descriptors, sockets)
**Solution:**
- Add database query logging to identify slow queries
- Implement optimistic locking or queue-based processing
- Increase file descriptor limits: `ulimit -n 65536`

### Issue: Memory Leak Detected
**Symptoms:** Memory usage grows continuously without stabilizing
**Diagnosis:**
- Heap dump analysis shows growing object count
- GC frequency increases over time
- API becomes unresponsive after extended load
**Solution:**
- Profile application with heap analyzer (Chrome DevTools, VisualVM)
- Check for unclosed database connections or file handles
- Review event listener registration (potential memory leak source)

### Issue: Test Client Crashes
**Symptoms:** k6/Artillery process terminated with OOM error
**Diagnosis:**
- Too many VUs for available client memory
- Large response bodies consuming memory
- Results export causing memory pressure
**Solution:**
- Reduce VU count or distribute across multiple machines
- Increase Node.js memory: `NODE_OPTIONS=--max-old-space-size=8192`
- Disable detailed logging: `--quiet` or `--summary-export` only

## Version History

- **1.0.0** (2025-10-11) - Initial release with k6, Artillery, and Gatling support
- **1.1.0** (2025-10-15) - Added custom metrics and Prometheus integration
- **1.2.0** (2025-10-20) - Distributed load testing support for high-scale scenarios
