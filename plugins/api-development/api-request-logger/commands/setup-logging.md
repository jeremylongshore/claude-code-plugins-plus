---
name: setup-logging
description: Set up API request logging
shortcut: logs
---
# Set Up API Request Logging

Implement production-grade structured logging with correlation IDs, request/response capture, PII redaction, and integration with log aggregation platforms.

## When to Use This Command

Use `/setup-logging` when you need to:
- Debug production issues with complete request context
- Track user journeys across distributed services
- Meet compliance requirements (audit trails, GDPR)
- Analyze API performance and usage patterns
- Investigate security incidents with detailed forensics
- Monitor business metrics derived from API usage

DON'T use this when:
- Building throwaway prototypes (use console.log)
- Extremely high-throughput systems where logging overhead matters (use sampling)
- Already using comprehensive APM tool (avoid duplication)

## Design Decisions

This command implements **Structured JSON logging with Winston/Bunyan** as the primary approach because:
- JSON format enables powerful query capabilities in log aggregation tools
- Structured data easier to parse and analyze than free-text logs
- Correlation IDs enable distributed tracing across services
- Standard libraries with proven reliability at scale

**Alternative considered: Plain text logging**
- Human-readable without tools
- Difficult to query and aggregate
- No structured fields for filtering
- Recommended only for simple applications

**Alternative considered: Binary logging protocols (gRPC, protobuf)**
- More efficient storage and transmission
- Requires specialized tooling to read
- Added complexity without clear benefits for most use cases
- Recommended only for extremely high-volume scenarios

**Alternative considered: Managed logging services (Datadog, Loggly)**
- Fastest time-to-value with built-in dashboards
- Higher ongoing costs
- Potential vendor lock-in
- Recommended for teams without logging infrastructure

## Prerequisites

Before running this command:
1. Node.js/Python runtime with logging library support
2. Understanding of sensitive data in your API (for PII redaction)
3. Log aggregation platform (ELK stack, Splunk, CloudWatch, etc.)
4. Disk space or log shipping configuration for log retention
5. Compliance requirements documented (GDPR, HIPAA, SOC2)

## Implementation Process

### Step 1: Configure Structured Logger
Set up Winston (Node.js) or structlog (Python) with JSON formatting and appropriate transports.

### Step 2: Implement Correlation ID Middleware
Generate unique request IDs and propagate through entire request lifecycle and downstream services.

### Step 3: Add Request/Response Logging Middleware
Capture HTTP method, path, headers, body, status code, and response time with configurable verbosity.

### Step 4: Implement PII Redaction
Identify and mask sensitive data (passwords, tokens, credit cards, SSNs) before logging.

### Step 5: Configure Log Shipping
Set up log rotation, compression, and shipping to centralized log aggregation platform.

## Output Format

The command generates:
- `logger.js` or `logger.py` - Core logging configuration and utilities
- `logging-middleware.js` - Express/FastAPI middleware for request logging
- `pii-redactor.js` - PII detection and masking utilities
- `log-shipping-config.json` - Fluentd/Filebeat/Logstash configuration
- `logger.test.js` - Test suite for logging functionality
- `README.md` - Integration guide and best practices

## Code Examples

### Example 1: Structured Logging with Winston and Correlation IDs

```javascript
// logger.js - Winston configuration with correlation IDs
const winston = require('winston');
const { v4: uuidv4 } = require('uuid');
const cls = require('cls-hooked');

// Create namespace for correlation ID context
const namespace = cls.createNamespace('request-context');

// Custom format for correlation ID
const correlationIdFormat = winston.format((info) => {
  const correlationId = namespace.get('correlationId');
  if (correlationId) {
    info.correlationId = correlationId;
  }
  return info;
});

// Custom format for sanitizing sensitive data
const sanitizeFormat = winston.format((info) => {
  if (info.meta && typeof info.meta === 'object') {
    info.meta = sanitizeSensitiveData(info.meta);
  }
  if (info.req && info.req.headers) {
    info.req.headers = sanitizeHeaders(info.req.headers);
  }
  return info;
});

// Create logger instance
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' }),
    correlationIdFormat(),
    sanitizeFormat(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: {
    service: process.env.SERVICE_NAME || 'api',
    environment: process.env.NODE_ENV || 'development',
    version: process.env.APP_VERSION || '1.0.0'
  },
  transports: [
    // Console transport for development
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.printf(({ timestamp, level, message, correlationId, ...meta }) => {
          const corrId = correlationId ? `[${correlationId}]` : '';
          return `${timestamp} ${level} ${corrId}: ${message} ${JSON.stringify(meta)}`;
        })
      )
    }),
    // File transport for production
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error',
      maxsize: 10485760, // 10MB
      maxFiles: 5
    }),
    new winston.transports.File({
      filename: 'logs/combined.log',
      maxsize: 10485760, // 10MB
      maxFiles: 10
    })
  ],
  // Don't exit on uncaught exception
  exitOnError: false
});

// PII redaction utilities
function sanitizeSensitiveData(obj) {
  const sensitiveKeys = ['password', 'token', 'apiKey', 'secret', 'authorization', 'creditCard', 'ssn', 'cvv'];
  const sanitized = { ...obj };

  for (const key of Object.keys(sanitized)) {
    const lowerKey = key.toLowerCase();
    if (sensitiveKeys.some(sensitive => lowerKey.includes(sensitive))) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof sanitized[key] === 'object' && sanitized[key] !== null) {
      sanitized[key] = sanitizeSensitiveData(sanitized[key]);
    }
  }

  return sanitized;
}

function sanitizeHeaders(headers) {
  const sanitized = { ...headers };
  const sensitiveHeaders = ['authorization', 'cookie', 'x-api-key', 'x-auth-token'];

  for (const header of sensitiveHeaders) {
    if (sanitized[header]) {
      sanitized[header] = '[REDACTED]';
    }
  }

  return sanitized;
}

// Middleware to set correlation ID
function correlationIdMiddleware(req, res, next) {
  namespace.run(() => {
    const correlationId = req.headers['x-correlation-id'] || uuidv4();
    namespace.set('correlationId', correlationId);
    res.setHeader('X-Correlation-Id', correlationId);
    next();
  });
}

// Request logging middleware
function requestLoggingMiddleware(req, res, next) {
  const startTime = Date.now();

  // Log incoming request
  logger.info('Incoming request', {
    method: req.method,
    path: req.path,
    query: req.query,
    ip: req.ip,
    userAgent: req.get('user-agent'),
    userId: req.user?.id,
    body: shouldLogBody(req) ? sanitizeSensitiveData(req.body) : '[OMITTED]'
  });

  // Capture response
  const originalSend = res.send;
  res.send = function (data) {
    res.send = originalSend;

    const duration = Date.now() - startTime;
    const statusCode = res.statusCode;

    // Log outgoing response
    logger.info('Outgoing response', {
      method: req.method,
      path: req.path,
      statusCode,
      duration,
      userId: req.user?.id,
      responseSize: data?.length || 0,
      response: shouldLogResponse(req, statusCode) ? sanitizeSensitiveData(JSON.parse(data)) : '[OMITTED]'
    });

    return res.send(data);
  };

  next();
}

function shouldLogBody(req) {
  // Only log body for specific endpoints or methods
  const logBodyPaths = ['/api/auth/login', '/api/users'];
  return req.method !== 'GET' && logBodyPaths.some(path => req.path.startsWith(path));
}

function shouldLogResponse(req, statusCode) {
  // Log responses for errors or specific endpoints
  return statusCode >= 400 || req.path.startsWith('/api/critical');
}

module.exports = {
  logger,
  correlationIdMiddleware,
  requestLoggingMiddleware,
  namespace
};
```

### Example 2: Python Structured Logging with FastAPI and PII Redaction

```python
# logger.py - Structlog configuration with PII redaction
import logging
import structlog
import uuid
import re
from contextvars import ContextVar
from typing import Any, Dict
from fastapi import Request, Response
import time

# Context variable for correlation ID
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default=None)

# PII patterns for redaction
PII_PATTERNS = {
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'credit_card': re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
    'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
    'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
}

SENSITIVE_KEYS = ['password', 'token', 'secret', 'api_key', 'authorization', 'credit_card', 'ssn', 'cvv']

def redact_pii(data: Any) -> Any:
    """Recursively redact PII from data structures"""
    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            # Check if key is sensitive
            if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
                redacted[key] = '[REDACTED]'
            else:
                redacted[key] = redact_pii(value)
        return redacted

    elif isinstance(data, list):
        return [redact_pii(item) for item in data]

    elif isinstance(data, str):
        # Apply PII pattern matching
        redacted_str = data
        for pattern_name, pattern in PII_PATTERNS.items():
            if pattern_name == 'email':
                # Partially redact emails (keep domain)
                redacted_str = pattern.sub(lambda m: f"***@{m.group(0).split('@')[1]}", redacted_str)
            else:
                redacted_str = pattern.sub('[REDACTED]', redacted_str)
        return redacted_str

    return data

def add_correlation_id(logger, method_name, event_dict):
    """Add correlation ID to log context"""
    correlation_id = correlation_id_var.get()
    if correlation_id:
        event_dict['correlation_id'] = correlation_id
    return event_dict

def add_service_context(logger, method_name, event_dict):
    """Add service metadata to logs"""
    import os
    event_dict['service'] = os.getenv('SERVICE_NAME', 'api')
    event_dict['environment'] = os.getenv('ENVIRONMENT', 'development')
    event_dict['version'] = os.getenv('APP_VERSION', '1.0.0')
    return event_dict

# Configure structlog
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_correlation_id,
        add_service_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Configure standard library logging
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/app.log')
    ]
)

# Create logger instance
logger = structlog.get_logger()

class RequestLoggingMiddleware:
    """FastAPI middleware for comprehensive request logging"""

    def __init__(self, app):
        self.app = app
        self.logger = structlog.get_logger()

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        correlation_id_var.set(correlation_id)

        request = Request(scope, receive)
        start_time = time.time()

        # Log incoming request
        body = await self._get_body(request)
        self.logger.info(
            "Incoming request",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
            body=redact_pii(body) if self._should_log_body(request) else '[OMITTED]'
        )

        # Capture response
        status_code = 500
        response_body = b''

        async def send_wrapper(message):
            nonlocal status_code, response_body
            if message['type'] == 'http.response.start':
                status_code = message['status']
                # Add correlation ID header
                headers = list(message.get('headers', []))
                headers.append((b'x-correlation-id', correlation_id.encode()))
                message['headers'] = headers
            elif message['type'] == 'http.response.body':
                response_body += message.get('body', b'')
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start_time

            # Log outgoing response
            self.logger.info(
                "Outgoing response",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=round(duration * 1000, 2),
                response_size=len(response_body),
                response=redact_pii(response_body.decode()) if self._should_log_response(status_code) else '[OMITTED]'
            )

    async def _get_body(self, request: Request) -> dict:
        """Safely get request body"""
        try:
            return await request.json()
        except:
            return {}

    def _should_log_body(self, request: Request) -> bool:
        """Determine if request body should be logged"""
        sensitive_paths = ['/api/auth', '/api/payment']
        return not any(request.url.path.startswith(path) for path in sensitive_paths)

    def _should_log_response(self, status_code: int) -> bool:
        """Determine if response body should be logged"""
        return status_code >= 400  # Log error responses

# Usage in FastAPI
from fastapi import FastAPI

app = FastAPI()

# Add middleware
app.add_middleware(RequestLoggingMiddleware)

# Example endpoint with logging
@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    logger.info("Fetching user", user_id=user_id)
    try:
        # Simulate user fetch
        user = {"id": user_id, "email": "user@example.com", "ssn": "123-45-6789"}
        logger.info("User fetched successfully", user_id=user_id)
        return redact_pii(user)
    except Exception as e:
        logger.error("Failed to fetch user", user_id=user_id, error=str(e))
        raise
```

### Example 3: Log Shipping with Filebeat and ELK Stack

```yaml
# filebeat.yml - Filebeat configuration for log shipping
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/api/combined.log
    json.keys_under_root: true
    json.add_error_key: true
    fields:
      service: api-gateway
      datacenter: us-east-1
    fields_under_root: true

  - type: log
    enabled: true
    paths:
      - /var/log/api/error.log
    json.keys_under_root: true
    json.add_error_key: true
    fields:
      service: api-gateway
      datacenter: us-east-1
      log_level: error
    fields_under_root: true

# Processors for enrichment
processors:
  - add_host_metadata:
      when.not.contains.tags: forwarded
  - add_cloud_metadata: ~
  - add_docker_metadata: ~
  - add_kubernetes_metadata: ~

  # Drop debug logs in production
  - drop_event:
      when:
        and:
          - equals:
              environment: production
          - equals:
              level: debug

# Output to Elasticsearch
output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "api-logs-%{+yyyy.MM.dd}"
  username: "${ELASTICSEARCH_USERNAME}"
  password: "${ELASTICSEARCH_PASSWORD}"

# Output to Logstash (alternative)
# output.logstash:
#   hosts: ["logstash:5044"]
#   compression_level: 3
#   bulk_max_size: 2048

# Logging configuration
logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644

# Enable monitoring
monitoring.enabled: true
```

```yaml
# docker-compose.yml - Complete ELK stack for log aggregation
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    networks:
      - logging

  logstash:
    image: docker.elastic.co/logstash/logstash:8.10.0
    container_name: logstash
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5044:5044"
    networks:
      - logging
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.10.0
    container_name: kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    networks:
      - logging
    depends_on:
      - elasticsearch

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.10.0
    container_name: filebeat
    user: root
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/log/api:/var/log/api:ro
      - filebeat-data:/usr/share/filebeat/data
    command: filebeat -e -strict.perms=false
    networks:
      - logging
    depends_on:
      - elasticsearch
      - logstash

networks:
  logging:
    driver: bridge

volumes:
  elasticsearch-data:
  filebeat-data:
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Log file not writable" | Permission issues | Ensure log directory has correct permissions, run with appropriate user |
| "Disk space full" | Logs not rotated | Implement log rotation, compress old logs, ship to remote storage |
| "PII detected in logs" | Incomplete redaction rules | Review and update PII patterns, audit existing logs |
| "High logging latency" | Synchronous file writes | Use async logging, buffer writes, or log to separate thread |
| "Lost correlation IDs" | Missing middleware or context propagation | Ensure middleware order is correct, propagate context to async operations |

## Configuration Options

**Log Levels**
- `debug`: Verbose output for development (not in production)
- `info`: General operational messages (default)
- `warn`: Unexpected but handled conditions
- `error`: Errors requiring attention
- `fatal`: Critical errors causing service failure

**Log Rotation**
- **Size-based**: Rotate when file reaches 10MB
- **Time-based**: Rotate daily at midnight
- **Retention**: Keep 7-30 days based on compliance requirements
- **Compression**: Gzip rotated logs to save space

**PII Redaction Strategies**
- **Pattern matching**: Regex for emails, SSNs, credit cards
- **Key-based**: Redact specific field names (password, token)
- **Partial redaction**: Keep domain for emails (***@example.com)
- **Tokenization**: Replace with consistent token for analysis

## Best Practices

DO:
- Use structured JSON logging for machine readability
- Generate correlation IDs for request tracking across services
- Redact PII before logging (passwords, tokens, SSNs, credit cards)
- Include sufficient context (user ID, request path, duration)
- Set appropriate log levels (info for production, debug for development)
- Implement log rotation and retention policies

DON'T:
- Log passwords, API keys, or authentication tokens
- Use console.log in production (no structure or persistence)
- Log full request/response bodies without sanitization
- Ignore log volume (can cause disk space or cost issues)
- Log at debug level in production (performance impact)
- Forget to propagate correlation IDs to downstream services

TIPS:
- Start with conservative logging, increase verbosity during incidents
- Use log sampling for high-volume endpoints (log 1%)
- Create dashboards for common queries (error rates, slow requests)
- Set up alerts for error rate spikes or specific error patterns
- Document log schema for easier querying
- Test PII redaction with known sensitive data

## Performance Considerations

**Logging Overhead**
- Structured logging: ~0.1-0.5ms per log statement
- JSON serialization: Negligible for small objects
- PII redaction: 1-2ms for complex objects
- File I/O: Use async writes to avoid blocking

**Optimization Strategies**
- Use log levels to control verbosity
- Sample high-volume logs (log 1 in 100 requests)
- Buffer logs before writing to disk
- Use separate thread for log processing
- Compress logs before shipping to reduce bandwidth

**Volume Management**
- Typical API: 100-500 log lines per request
- At 1000 req/s: 100k-500k log lines/s
- With 1KB per line: 100-500 MB/s log volume
- Plan for log retention and storage costs

## Security Considerations

1. **PII Protection**: Redact sensitive data before logging (GDPR, CCPA compliance)
2. **Access Control**: Restrict log access to authorized personnel only
3. **Encryption**: Encrypt logs at rest and in transit
4. **Audit Trail**: Log administrative actions (config changes, user access)
5. **Injection Prevention**: Sanitize user input to prevent log injection attacks
6. **Retention Policies**: Delete logs after retention period (compliance requirement)

## Compliance Considerations

**GDPR Requirements**
- Log only necessary personal data
- Implement data minimization
- Provide mechanism to delete user logs (right to be forgotten)
- Document data retention policies

**HIPAA Requirements**
- Encrypt logs containing PHI
- Maintain audit trails for access
- Implement access controls
- Regular security audits

**SOC 2 Requirements**
- Centralized log aggregation
- Tamper-proof log storage
- Real-time monitoring and alerting
- Regular log review procedures

## Troubleshooting

**Logs Not Appearing**
```bash
# Check log file permissions
ls -la /var/log/api/

# Verify logging middleware is registered
# Check application startup logs

# Test logger directly
curl -X POST http://localhost:3000/api/test -d '{"test": "data"}'
tail -f /var/log/api/combined.log
```

**Missing Correlation IDs**
```bash
# Verify correlation ID middleware is first
# Check middleware order in application

# Test correlation ID propagation
curl -H "X-Correlation-Id: test-123" http://localhost:3000/api/test
grep "test-123" /var/log/api/combined.log
```

**PII Leaking into Logs**
```bash
# Search for common PII patterns
grep -E '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b' /var/log/api/combined.log
grep -E '\b\d{3}-\d{2}-\d{4}\b' /var/log/api/combined.log

# Review and update redaction rules
# Audit existing logs and delete if necessary
```

**High Disk Usage from Logs**
```bash
# Check log directory size
du -sh /var/log/api/

# Review log rotation configuration
cat /etc/logrotate.d/api

# Manually rotate logs
logrotate -f /etc/logrotate.d/api

# Enable compression and reduce retention
```

## Related Commands

- `/create-monitoring` - Visualize log data with dashboards and alerts
- `/add-rate-limiting` - Log rate limit violations for security analysis
- `/api-security-scanner` - Audit security-relevant log events
- `/api-error-handler` - Integrate error handling with structured logging

## Version History

- v1.0.0 (2024-10): Initial implementation with Winston/structlog and PII redaction
- Planned v1.1.0: Add OpenTelemetry integration for unified observability
