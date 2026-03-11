# Guidewire Debug Bundle — Implementation Guide

## Debug Logging Configuration

```xml
<!-- config/logging/log4j2.xml -->
<Configuration status="WARN">
  <Appenders>
    <Console name="Console" target="SYSTEM_OUT">
      <PatternLayout pattern="%d{HH:mm:ss.SSS} [%t] %-5level %logger{36} - %msg%n"/>
    </Console>
    <RollingFile name="DebugFile" fileName="logs/debug.log"
                 filePattern="logs/debug-%d{yyyy-MM-dd}-%i.log.gz">
      <PatternLayout pattern="%d{ISO8601} [%t] %-5level %logger{36} - %msg%n"/>
      <Policies>
        <SizeBasedTriggeringPolicy size="100 MB"/>
      </Policies>
    </RollingFile>
  </Appenders>

  <Loggers>
    <Logger name="gw.custom" level="DEBUG"/>
    <Logger name="gw.plugin" level="DEBUG"/>
    <Logger name="gw.api.rest" level="DEBUG"/>
    <Logger name="gw.api.webservice" level="DEBUG"/>
    <Logger name="gw.api.database" level="DEBUG"/>
    <Logger name="org.hibernate.SQL" level="DEBUG"/>
    <Logger name="gw.integration" level="DEBUG"/>

    <Root level="INFO">
      <AppenderRef ref="Console"/>
      <AppenderRef ref="DebugFile"/>
    </Root>
  </Loggers>
</Configuration>
```

## Gosu Debug Helper

```gosu
package gw.custom.debug

uses gw.api.util.Logger

class DebugHelper {
  private static final var LOG = Logger.forCategory("DebugHelper")

  // Debug method entry/exit
  static function trace<T>(methodName : String, block() : T) : T {
    LOG.debug(">>> Entering ${methodName}")
    var startTime = System.currentTimeMillis()
    try {
      var result = block()
      LOG.debug("<<< Exiting ${methodName} (${System.currentTimeMillis() - startTime}ms)")
      return result
    } catch (e : Exception) {
      LOG.error("!!! Exception in ${methodName}: ${e.Message}", e)
      throw e
    }
  }

  // Dump entity state
  static function dumpEntity(entity : KeyableBean) {
    LOG.debug("=== Entity Dump: ${entity.IntrinsicType.Name} ===")
    LOG.debug("  ID: ${entity.ID}")
    LOG.debug("  PublicID: ${entity.PublicID}")

    entity.IntrinsicType.TypeInfo.Properties
      .where(\p -> !p.Name.startsWith("_"))
      .each(\prop -> {
        try {
          var value = prop.Accessor.getValue(entity)
          LOG.debug("  ${prop.Name}: ${value}")
        } catch (e : Exception) {
          LOG.debug("  ${prop.Name}: <error reading>")
        }
      })
  }

  // Debug query execution
  static function debugQuery<T>(query : Query<T>) : List<T> {
    LOG.debug("Query: ${query.toString()}")
    var startTime = System.currentTimeMillis()
    var results = query.select().toList()
    var elapsed = System.currentTimeMillis() - startTime
    LOG.debug("Query returned ${results.Count} rows in ${elapsed}ms")
    return results
  }
}
```

## API Request Tracing

```typescript
import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

function createDebugClient(): AxiosInstance {
  const client = axios.create({
    baseURL: process.env.POLICYCENTER_URL,
    timeout: 30000
  });

  // Request interceptor
  client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const requestId = crypto.randomUUID();
    config.headers['X-Request-ID'] = requestId;

    console.log(`[${requestId}] >>> ${config.method?.toUpperCase()} ${config.url}`);
    if (config.data) {
      console.log(`[${requestId}] Request body:`, JSON.stringify(config.data, null, 2));
    }

    (config as any).metadata = { startTime: Date.now(), requestId };
    return config;
  });

  // Response interceptor
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      const metadata = (response.config as any).metadata;
      const elapsed = Date.now() - metadata.startTime;
      const traceId = response.headers['x-gw-trace-id'];

      console.log(`[${metadata.requestId}] <<< ${response.status} (${elapsed}ms) trace=${traceId}`);
      console.log(`[${metadata.requestId}] Response:`, JSON.stringify(response.data, null, 2));

      return response;
    },
    (error) => {
      const metadata = (error.config as any)?.metadata;
      console.error(`[${metadata?.requestId}] !!! Error:`, error.response?.data || error.message);
      throw error;
    }
  );

  return client;
}
```

## Cloud Console Log Queries

```bash
# Common log queries (Lucene syntax)
# Find errors for a specific claim
claimNumber:"CLM-001234" AND level:ERROR

# Find slow API calls (>5 seconds)
message:"API call completed" AND duration:[5000 TO *]

# Find authentication failures
category:"Authentication" AND level:WARN

# Find integration errors
category:"gw.integration*" AND level:ERROR

# Download logs via API
curl -X GET "https://your-tenant.cloud.guidewire.com/api/v1/logs" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d "from=2024-01-15T00:00:00Z" \
  -d "to=2024-01-15T23:59:59Z" \
  -d "filter=level:ERROR" \
  -o error-logs.json
```

## Database Query Analysis

```gosu
uses gw.api.database.Query
uses gw.api.database.QueryPlanExplainer

class QueryDebugger {

  static function explainQuery<T>(query : Query<T>) : String {
    var explainer = new QueryPlanExplainer(query)
    var plan = explainer.explain()

    LOG.debug("=== Query Execution Plan ===")
    LOG.debug("SQL: ${plan.SQL}")
    LOG.debug("Estimated Rows: ${plan.EstimatedRows}")
    LOG.debug("Index Used: ${plan.IndexUsed}")
    LOG.debug("Scan Type: ${plan.ScanType}")

    if (plan.ScanType == "FULL_TABLE_SCAN" && plan.EstimatedRows > 10000) {
      LOG.warn("WARNING: Full table scan on large table!")
    }

    return plan.toString()
  }

  static function profileQuery<T>(name : String, query : Query<T>) : List<T> {
    var startTime = System.nanoTime()
    var results = query.select().toList()
    var elapsed = (System.nanoTime() - startTime) / 1_000_000.0

    LOG.info("Query '${name}': ${results.Count} rows in ${elapsed}ms")

    if (elapsed > 1000) {
      LOG.warn("Slow query detected: ${name}")
      explainQuery(query)
    }

    return results
  }
}
```

## Memory and Thread Analysis

```gosu
class MemoryDebugger {
  static function logMemoryUsage() {
    var runtime = Runtime.getRuntime()
    var totalMB = runtime.totalMemory() / 1024 / 1024
    var freeMB = runtime.freeMemory() / 1024 / 1024
    var usedMB = totalMB - freeMB
    var maxMB = runtime.maxMemory() / 1024 / 1024

    LOG.info("Memory: used=${usedMB}MB, free=${freeMB}MB, total=${totalMB}MB, max=${maxMB}MB")

    if (usedMB > maxMB * 0.9) {
      LOG.warn("HIGH MEMORY USAGE: ${(usedMB * 100.0 / maxMB) as int}%")
    }
  }

  static function dumpThreads() {
    LOG.info("=== Thread Dump ===")
    Thread.getAllStackTraces().each(\thread, stack -> {
      LOG.info("Thread: ${thread.Name} [${thread.State}]")
      stack.each(\frame -> {
        LOG.info("  at ${frame}")
      })
    })
  }
}
```

## Debug Support Bundle

```typescript
interface DebugBundle {
  timestamp: string;
  environment: string;
  version: string;
  systemInfo: any;
  recentErrors: any[];
  configSnapshot: any;
  performanceMetrics: any;
}

async function collectDebugBundle(): Promise<DebugBundle> {
  const bundle: DebugBundle = {
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'unknown',
    version: process.env.APP_VERSION || 'unknown',
    systemInfo: await getSystemInfo(),
    recentErrors: await getRecentErrors(100),
    configSnapshot: getConfigSnapshot(),
    performanceMetrics: await getPerformanceMetrics()
  };

  const filename = `debug-bundle-${Date.now()}.json`;
  await fs.writeFile(filename, JSON.stringify(bundle, null, 2));
  console.log(`Debug bundle saved to ${filename}`);

  return bundle;
}

async function getSystemInfo() {
  return {
    nodeVersion: process.version,
    platform: process.platform,
    memoryUsage: process.memoryUsage(),
    uptime: process.uptime(),
    apiEndpoint: process.env.POLICYCENTER_URL
  };
}
```

## Debugging Workflow Failures

```gosu
class WorkflowDebugger {
  static function debugWorkflowStep(workflow : Workflow, step : WorkflowStep) {
    LOG.debug("=== Workflow Step Debug ===")
    LOG.debug("Workflow: ${workflow.Name}")
    LOG.debug("Step: ${step.Name}")
    LOG.debug("Status: ${step.Status}")

    step.Preconditions.each(\precond -> {
      var result = precond.evaluate(workflow.Context)
      LOG.debug("Precondition '${precond.Name}': ${result}")
    })

    step.AvailableActions.each(\action -> {
      LOG.debug("Available action: ${action.Name}")
    })
  }
}
```

## Debugging Integration Failures

```gosu
class IntegrationDebugger {
  static function debugRequest(request : RestRequest) {
    LOG.debug("=== Outbound Request ===")
    LOG.debug("URL: ${request.URL}")
    LOG.debug("Method: ${request.Method}")
    LOG.debug("Headers:")
    request.Headers.each(\name, value -> {
      var displayValue = name.toLowerCase().contains("auth") ? "***" : value
      LOG.debug("  ${name}: ${displayValue}")
    })
    LOG.debug("Body: ${request.Body}")
  }

  static function debugResponse(response : RestResponse) {
    LOG.debug("=== Inbound Response ===")
    LOG.debug("Status: ${response.StatusCode}")
    LOG.debug("Headers:")
    response.Headers.each(\name, value -> {
      LOG.debug("  ${name}: ${value}")
    })
    LOG.debug("Body: ${response.Body}")
  }
}
```
