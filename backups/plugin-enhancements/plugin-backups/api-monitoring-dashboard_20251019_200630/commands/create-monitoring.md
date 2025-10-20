---
description: Create API monitoring dashboard
shortcut: monitor
---

# Create API Monitoring Dashboard

Build comprehensive monitoring infrastructure with metrics, logs, traces, and alerts for full API observability.

## When to Use This Command

Use `/create-monitoring` when you need to:
- Establish observability for production APIs
- Track RED metrics (Rate, Errors, Duration) across services
- Set up real-time alerting for SLO violations
- Debug performance issues with distributed tracing
- Create executive dashboards for API health
- Implement SRE practices with data-driven insights

DON'T use this when:
- Building proof-of-concept applications (use lightweight logging instead)
- Monitoring non-critical internal tools (basic health checks may suffice)
- Resources are extremely constrained (consider managed solutions like Datadog first)

## Design Decisions

This command implements a **Prometheus + Grafana stack** as the primary approach because:
- Open-source with no vendor lock-in
- Industry-standard metric format with wide ecosystem support
- Powerful query language (PromQL) for complex analysis
- Horizontal scalability via federation and remote storage

**Alternative considered: ELK Stack** (Elasticsearch, Logstash, Kibana)
- Better for log-centric analysis
- Higher resource requirements
- More complex operational overhead
- Recommended when logs are primary data source

**Alternative considered: Managed solutions** (Datadog, New Relic)
- Faster time-to-value
- Higher ongoing cost
- Less customization flexibility
- Recommended for teams without dedicated DevOps

## Prerequisites

Before running this command:
1. Docker and Docker Compose installed
2. API instrumented with metrics endpoints (Prometheus format)
3. Basic understanding of PromQL query language
4. Network access for inter-service communication
5. Sufficient disk space for time-series data (plan for 2-4 weeks retention)

## Implementation Process

### Step 1: Configure Prometheus
Set up Prometheus to scrape metrics from your API endpoints with service discovery.

### Step 2: Create Grafana Dashboards
Build visualizations for RED metrics, custom business metrics, and SLO tracking.

### Step 3: Implement Distributed Tracing
Integrate Jaeger for end-to-end request tracing across microservices.

### Step 4: Configure Alerting
Set up AlertManager rules for critical thresholds with notification channels (Slack, PagerDuty).

### Step 5: Deploy Monitoring Stack
Deploy complete observability infrastructure with health checks and backup configurations.

## Output Format

The command generates:
- `docker-compose.yml` - Complete monitoring stack configuration
- `prometheus.yml` - Prometheus scrape configuration
- `grafana-dashboards/` - Pre-built dashboard JSON files
- `alerting-rules.yml` - AlertManager rule definitions
- `jaeger-config.yml` - Distributed tracing configuration
- `README.md` - Deployment and operation guide

## Code Examples

### Example 1: Complete Node.js Express API with Comprehensive Monitoring

```javascript
// metrics/instrumentation.js - Full-featured Prometheus instrumentation
const promClient = require('prom-client');
const { performance } = require('perf_hooks');
const os = require('os');

class MetricsCollector {
  constructor() {
    // Create separate registries for different metric types
    this.register = new promClient.Registry();
    this.businessRegister = new promClient.Registry();

    // Add default system metrics
    promClient.collectDefaultMetrics({
      register: this.register,
      prefix: 'api_',
      gcDurationBuckets: [0.001, 0.01, 0.1, 1, 2, 5]
    });

    // Initialize all metric types
    this.initializeMetrics();
    this.initializeBusinessMetrics();
    this.initializeCustomCollectors();

    // Start periodic collectors
    this.startPeriodicCollectors();
  }

  initializeMetrics() {
    // RED Metrics (Rate, Errors, Duration)
    this.httpRequestDuration = new promClient.Histogram({
      name: 'http_request_duration_seconds',
      help: 'Duration of HTTP requests in seconds',
      labelNames: ['method', 'route', 'status_code', 'service', 'environment'],
      buckets: [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
    });

    this.httpRequestTotal = new promClient.Counter({
      name: 'http_requests_total',
      help: 'Total number of HTTP requests',
      labelNames: ['method', 'route', 'status_code', 'service', 'environment']
    });

    this.httpRequestErrors = new promClient.Counter({
      name: 'http_request_errors_total',
      help: 'Total number of HTTP errors',
      labelNames: ['method', 'route', 'error_type', 'service', 'environment']
    });

    // Database metrics
    this.dbQueryDuration = new promClient.Histogram({
      name: 'db_query_duration_seconds',
      help: 'Database query execution time',
      labelNames: ['operation', 'table', 'database', 'status'],
      buckets: [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5]
    });

    this.dbConnectionPool = new promClient.Gauge({
      name: 'db_connection_pool_size',
      help: 'Database connection pool metrics',
      labelNames: ['state', 'database'] // states: active, idle, total
    });

    // Cache metrics
    this.cacheHitRate = new promClient.Counter({
      name: 'cache_operations_total',
      help: 'Cache operation counts',
      labelNames: ['operation', 'cache_name', 'status'] // hit, miss, set, delete
    });

    this.cacheLatency = new promClient.Histogram({
      name: 'cache_operation_duration_seconds',
      help: 'Cache operation latency',
      labelNames: ['operation', 'cache_name'],
      buckets: [0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1]
    });

    // External API metrics
    this.externalApiCalls = new promClient.Histogram({
      name: 'external_api_duration_seconds',
      help: 'External API call duration',
      labelNames: ['service', 'endpoint', 'status_code'],
      buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30]
    });

    // Circuit breaker metrics
    this.circuitBreakerState = new promClient.Gauge({
      name: 'circuit_breaker_state',
      help: 'Circuit breaker state (0=closed, 1=open, 2=half-open)',
      labelNames: ['service']
    });

    // Rate limiting metrics
    this.rateLimitHits = new promClient.Counter({
      name: 'rate_limit_hits_total',
      help: 'Number of rate limited requests',
      labelNames: ['limit_type', 'client_type']
    });

    // WebSocket metrics
    this.activeWebsockets = new promClient.Gauge({
      name: 'websocket_connections_active',
      help: 'Number of active WebSocket connections',
      labelNames: ['namespace', 'room']
    });

    // Register all metrics
    [
      this.httpRequestDuration, this.httpRequestTotal, this.httpRequestErrors,
      this.dbQueryDuration, this.dbConnectionPool, this.cacheHitRate,
      this.cacheLatency, this.externalApiCalls, this.circuitBreakerState,
      this.rateLimitHits, this.activeWebsockets
    ].forEach(metric => this.register.registerMetric(metric));
  }

  initializeBusinessMetrics() {
    // User activity metrics
    this.activeUsers = new promClient.Gauge({
      name: 'business_active_users',
      help: 'Number of active users in the last 5 minutes',
      labelNames: ['user_type', 'plan']
    });

    this.userSignups = new promClient.Counter({
      name: 'business_user_signups_total',
      help: 'Total user signups',
      labelNames: ['source', 'plan', 'country']
    });

    // Transaction metrics
    this.transactionAmount = new promClient.Histogram({
      name: 'business_transaction_amount_dollars',
      help: 'Transaction amounts in dollars',
      labelNames: ['type', 'status', 'payment_method'],
      buckets: [1, 5, 10, 25, 50, 100, 250, 500, 1000, 5000, 10000]
    });

    this.orderProcessingTime = new promClient.Histogram({
      name: 'business_order_processing_seconds',
      help: 'Time to process orders end-to-end',
      labelNames: ['order_type', 'fulfillment_type'],
      buckets: [10, 30, 60, 180, 300, 600, 1800, 3600]
    });

    // API usage metrics
    this.apiUsageByClient = new promClient.Counter({
      name: 'business_api_usage_by_client',
      help: 'API usage segmented by client',
      labelNames: ['client_id', 'tier', 'endpoint']
    });

    this.apiQuotaRemaining = new promClient.Gauge({
      name: 'business_api_quota_remaining',
      help: 'Remaining API quota for clients',
      labelNames: ['client_id', 'tier', 'quota_type']
    });

    // Revenue metrics
    this.revenueByProduct = new promClient.Counter({
      name: 'business_revenue_by_product_cents',
      help: 'Revenue by product in cents',
      labelNames: ['product_id', 'product_category', 'currency']
    });

    // Register business metrics
    [
      this.activeUsers, this.userSignups, this.transactionAmount,
      this.orderProcessingTime, this.apiUsageByClient, this.apiQuotaRemaining,
      this.revenueByProduct
    ].forEach(metric => this.businessRegister.registerMetric(metric));
  }

  initializeCustomCollectors() {
    // SLI/SLO metrics
    this.sloCompliance = new promClient.Gauge({
      name: 'slo_compliance_percentage',
      help: 'SLO compliance percentage',
      labelNames: ['slo_name', 'service', 'window']
    });

    this.errorBudgetRemaining = new promClient.Gauge({
      name: 'error_budget_remaining_percentage',
      help: 'Remaining error budget percentage',
      labelNames: ['service', 'slo_type']
    });

    this.register.registerMetric(this.sloCompliance);
    this.register.registerMetric(this.errorBudgetRemaining);
  }

  startPeriodicCollectors() {
    // Update active users every 30 seconds
    setInterval(() => {
      const activeUserCount = this.calculateActiveUsers();
      this.activeUsers.set(
        { user_type: 'registered', plan: 'free' },
        activeUserCount.free
      );
      this.activeUsers.set(
        { user_type: 'registered', plan: 'premium' },
        activeUserCount.premium
      );
    }, 30000);

    // Update SLO compliance every minute
    setInterval(() => {
      this.updateSLOCompliance();
    }, 60000);

    // Database pool monitoring
    setInterval(() => {
      this.updateDatabasePoolMetrics();
    }, 15000);
  }

  // Middleware for HTTP metrics
  httpMetricsMiddleware() {
    return (req, res, next) => {
      const start = performance.now();
      const route = req.route?.path || req.path || 'unknown';

      // Track in-flight requests
      const inFlightGauge = new promClient.Gauge({
        name: 'http_requests_in_flight',
        help: 'Number of in-flight HTTP requests',
        labelNames: ['method', 'route']
      });

      inFlightGauge.inc({ method: req.method, route });

      res.on('finish', () => {
        const duration = (performance.now() - start) / 1000;
        const labels = {
          method: req.method,
          route,
          status_code: res.statusCode,
          service: process.env.SERVICE_NAME || 'api',
          environment: process.env.NODE_ENV || 'development'
        };

        // Record metrics
        this.httpRequestDuration.observe(labels, duration);
        this.httpRequestTotal.inc(labels);

        if (res.statusCode >= 400) {
          const errorType = res.statusCode >= 500 ? 'server_error' : 'client_error';
          this.httpRequestErrors.inc({
            ...labels,
            error_type: errorType
          });
        }

        inFlightGauge.dec({ method: req.method, route });

        // Log slow requests
        if (duration > 1) {
          console.warn('Slow request detected:', {
            ...labels,
            duration,
            user: req.user?.id,
            ip: req.ip
          });
        }
      });

      next();
    };
  }

  // Database query instrumentation
  instrumentDatabase(knex) {
    knex.on('query', (query) => {
      query.__startTime = performance.now();
    });

    knex.on('query-response', (response, query) => {
      const duration = (performance.now() - query.__startTime) / 1000;
      const table = this.extractTableName(query.sql);

      this.dbQueryDuration.observe({
        operation: query.method || 'select',
        table,
        database: process.env.DB_NAME || 'default',
        status: 'success'
      }, duration);
    });

    knex.on('query-error', (error, query) => {
      const duration = (performance.now() - query.__startTime) / 1000;
      const table = this.extractTableName(query.sql);

      this.dbQueryDuration.observe({
        operation: query.method || 'select',
        table,
        database: process.env.DB_NAME || 'default',
        status: 'error'
      }, duration);
    });
  }

  // Cache instrumentation wrapper
  wrapCache(cache) {
    const wrapper = {};
    const methods = ['get', 'set', 'delete', 'has'];

    methods.forEach(method => {
      wrapper[method] = async (...args) => {
        const start = performance.now();
        const cacheName = cache.name || 'default';

        try {
          const result = await cache[method](...args);
          const duration = (performance.now() - start) / 1000;

          // Record cache metrics
          if (method === 'get') {
            const status = result !== undefined ? 'hit' : 'miss';
            this.cacheHitRate.inc({
              operation: method,
              cache_name: cacheName,
              status
            });
          } else {
            this.cacheHitRate.inc({
              operation: method,
              cache_name: cacheName,
              status: 'success'
            });
          }

          this.cacheLatency.observe({
            operation: method,
            cache_name: cacheName
          }, duration);

          return result;
        } catch (error) {
          this.cacheHitRate.inc({
            operation: method,
            cache_name: cacheName,
            status: 'error'
          });
          throw error;
        }
      };
    });

    return wrapper;
  }

  // External API call instrumentation
  async trackExternalCall(serviceName, endpoint, callFunc) {
    const start = performance.now();

    try {
      const result = await callFunc();
      const duration = (performance.now() - start) / 1000;

      this.externalApiCalls.observe({
        service: serviceName,
        endpoint,
        status_code: result.status || 200
      }, duration);

      return result;
    } catch (error) {
      const duration = (performance.now() - start) / 1000;

      this.externalApiCalls.observe({
        service: serviceName,
        endpoint,
        status_code: error.response?.status || 0
      }, duration);

      throw error;
    }
  }

  // Circuit breaker monitoring
  updateCircuitBreakerState(service, state) {
    const stateValue = {
      'closed': 0,
      'open': 1,
      'half-open': 2
    }[state] || 0;

    this.circuitBreakerState.set({ service }, stateValue);
  }

  // Helper methods
  calculateActiveUsers() {
    // Implementation would query your session store or database
    return {
      free: Math.floor(Math.random() * 1000),
      premium: Math.floor(Math.random() * 100)
    };
  }

  updateSLOCompliance() {
    // Calculate based on recent metrics
    const availability = 99.95; // Calculate from actual metrics
    const latencyP99 = 250; // Calculate from actual metrics

    this.sloCompliance.set({
      slo_name: 'availability',
      service: 'api',
      window: '30d'
    }, availability);

    this.sloCompliance.set({
      slo_name: 'latency_p99',
      service: 'api',
      window: '30d'
    }, latencyP99 < 500 ? 100 : 0);

    // Update error budget
    const errorBudget = 100 - ((100 - availability) / 0.05) * 100;
    this.errorBudgetRemaining.set({
      service: 'api',
      slo_type: 'availability'
    }, Math.max(0, errorBudget));
  }

  updateDatabasePoolMetrics() {
    // Get pool stats from your database driver
    const pool = global.dbPool; // Your database pool instance
    if (pool) {
      this.dbConnectionPool.set({
        state: 'active',
        database: 'primary'
      }, pool.numUsed());

      this.dbConnectionPool.set({
        state: 'idle',
        database: 'primary'
      }, pool.numFree());

      this.dbConnectionPool.set({
        state: 'total',
        database: 'primary'
      }, pool.numUsed() + pool.numFree());
    }
  }

  extractTableName(sql) {
    const match = sql.match(/(?:from|into|update)\s+`?(\w+)`?/i);
    return match ? match[1] : 'unknown';
  }

  // Expose metrics endpoint
  async getMetrics() {
    const baseMetrics = await this.register.metrics();
    const businessMetrics = await this.businessRegister.metrics();
    return baseMetrics + '\n' + businessMetrics;
  }
}

// Express application setup
const express = require('express');
const app = express();
const metricsCollector = new MetricsCollector();

// Apply monitoring middleware
app.use(metricsCollector.httpMetricsMiddleware());

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', metricsCollector.register.contentType);
  res.end(await metricsCollector.getMetrics());
});

// Example API endpoint with comprehensive tracking
app.post('/api/orders', async (req, res) => {
  const orderStart = performance.now();

  try {
    // Track business metrics
    metricsCollector.transactionAmount.observe({
      type: 'purchase',
      status: 'pending',
      payment_method: req.body.paymentMethod
    }, req.body.amount);

    // Simulate external payment API call
    const paymentResult = await metricsCollector.trackExternalCall(
      'stripe',
      '/charges',
      async () => {
        // Your actual payment API call
        return await stripeClient.charges.create({
          amount: req.body.amount * 100,
          currency: 'usd'
        });
      }
    );

    // Track order processing time
    const processingTime = (performance.now() - orderStart) / 1000;
    metricsCollector.orderProcessingTime.observe({
      order_type: 'standard',
      fulfillment_type: 'digital'
    }, processingTime);

    // Track revenue
    metricsCollector.revenueByProduct.inc({
      product_id: req.body.productId,
      product_category: req.body.category,
      currency: 'USD'
    }, req.body.amount * 100);

    res.json({ success: true, orderId: paymentResult.id });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = { app, metricsCollector };
```

### Example 2: Complete Monitoring Stack with Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerting-rules.yml:/etc/prometheus/alerting-rules.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--storage.tsdb.retention.time=15d'
    ports:
      - "9090:9090"
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:10.0.0
    container_name: grafana
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana-dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=http://localhost:3000
    ports:
      - "3000:3000"
    networks:
      - monitoring
    depends_on:
      - prometheus

  jaeger:
    image: jaegertracing/all-in-one:1.47
    container_name: jaeger
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "5775:5775/udp"
      - "6831:6831/udp"
      - "6832:6832/udp"
      - "5778:5778"
      - "16686:16686"  # Jaeger UI
      - "14268:14268"
      - "14250:14250"
      - "9411:9411"
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:v0.26.0
    container_name: alertmanager
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    ports:
      - "9093:9093"
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus-data:
  grafana-data:
```

### Example 3: Advanced Grafana Dashboard Definitions

```json
// grafana-dashboards/api-overview.json
{
  "dashboard": {
    "id": null,
    "uid": "api-overview",
    "title": "API Performance Overview",
    "tags": ["api", "performance", "sre"],
    "timezone": "browser",
    "schemaVersion": 16,
    "version": 0,
    "refresh": "30s",
    "time": {
      "from": "now-6h",
      "to": "now"
    },
    "templating": {
      "list": [
        {
          "name": "datasource",
          "type": "datasource",
          "query": "prometheus",
          "current": {
            "value": "Prometheus",
            "text": "Prometheus"
          }
        },
        {
          "name": "service",
          "type": "query",
          "datasource": "$datasource",
          "query": "label_values(http_requests_total, service)",
          "multi": true,
          "includeAll": true,
          "current": {
            "value": ["$__all"],
            "text": "All"
          },
          "refresh": 1
        },
        {
          "name": "environment",
          "type": "query",
          "datasource": "$datasource",
          "query": "label_values(http_requests_total, environment)",
          "current": {
            "value": "production",
            "text": "Production"
          }
        }
      ]
    },
    "panels": [
      {
        "id": 1,
        "gridPos": { "h": 8, "w": 8, "x": 0, "y": 0 },
        "type": "graph",
        "title": "Request Rate (req/s)",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{service=~\"$service\",environment=\"$environment\"}[5m])) by (service)",
            "legendFormat": "{{service}}",
            "refId": "A"
          }
        ],
        "yaxes": [
          {
            "format": "reqps",
            "label": "Requests per second"
          }
        ],
        "lines": true,
        "linewidth": 2,
        "fill": 1,
        "fillGradient": 3,
        "steppedLine": false,
        "tooltip": {
          "shared": true,
          "sort": 0,
          "value_type": "individual"
        },
        "alert": {
          "name": "High Request Rate",
          "conditions": [
            {
              "evaluator": {
                "params": [10000],
                "type": "gt"
              },
              "operator": {
                "type": "and"
              },
              "query": {
                "params": ["A", "5m", "now"]
              },
              "reducer": {
                "type": "avg"
              },
              "type": "query"
            }
          ],
          "executionErrorState": "alerting",
          "frequency": "1m",
          "handler": 1,
          "noDataState": "no_data",
          "notifications": [
            {
              "uid": "slack-channel"
            }
          ]
        }
      },
      {
        "id": 2,
        "gridPos": { "h": 8, "w": 8, "x": 8, "y": 0 },
        "type": "graph",
        "title": "Error Rate (%)",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{service=~\"$service\",environment=\"$environment\",status_code=~\"5..\"}[5m])) by (service) / sum(rate(http_requests_total{service=~\"$service\",environment=\"$environment\"}[5m])) by (service) * 100",
            "legendFormat": "{{service}}",
            "refId": "A"
          }
        ],
        "yaxes": [
          {
            "format": "percent",
            "label": "Error Rate",
            "max": 10
          }
        ],
        "thresholds": [
          {
            "value": 1,
            "op": "gt",
            "fill": true,
            "line": true,
            "colorMode": "critical"
          }
        ],
        "alert": {
          "name": "High Error Rate",
          "conditions": [
            {
              "evaluator": {
                "params": [1],
                "type": "gt"
              },
              "operator": {
                "type": "and"
              },
              "query": {
                "params": ["A", "5m", "now"]
              },
              "reducer": {
                "type": "last"
              },
              "type": "query"
            }
          ],
          "executionErrorState": "alerting",
          "frequency": "1m",
          "handler": 1,
          "noDataState": "no_data",
          "notifications": [
            {
              "uid": "pagerduty"
            }
          ],
          "message": "Error rate is above 1% for service {{service}}"
        }
      },
      {
        "id": 3,
        "gridPos": { "h": 8, "w": 8, "x": 16, "y": 0 },
        "type": "graph",
        "title": "Response Time (p50, p95, p99)",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{service=~\"$service\",environment=\"$environment\"}[5m])) by (le, service))",
            "legendFormat": "p50 {{service}}",
            "refId": "A"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{service=~\"$service\",environment=\"$environment\"}[5m])) by (le, service))",
            "legendFormat": "p95 {{service}}",
            "refId": "B"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{service=~\"$service\",environment=\"$environment\"}[5m])) by (le, service))",
            "legendFormat": "p99 {{service}}",
            "refId": "C"
          }
        ],
        "yaxes": [
          {
            "format": "s",
            "label": "Response Time"
          }
        ]
      },
      {
        "id": 4,
        "gridPos": { "h": 6, "w": 6, "x": 0, "y": 8 },
        "type": "stat",
        "title": "Current QPS",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{service=~\"$service\",environment=\"$environment\"}[1m]))",
            "instant": true,
            "refId": "A"
          }
        ],
        "format": "reqps",
        "sparkline": {
          "show": true,
          "lineColor": "rgb(31, 120, 193)",
          "fillColor": "rgba(31, 120, 193, 0.18)"
        },
        "thresholds": {
          "mode": "absolute",
          "steps": [
            { "value": 0, "color": "green" },
            { "value": 5000, "color": "yellow" },
            { "value": 10000, "color": "red" }
          ]
        }
      },
      {
        "id": 5,
        "gridPos": { "h": 6, "w": 6, "x": 6, "y": 8 },
        "type": "stat",
        "title": "Error Budget Remaining",
        "targets": [
          {
            "expr": "error_budget_remaining_percentage{service=~\"$service\",slo_type=\"availability\"}",
            "instant": true,
            "refId": "A"
          }
        ],
        "format": "percent",
        "thresholds": {
          "mode": "absolute",
          "steps": [
            { "value": 0, "color": "red" },
            { "value": 25, "color": "orange" },
            { "value": 50, "color": "yellow" },
            { "value": 75, "color": "green" }
          ]
        }
      },
      {
        "id": 6,
        "gridPos": { "h": 6, "w": 12, "x": 12, "y": 8 },
        "type": "table",
        "title": "Top Slow Endpoints",
        "targets": [
          {
            "expr": "topk(10, histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{service=~\"$service\",environment=\"$environment\"}[5m])) by (le, route)))",
            "format": "table",
            "instant": true,
            "refId": "A"
          }
        ],
        "styles": [
          {
            "alias": "Time",
            "dateFormat": "YYYY-MM-DD HH:mm:ss",
            "type": "date"
          },
          {
            "alias": "Duration",
            "colorMode": "cell",
            "colors": ["green", "yellow", "red"],
            "thresholds": [0.5, 1],
            "type": "number",
            "unit": "s"
          }
        ]
      }
    ]
  }
}
```

### Example 4: Production-Ready Alerting Rules

```yaml
# alerting-rules.yml
groups:
  - name: api_alerts
    interval: 30s
    rules:
      # SLO-based alerts
      - alert: APIHighErrorRate
        expr: |
          (
            sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (service, environment)
            /
            sum(rate(http_requests_total[5m])) by (service, environment)
          ) > 0.01
        for: 5m
        labels:
          severity: critical
          team: api-platform
        annotations:
          summary: "High error rate on {{ $labels.service }}"
          description: "{{ $labels.service }} in {{ $labels.environment }} has error rate of {{ $value | humanizePercentage }} (threshold: 1%)"
          runbook_url: "https://wiki.example.com/runbooks/api-high-error-rate"
          dashboard_url: "https://grafana.example.com/d/api-overview?var-service={{ $labels.service }}"

      - alert: APIHighLatency
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (service, le)
          ) > 0.5
        for: 10m
        labels:
          severity: warning
          team: api-platform
        annotations:
          summary: "High latency on {{ $labels.service }}"
          description: "P95 latency for {{ $labels.service }} is {{ $value | humanizeDuration }} (threshold: 500ms)"

      - alert: APILowAvailability
        expr: |
          up{job="api-services"} == 0
        for: 1m
        labels:
          severity: critical
          team: api-platform
        annotations:
          summary: "API service {{ $labels.instance }} is down"
          description: "{{ $labels.instance }} has been down for more than 1 minute"

      # Business metrics alerts
      - alert: LowActiveUsers
        expr: |
          business_active_users{plan="premium"} < 10
        for: 30m
        labels:
          severity: warning
          team: product
        annotations:
          summary: "Low number of active premium users"
          description: "Only {{ $value }} premium users active in the last 30 minutes"

      - alert: HighTransactionFailureRate
        expr: |
          (
            sum(rate(business_transaction_amount_dollars_sum{status="failed"}[5m]))
            /
            sum(rate(business_transaction_amount_dollars_sum[5m]))
          ) > 0.05
        for: 5m
        labels:
          severity: critical
          team: payments
        annotations:
          summary: "High transaction failure rate"
          description: "Transaction failure rate is {{ $value | humanizePercentage }} (threshold: 5%)"

      # Infrastructure alerts
      - alert: DatabaseConnectionPoolExhausted
        expr: |
          (
            db_connection_pool_size{state="active"}
            /
            db_connection_pool_size{state="total"}
          ) > 0.9
        for: 5m
        labels:
          severity: warning
          team: database
        annotations:
          summary: "Database connection pool near exhaustion"
          description: "{{ $labels.database }} pool is {{ $value | humanizePercentage }} utilized"

      - alert: CacheLowHitRate
        expr: |
          (
            sum(rate(cache_operations_total{status="hit"}[5m])) by (cache_name)
            /
            sum(rate(cache_operations_total{operation="get"}[5m])) by (cache_name)
          ) < 0.8
        for: 15m
        labels:
          severity: warning
          team: api-platform
        annotations:
          summary: "Low cache hit rate for {{ $labels.cache_name }}"
          description: "Cache hit rate is {{ $value | humanizePercentage }} (expected: >80%)"

      - alert: CircuitBreakerOpen
        expr: |
          circuit_breaker_state == 1
        for: 1m
        labels:
          severity: warning
          team: api-platform
        annotations:
          summary: "Circuit breaker open for {{ $labels.service }}"
          description: "Circuit breaker for {{ $labels.service }} has been open for more than 1 minute"

      # SLO burn rate alerts (multi-window approach)
      - alert: SLOBurnRateHigh
        expr: |
          (
            # 5m burn rate > 14.4 (1 hour of error budget in 5 minutes)
            (
              sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (service)
              /
              sum(rate(http_requests_total[5m])) by (service)
            ) > (1 - 0.999) * 14.4
          ) and (
            # 1h burn rate > 1 (confirms it's not a spike)
            (
              sum(rate(http_requests_total{status_code=~"5.."}[1h])) by (service)
              /
              sum(rate(http_requests_total[1h])) by (service)
            ) > (1 - 0.999)
          )
        labels:
          severity: critical
          team: api-platform
          alert_type: slo_burn
        annotations:
          summary: "SLO burn rate critically high for {{ $labels.service }}"
          description: "{{ $labels.service }} is burning error budget 14.4x faster than normal"

      # Resource alerts
      - alert: HighMemoryUsage
        expr: |
          (
            container_memory_usage_bytes{container!="POD",container!=""}
            /
            container_spec_memory_limit_bytes{container!="POD",container!=""}
          ) > 0.9
        for: 5m
        labels:
          severity: warning
          team: api-platform
        annotations:
          summary: "High memory usage for {{ $labels.container }}"
          description: "Container {{ $labels.container }} memory usage is {{ $value | humanizePercentage }}"

# AlertManager configuration
# alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: 'YOUR_SLACK_WEBHOOK_URL'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      continue: true
    - match:
        severity: warning
      receiver: 'slack-warnings'
    - match:
        team: payments
      receiver: 'payments-team'

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
        description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
        details:
          firing: '{{ .Alerts.Firing | len }}'
          resolved: '{{ .Alerts.Resolved | len }}'
          labels: '{{ .CommonLabels }}'

  - name: 'slack-warnings'
    slack_configs:
      - channel: '#warnings'
        send_resolved: true
        title: 'Warning: {{ .GroupLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'
        actions:
          - type: button
            text: 'View Dashboard'
            url: '{{ .CommonAnnotations.dashboard_url }}'
          - type: button
            text: 'View Runbook'
            url: '{{ .CommonAnnotations.runbook_url }}'

  - name: 'payments-team'
    email_configs:
      - to: 'payments-team@example.com'
        from: 'alerts@example.com'
        headers:
          Subject: 'Payment Alert: {{ .GroupLabels.alertname }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'service']
```

### Example 5: OpenTelemetry Integration for Distributed Tracing

```javascript
// tracing/setup.js - OpenTelemetry configuration
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { JaegerExporter } = require('@opentelemetry/exporter-jaeger');
const { PrometheusExporter } = require('@opentelemetry/exporter-prometheus');
const {
  ConsoleSpanExporter,
  BatchSpanProcessor,
  SimpleSpanProcessor
} = require('@opentelemetry/sdk-trace-base');
const { PeriodicExportingMetricReader } = require('@opentelemetry/sdk-metrics');

class TracingSetup {
  constructor(serviceName, environment = 'production') {
    this.serviceName = serviceName;
    this.environment = environment;
    this.sdk = null;
  }

  initialize() {
    // Create resource identifying the service
    const resource = Resource.default().merge(
      new Resource({
        [SemanticResourceAttributes.SERVICE_NAME]: this.serviceName,
        [SemanticResourceAttributes.SERVICE_VERSION]: process.env.VERSION || '1.0.0',
        [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: this.environment,
        'service.namespace': 'api-platform',
        'service.instance.id': process.env.HOSTNAME || 'unknown',
        'telemetry.sdk.language': 'nodejs',
      })
    );

    // Configure Jaeger exporter for traces
    const jaegerExporter = new JaegerExporter({
      endpoint: process.env.JAEGER_ENDPOINT || 'http://localhost:14268/api/traces',
      tags: {
        service: this.serviceName,
        environment: this.environment
      }
    });

    // Configure Prometheus exporter for metrics
    const prometheusExporter = new PrometheusExporter({
      port: 9464,
      endpoint: '/metrics',
      prefix: 'otel_',
      appendTimestamp: true,
    }, () => {
      console.log('Prometheus metrics server started on port 9464');
    });

    // Create SDK with auto-instrumentation
    this.sdk = new NodeSDK({
      resource,
      instrumentations: [
        getNodeAutoInstrumentations({
          '@opentelemetry/instrumentation-fs': {
            enabled: false, // Disable fs to reduce noise
          },
          '@opentelemetry/instrumentation-http': {
            requestHook: (span, request) => {
              span.setAttribute('http.request.body', JSON.stringify(request.body));
              span.setAttribute('http.request.user_id', request.user?.id);
            },
            responseHook: (span, response) => {
              span.setAttribute('http.response.size', response.length);
            },
            ignoreIncomingPaths: ['/health', '/metrics', '/favicon.ico'],
            ignoreOutgoingUrls: [(url) => url.includes('prometheus')]
          },
          '@opentelemetry/instrumentation-express': {
            requestHook: (span, request) => {
              span.setAttribute('express.route', request.route?.path);
              span.setAttribute('express.params', JSON.stringify(request.params));
            }
          },
          '@opentelemetry/instrumentation-mysql2': {
            enhancedDatabaseReporting: true,
          },
          '@opentelemetry/instrumentation-redis-4': {
            dbStatementSerializer: (cmdName, cmdArgs) => {
              return `${cmdName} ${cmdArgs.slice(0, 2).join(' ')}`;
            }
          }
        })
      ],
      spanProcessor: new BatchSpanProcessor(jaegerExporter, {
        maxQueueSize: 2048,
        maxExportBatchSize: 512,
        scheduledDelayMillis: 5000,
        exportTimeoutMillis: 30000,
      }),
      metricReader: new PeriodicExportingMetricReader({
        exporter: prometheusExporter,
        exportIntervalMillis: 10000,
      }),
    });

    // Start the SDK
    this.sdk.start()
      .then(() => console.log('Tracing initialized successfully'))
      .catch((error) => console.error('Error initializing tracing', error));

    // Graceful shutdown
    process.on('SIGTERM', () => {
      this.shutdown();
    });
  }

  async shutdown() {
    try {
      await this.sdk.shutdown();
      console.log('Tracing terminated successfully');
    } catch (error) {
      console.error('Error terminating tracing', error);
    }
  }

  // Manual span creation for custom instrumentation
  createSpan(tracer, spanName, fn) {
    return tracer.startActiveSpan(spanName, async (span) => {
      try {
        span.setAttribute('span.kind', 'internal');
        span.setAttribute('custom.span', true);

        const result = await fn(span);

        span.setStatus({ code: 0, message: 'OK' });
        return result;
      } catch (error) {
        span.setStatus({ code: 2, message: error.message });
        span.recordException(error);
        throw error;
      } finally {
        span.end();
      }
    });
  }
}

// Usage in application
const tracing = new TracingSetup('api-gateway', process.env.NODE_ENV);
tracing.initialize();

// Custom instrumentation example
const { trace } = require('@opentelemetry/api');

async function processOrder(orderId) {
  const tracer = trace.getTracer('order-processing', '1.0.0');

  return tracing.createSpan(tracer, 'processOrder', async (span) => {
    span.setAttribute('order.id', orderId);
    span.addEvent('Order processing started');

    // Validate order
    await tracing.createSpan(tracer, 'validateOrder', async (childSpan) => {
      childSpan.setAttribute('validation.type', 'schema');
      // Validation logic
      await validateOrderSchema(orderId);
    });

    // Process payment
    await tracing.createSpan(tracer, 'processPayment', async (childSpan) => {
      childSpan.setAttribute('payment.method', 'stripe');
      // Payment logic
      const result = await processStripePayment(orderId);
      childSpan.setAttribute('payment.status', result.status);
      childSpan.addEvent('Payment processed', {
        'payment.amount': result.amount,
        'payment.currency': result.currency
      });
    });

    // Send confirmation
    await tracing.createSpan(tracer, 'sendConfirmation', async (childSpan) => {
      childSpan.setAttribute('notification.type', 'email');
      // Email logic
      await sendOrderConfirmation(orderId);
    });

    span.addEvent('Order processing completed');
    return { success: true, orderId };
  });
}

module.exports = { TracingSetup, tracing };
```

### Example 6: Custom Prometheus Exporters for Complex Metrics

```python
# custom_exporters.py - Python Prometheus exporter for business metrics
from prometheus_client import start_http_server, Gauge, Counter, Histogram, Info, Enum
from prometheus_client.core import CollectorRegistry
from prometheus_client import generate_latest
import time
import psycopg2
import redis
import requests
from datetime import datetime, timedelta
import asyncio
import aiohttp

class CustomBusinessExporter:
    def __init__(self, db_config, redis_config, port=9091):
        self.registry = CollectorRegistry()
        self.db_config = db_config
        self.redis_config = redis_config
        self.port = port

        # Initialize metrics
        self.initialize_metrics()

        # Connect to data sources
        self.connect_datasources()

    def initialize_metrics(self):
        # Business KPI metrics
        self.revenue_total = Gauge(
            'business_revenue_total_usd',
            'Total revenue in USD',
            ['period', 'product_line', 'region'],
            registry=self.registry
        )

        self.customer_lifetime_value = Histogram(
            'business_customer_lifetime_value_usd',
            'Customer lifetime value distribution',
            ['customer_segment', 'acquisition_channel'],
            buckets=(10, 50, 100, 500, 1000, 5000, 10000, 50000),
            registry=self.registry
        )

        self.churn_rate = Gauge(
            'business_churn_rate_percentage',
            'Customer churn rate',
            ['plan', 'cohort'],
            registry=self.registry
        )

        self.monthly_recurring_revenue = Gauge(
            'business_mrr_usd',
            'Monthly recurring revenue',
            ['plan', 'currency'],
            registry=self.registry
        )

        self.net_promoter_score = Gauge(
            'business_nps',
            'Net Promoter Score',
            ['segment', 'survey_type'],
            registry=self.registry
        )

        # Operational metrics
        self.data_pipeline_lag = Histogram(
            'data_pipeline_lag_seconds',
            'Data pipeline processing lag',
            ['pipeline', 'stage'],
            buckets=(1, 5, 10, 30, 60, 300, 600, 1800, 3600),
            registry=self.registry
        )

        self.feature_usage = Counter(
            'feature_usage_total',
            'Feature usage counts',
            ['feature_name', 'user_tier', 'success'],
            registry=self.registry
        )

        self.api_quota_usage = Gauge(
            'api_quota_usage_percentage',
            'API quota usage by customer',
            ['customer_id', 'tier', 'resource'],
            registry=self.registry
        )

        # System health indicators
        self.dependency_health = Enum(
            'dependency_health_status',
            'Health status of external dependencies',
            ['service', 'dependency'],
            states=['healthy', 'degraded', 'unhealthy'],
            registry=self.registry
        )

        self.data_quality_score = Gauge(
            'data_quality_score',
            'Data quality score (0-100)',
            ['dataset', 'dimension'],
            registry=self.registry
        )

    def connect_datasources(self):
        # PostgreSQL connection
        self.db_conn = psycopg2.connect(**self.db_config)

        # Redis connection
        self.redis_client = redis.Redis(**self.redis_config)

    def collect_business_metrics(self):
        """Collect business metrics from various data sources"""
        cursor = self.db_conn.cursor()

        # Revenue metrics
        cursor.execute("""
            SELECT
                DATE_TRUNC('day', created_at) as period,
                product_line,
                region,
                SUM(amount) as total_revenue
            FROM orders
            WHERE status = 'completed'
                AND created_at >= NOW() - INTERVAL '7 days'
            GROUP BY period, product_line, region
        """)

        for row in cursor.fetchall():
            self.revenue_total.labels(
                period=row[0].isoformat(),
                product_line=row[1],
                region=row[2]
            ).set(row[3])

        # Customer lifetime value
        cursor.execute("""
            SELECT
                c.segment,
                c.acquisition_channel,
                AVG(o.total_spent) as avg_clv
            FROM customers c
            JOIN (
                SELECT customer_id, SUM(amount) as total_spent
                FROM orders
                WHERE status = 'completed'
                GROUP BY customer_id
            ) o ON c.id = o.customer_id
            GROUP BY c.segment, c.acquisition_channel
        """)

        for row in cursor.fetchall():
            self.customer_lifetime_value.labels(
                customer_segment=row[0],
                acquisition_channel=row[1]
            ).observe(row[2])

        # MRR calculation
        cursor.execute("""
            SELECT
                plan_name,
                currency,
                SUM(
                    CASE
                        WHEN billing_period = 'yearly' THEN amount / 12
                        ELSE amount
                    END
                ) as mrr
            FROM subscriptions
            WHERE status = 'active'
            GROUP BY plan_name, currency
        """)

        for row in cursor.fetchall():
            self.monthly_recurring_revenue.labels(
                plan=row[0],
                currency=row[1]
            ).set(row[2])

        # Churn rate
        cursor.execute("""
            WITH cohort_data AS (
                SELECT
                    plan_name,
                    DATE_TRUNC('month', created_at) as cohort,
                    COUNT(*) as total_customers,
                    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as churned_customers
                FROM subscriptions
                WHERE created_at >= NOW() - INTERVAL '6 months'
                GROUP BY plan_name, cohort
            )
            SELECT
                plan_name,
                cohort,
                (churned_customers::float / total_customers) * 100 as churn_rate
            FROM cohort_data
        """)

        for row in cursor.fetchall():
            self.churn_rate.labels(
                plan=row[0],
                cohort=row[1].isoformat()
            ).set(row[2])

        cursor.close()

    def collect_operational_metrics(self):
        """Collect operational metrics from Redis and other sources"""

        # API quota usage from Redis
        for key in self.redis_client.scan_iter("quota:*"):
            parts = key.decode().split(':')
            if len(parts) >= 3:
                customer_id = parts[1]
                resource = parts[2]

                used = float(self.redis_client.get(key) or 0)
                limit_key = f"quota_limit:{customer_id}:{resource}"
                limit = float(self.redis_client.get(limit_key) or 1000)

                usage_percentage = (used / limit) * 100 if limit > 0 else 0

                # Get customer tier from database
                cursor = self.db_conn.cursor()
                cursor.execute(
                    "SELECT tier FROM customers WHERE id = %s",
                    (customer_id,)
                )
                result = cursor.fetchone()
                tier = result[0] if result else 'unknown'
                cursor.close()

                self.api_quota_usage.labels(
                    customer_id=customer_id,
                    tier=tier,
                    resource=resource
                ).set(usage_percentage)

        # Data pipeline lag from Redis
        pipeline_stages = ['ingestion', 'processing', 'storage', 'delivery']
        for stage in pipeline_stages:
            lag_key = f"pipeline:lag:{stage}"
            lag_value = self.redis_client.get(lag_key)
            if lag_value:
                self.data_pipeline_lag.labels(
                    pipeline='main',
                    stage=stage
                ).observe(float(lag_value))

    def check_dependency_health(self):
        """Check health of external dependencies"""
        dependencies = [
            ('payment', 'stripe', 'https://api.stripe.com/health'),
            ('email', 'sendgrid', 'https://api.sendgrid.com/health'),
            ('storage', 's3', 'https://s3.amazonaws.com/health'),
            ('cache', 'redis', 'redis://localhost:6379'),
            ('database', 'postgres', self.db_config)
        ]

        for service, dep_name, endpoint in dependencies:
            try:
                if dep_name == 'redis':
                    # Check Redis
                    self.redis_client.ping()
                    status = 'healthy'
                elif dep_name == 'postgres':
                    # Check PostgreSQL
                    cursor = self.db_conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    status = 'healthy'
                else:
                    # Check HTTP endpoints
                    response = requests.get(endpoint, timeout=5)
                    if response.status_code == 200:
                        status = 'healthy'
                    elif 200 < response.status_code < 500:
                        status = 'degraded'
                    else:
                        status = 'unhealthy'
            except Exception as e:
                print(f"Health check failed for {dep_name}: {e}")
                status = 'unhealthy'

            self.dependency_health.labels(
                service=service,
                dependency=dep_name
            ).state(status)

    def calculate_data_quality(self):
        """Calculate data quality scores"""
        cursor = self.db_conn.cursor()

        # Completeness score
        cursor.execute("""
            SELECT
                'orders' as dataset,
                (COUNT(*) - COUNT(CASE WHEN customer_email IS NULL THEN 1 END))::float / COUNT(*) * 100 as completeness
            FROM orders
            WHERE created_at >= NOW() - INTERVAL '1 day'
        """)

        for row in cursor.fetchall():
            self.data_quality_score.labels(
                dataset=row[0],
                dimension='completeness'
            ).set(row[1])

        # Accuracy score (checking for valid email formats)
        cursor.execute("""
            SELECT
                'customers' as dataset,
                COUNT(CASE WHEN email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$' THEN 1 END)::float / COUNT(*) * 100 as accuracy
            FROM customers
            WHERE created_at >= NOW() - INTERVAL '1 day'
        """)

        for row in cursor.fetchall():
            self.data_quality_score.labels(
                dataset=row[0],
                dimension='accuracy'
            ).set(row[1])

        cursor.close()

    async def collect_metrics_async(self):
        """Async collection for improved performance"""
        tasks = [
            self.collect_business_metrics_async(),
            self.collect_operational_metrics_async(),
            self.check_dependency_health_async(),
            self.calculate_data_quality_async()
        ]

        await asyncio.gather(*tasks)

    def run(self):
        """Start the exporter"""
        # Start HTTP server for Prometheus to scrape
        start_http_server(self.port, registry=self.registry)
        print(f"Custom exporter started on port {self.port}")

        # Collect metrics every 30 seconds
        while True:
            try:
                self.collect_business_metrics()
                self.collect_operational_metrics()
                self.check_dependency_health()
                self.calculate_data_quality()

                print(f"Metrics collected at {datetime.now()}")
                time.sleep(30)

            except Exception as e:
                print(f"Error collecting metrics: {e}")
                time.sleep(30)

# Usage
if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'database': 'production',
        'user': 'metrics_user',
        'password': 'secure_password',
        'port': 5432
    }

    redis_config = {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'decode_responses': True
    }

    exporter = CustomBusinessExporter(db_config, redis_config)
    exporter.run()
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Connection refused to Prometheus" | Prometheus not running or wrong port | Check Docker container status with `docker ps`, verify port mapping |
| "No data in Grafana dashboard" | Metrics not being scraped | Verify Prometheus targets at `localhost:9090/targets`, check API metrics endpoint |
| "Too many samples" error | High cardinality labels | Review label usage, avoid user IDs or timestamps as labels |
| "Out of memory" in Prometheus | Retention too long or too many metrics | Reduce retention time, implement remote storage, or scale vertically |
| Jaeger traces not appearing | Incorrect sampling rate | Increase sampling rate in tracer configuration |
| "Context deadline exceeded" | Scrape timeout too short | Increase scrape_timeout in prometheus.yml (default 10s) |
| "Error reading Prometheus" | Corrupt WAL (write-ahead log) | Delete WAL directory: `rm -rf /prometheus/wal/*` and restart |
| "Too many open files" | File descriptor limit reached | Increase ulimit: `ulimit -n 65536` or adjust systemd limits |
| AlertManager not firing | Incorrect routing rules | Validate routing tree with `amtool config routes` |
| Grafana login loop | Cookie/session issues | Clear browser cookies, check Grafana cookie settings |

## Configuration Options

**Basic Usage:**
```bash
/create-monitoring \
  --stack=prometheus \
  --services=api-gateway,user-service,order-service \
  --environment=production \
  --retention=30d
```

**Available Options:**

`--stack <type>` - Monitoring stack to deploy
- `prometheus` - Prometheus + Grafana + AlertManager (default, open-source)
- `elastic` - ELK stack (Elasticsearch, Logstash, Kibana) for log-centric
- `datadog` - Datadog agent configuration (requires API key)
- `newrelic` - New Relic agent setup (requires license key)
- `hybrid` - Combination of metrics (Prometheus) and logs (ELK)

`--tracing <backend>` - Distributed tracing backend
- `jaeger` - Jaeger all-in-one (default, recommended for start)
- `zipkin` - Zipkin server
- `tempo` - Grafana Tempo (for high-scale)
- `xray` - AWS X-Ray (for AWS environments)
- `none` - Skip tracing setup

`--retention <duration>` - Metrics retention period
- Default: `15d` (15 days)
- Production: `30d` to `90d`
- With remote storage: `365d` or more

`--scrape-interval <duration>` - How often to collect metrics
- Default: `15s`
- High-frequency: `5s` (higher resource usage)
- Low-frequency: `60s` (for stable metrics)

`--alerting-channels <channels>` - Where to send alerts
- `slack` - Slack webhook integration
- `pagerduty` - PagerDuty integration
- `email` - SMTP email notifications
- `webhook` - Custom webhook endpoint
- `opsgenie` - Atlassian OpsGenie

`--dashboard-presets <presets>` - Pre-built dashboards to install
- `red-metrics` - Rate, Errors, Duration
- `four-golden` - Latency, Traffic, Errors, Saturation
- `business-kpis` - Revenue, Users, Conversion
- `sre-slos` - SLI/SLO tracking
- `security` - Security metrics and anomalies

`--exporters <list>` - Additional exporters to configure
- `node-exporter` - System/host metrics
- `blackbox-exporter` - Probe endpoints
- `postgres-exporter` - PostgreSQL metrics
- `redis-exporter` - Redis metrics
- `custom` - Custom business metrics

`--high-availability` - Enable HA configuration
- Sets up Prometheus federation
- Configures AlertManager clustering
- Enables Grafana database replication

`--storage <type>` - Long-term storage backend
- `local` - Local disk (default)
- `thanos` - Thanos for unlimited retention
- `cortex` - Cortex for multi-tenant
- `victoria` - VictoriaMetrics for efficiency
- `s3` - S3-compatible object storage

`--dry-run` - Generate configuration without deploying
- Creates all config files
- Validates syntax
- Shows what would be deployed
- No actual containers started

## Best Practices

DO:
- Start with RED metrics (Rate, Errors, Duration) as your foundation
- Use histogram buckets that align with your SLO targets
- Tag metrics with environment, region, version, and service
- Create runbooks for every alert and link them in annotations
- Implement meta-monitoring (monitor the monitoring system)
- Use recording rules for frequently-run expensive queries
- Set up separate dashboards for different audiences (ops, dev, business)
- Use exemplars to link metrics to traces for easier debugging
- Implement gradual rollout of new metrics to avoid cardinality explosion
- Archive old dashboards before creating new ones

DON'T:
- Add high-cardinality labels like user IDs, session IDs, or UUIDs
- Create dashboards with 50+ panels (causes browser performance issues)
- Alert on symptoms without providing actionable runbooks
- Store raw logs in Prometheus (use log aggregation systems)
- Ignore alert fatigue (regularly review and tune thresholds)
- Hardcode datasource UIDs in dashboard JSON
- Mix metrics from different time ranges in one panel
- Use regex selectors without limits in production queries
- Forget to set up backup for Grafana database
- Skip capacity planning for metrics growth

TIPS:
- Import dashboards from grafana.com marketplace (dashboard IDs)
- Use Prometheus federation for multi-region deployments
- Implement progressive alerting: warning (Slack) → critical (PagerDuty)
- Create team-specific folders in Grafana for organization
- Use Grafana variables for dynamic, reusable dashboards
- Set up dashboard playlists for NOC/SOC displays
- Use annotations to mark deployments and incidents on graphs
- Implement SLO burn rate alerts instead of static thresholds
- Create separate Prometheus jobs for different scrape intervals
- Use remote_write for backup and long-term storage

## Performance Considerations

**Prometheus Resource Planning**
```
Memory Required =
  (number_of_time_series * 2KB) +    # Active series
  (ingestion_rate * 2 * retention_hours) +  # WAL and blocks
  (2GB)                               # Base overhead

CPU Cores Required =
  (ingestion_rate / 100,000) +        # Ingestion processing
  (query_rate / 10) +                 # Query processing
  (1)                                 # Base overhead

Disk IOPS Required =
  (ingestion_rate / 1000) +           # Write IOPS
  (query_rate * 100) +                # Read IOPS
  (100)                               # Background compaction
```

**Optimization Strategies**
1. **Reduce cardinality**: Audit and remove unnecessary labels
2. **Use recording rules**: Pre-compute expensive queries
3. **Optimize scrape configs**: Different intervals for different metrics
4. **Implement downsampling**: For long-term storage
5. **Horizontal sharding**: Separate Prometheus per service/team
6. **Remote storage**: Offload old data to object storage
7. **Query caching**: Use Trickster or built-in Grafana caching
8. **Metric relabeling**: Drop unwanted metrics at scrape time
9. **Federation**: Aggregate metrics hierarchically
10. **Capacity limits**: Set max_samples_per_send and queue sizes

**Scaling Thresholds**
- < 1M active series: Single Prometheus instance
- 1M - 10M series: Prometheus with remote storage
- 10M - 100M series: Sharded Prometheus or Cortex
- > 100M series: Thanos or multi-region Cortex

## Security Considerations

**Authentication & Authorization**
```yaml
# prometheus.yml with basic auth
scrape_configs:
  - job_name: 'secured-api'
    basic_auth:
      username: 'prometheus'
      password_file: '/etc/prometheus/password.txt'
    scheme: https
    tls_config:
      ca_file: '/etc/prometheus/ca.crt'
      cert_file: '/etc/prometheus/cert.crt'
      key_file: '/etc/prometheus/key.pem'
      insecure_skip_verify: false
```

**Network Security**
- Deploy monitoring stack in isolated subnet
- Use internal load balancers for Prometheus federation
- Implement mTLS between Prometheus and targets
- Restrict metrics endpoints to monitoring CIDR blocks
- Use VPN or private links for cross-region federation

**Data Security**
- Encrypt data at rest (filesystem encryption)
- Sanitize metrics to avoid leaking sensitive data
- Implement audit logging for all access
- Regular security scanning of monitoring infrastructure
- Rotate credentials and certificates regularly

**Compliance Considerations**
- GDPR: Avoid collecting PII in metrics labels
- HIPAA: Encrypt all health-related metrics
- PCI DSS: Separate payment metrics into isolated stack
- SOC 2: Maintain audit trails and access logs

## Troubleshooting Guide

**Issue: Prometheus consuming too much memory**
```bash
# 1. Check current memory usage and series count
curl -s http://localhost:9090/api/v1/status/tsdb | jq '.data.seriesCountByMetricName' | head -20

# 2. Find high cardinality metrics
curl -g 'http://localhost:9090/api/v1/query?query=count(count+by(__name__)({__name__=~".+"}))' | jq

# 3. Identify problematic labels
curl -s http://localhost:9090/api/v1/label/userId/values | jq '. | length'

# 4. Drop high-cardinality metrics
# Add to prometheus.yml:
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'problematic_metric_.*'
    action: drop
```

**Issue: Grafana dashboards loading slowly**
```bash
# 1. Check query performance
curl -s 'http://localhost:9090/api/v1/query_log' | jq '.data[] | select(.duration_seconds > 1)'

# 2. Analyze slow queries in Grafana
SELECT
  dashboard_id,
  panel_id,
  AVG(duration) as avg_duration,
  query
FROM grafana.query_history
WHERE duration > 1000
GROUP BY dashboard_id, panel_id, query
ORDER BY avg_duration DESC;

# 3. Optimize with recording rules
# Add to recording_rules.yml:
groups:
  - name: dashboard_queries
    interval: 30s
    rules:
      - record: api:request_rate5m
        expr: sum(rate(http_requests_total[5m])) by (service)
```

**Issue: Alerts not firing**
```bash
# 1. Check alert state
curl http://localhost:9090/api/v1/alerts | jq

# 2. Validate AlertManager config
docker exec alertmanager amtool config routes

# 3. Test alert routing
docker exec alertmanager amtool config routes test \
  --config.file=/etc/alertmanager/alertmanager.yml \
  --verify.receivers=slack-critical \
  severity=critical service=api

# 4. Check for inhibition rules
curl http://localhost:9093/api/v1/alerts | jq '.[] | select(.status.inhibitedBy != [])'
```

**Issue: Missing traces in Jaeger**
```javascript
// 1. Verify sampling rate
const tracer = initTracer({
  serviceName: 'api-gateway',
  sampler: {
    type: 'const',  // Change to 'const' for debugging
    param: 1,        // 1 = sample everything
  },
});

// 2. Check span reporting
tracer.on('span_finished', (span) => {
  console.log('Span finished:', span.operationName(), span.context().toTraceId());
});

// 3. Verify Jaeger agent connectivity
curl http://localhost:14268/api/traces?service=api-gateway
```

## Migration Guide

**From CloudWatch to Prometheus:**
```python
# Migration script example
import boto3
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

def migrate_cloudwatch_to_prometheus():
    # Read from CloudWatch
    cw = boto3.client('cloudwatch')
    metrics = cw.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        StartTime=datetime.now() - timedelta(hours=1),
        EndTime=datetime.now(),
        Period=300,
        Statistics=['Average']
    )

    # Write to Prometheus
    registry = CollectorRegistry()
    g = Gauge('aws_ec2_cpu_utilization', 'EC2 CPU Usage',
              ['instance_id'], registry=registry)

    for datapoint in metrics['Datapoints']:
        g.labels(instance_id='i-1234567890abcdef0').set(datapoint['Average'])
        push_to_gateway('localhost:9091', job='cloudwatch_migration', registry=registry)
```

**From Datadog to Prometheus:**
1. Export Datadog dashboards as JSON
2. Convert queries using query translator
3. Import to Grafana with dashboard converter
4. Map Datadog tags to Prometheus labels
5. Recreate alerts in AlertManager format

## Related Commands

- `/api-load-tester` - Generate test traffic to validate monitoring setup
- `/api-security-scanner` - Security testing with metrics integration
- `/add-rate-limiting` - Rate limiting with metrics exposure
- `/api-contract-generator` - Generate OpenAPI specs with metrics annotations
- `/deployment-pipeline-orchestrator` - CI/CD with monitoring integration
- `/api-versioning-manager` - Version-aware metrics tracking

## Advanced Topics

**Multi-Cluster Monitoring with Thanos:**
```yaml
# thanos-sidecar.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: thanos-config
data:
  object-store.yaml: |
    type: S3
    config:
      bucket: metrics-long-term
      endpoint: s3.amazonaws.com
      access_key: ${AWS_ACCESS_KEY}
      secret_key: ${AWS_SECRET_KEY}
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: prometheus-thanos
spec:
  template:
    spec:
      containers:
      - name: prometheus
        args:
          - --storage.tsdb.retention.time=2h
          - --storage.tsdb.min-block-duration=2h
          - --storage.tsdb.max-block-duration=2h
          - --web.enable-lifecycle
      - name: thanos-sidecar
        image: quay.io/thanos/thanos:v0.31.0
        args:
          - sidecar
          - --prometheus.url=http://localhost:9090
          - --objstore.config-file=/etc/thanos/object-store.yaml
```

**Service Mesh Observability (Istio):**
```yaml
# Automatic metrics from Istio
telemetry:
  v2:
    prometheus:
      providers:
        - name: prometheus
      configOverride:
        inboundSidecar:
          disable_host_header_fallback: false
          metric_expiry_duration: 10m
        outboundSidecar:
          disable_host_header_fallback: false
          metric_expiry_duration: 10m
        gateway:
          disable_host_header_fallback: true
```

## Version History

- v1.0.0 (2024-01): Initial Prometheus + Grafana implementation
- v1.1.0 (2024-03): Added Jaeger tracing integration
- v1.2.0 (2024-05): Thanos long-term storage support
- v1.3.0 (2024-07): OpenTelemetry collector integration
- v1.4.0 (2024-09): Multi-cluster federation support
- v1.5.0 (2024-10): Custom business metrics exporters
- Planned v2.0.0: eBPF-based zero-instrumentation monitoring
