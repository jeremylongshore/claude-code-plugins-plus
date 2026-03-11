---
name: testing-load-balancers
description: |
  Validate load balancer behavior, failover, and traffic distribution.
  Use when performing specialized testing.
  Trigger with phrases like "test load balancer", "validate failover", or "check traffic distribution".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:loadbalancer-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Load Balancer Tester

## Overview

Validate load balancer behavior including traffic distribution algorithms, health check mechanisms, failover scenarios, session persistence, and SSL termination. Supports testing for NGINX, HAProxy, AWS ALB/NLB, GCP Load Balancers, and Kubernetes Ingress controllers.

## Prerequisites

- Load balancer deployed and accessible in a test environment
- Multiple backend instances running with identifiable responses (hostname headers)
- HTTP client tools (`curl`, `wrk`, `hey`, or `k6`) for sending test traffic
- Access to load balancer configuration and health check settings
- Ability to stop/start backend instances to simulate failures

## Instructions

1. Verify basic load balancer connectivity:
   - Send a request through the load balancer and confirm a backend response.
   - Check the response includes identifying headers (`X-Backend-Server`, `Server`) to determine which instance served the request.
   - Verify SSL/TLS termination works correctly (valid certificate, proper redirect from HTTP to HTTPS).
2. Test traffic distribution algorithm:
   - Send 100+ sequential requests and record which backend handled each.
   - For round-robin: verify even distribution across all backends (within 5% tolerance).
   - For least-connections: verify the least-loaded backend receives new requests.
   - For weighted: verify traffic ratio matches configured weights.
3. Validate health check behavior:
   - Stop one backend instance.
   - Verify the load balancer detects the failure within the configured health check interval.
   - Confirm subsequent requests are routed only to healthy backends (zero errors).
   - Restart the backend and verify it is returned to the pool after passing health checks.
4. Test failover scenarios:
   - Stop all backends except one and verify the remaining backend handles all traffic.
   - Stop all backends and verify the load balancer returns a 502 or 503 error (not hang).
   - Simulate slow backend responses and verify timeout behavior.
5. Validate session persistence (sticky sessions):
   - Send multiple requests with the same session cookie.
   - Verify all requests route to the same backend instance.
   - Verify a new session (no cookie) can route to any backend.
6. Test connection draining:
   - Start a long-running request, then remove the backend from the pool.
   - Verify the in-flight request completes successfully.
   - Verify new requests route to remaining backends.
7. Document all results with request/response evidence and timing data.

## Output

- Traffic distribution report showing request counts per backend instance
- Health check failover timeline with detection and recovery durations
- Session persistence validation results
- SSL/TLS certificate and configuration verification
- Load balancer behavior summary with pass/fail for each test scenario

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| All requests hit the same backend | Session affinity enabled unintentionally or DNS caching | Disable sticky sessions for distribution tests; use different source IPs; bypass DNS cache |
| Health check passes but backend is unhealthy | Health check endpoint does not reflect actual application health | Configure health checks to hit a deep endpoint that verifies database connectivity |
| 502 Bad Gateway during failover | Health check interval too long; load balancer still routing to failed backend | Reduce health check interval and failure threshold; verify deregistration delay settings |
| SSL certificate error | Certificate does not match domain or is expired | Verify certificate SAN entries; check expiration date; ensure full certificate chain is configured |
| Connection refused on backend port | Firewall or security group blocking load balancer to backend traffic | Verify security group rules allow traffic from load balancer subnet; check backend listen address |

## Examples

**Traffic distribution test with curl:**
```bash
#!/bin/bash
set -euo pipefail
declare -A counts
for i in $(seq 1 100); do
  backend=$(curl -s -H "Host: app.test.com" http://lb.test.com/health \
    | jq -r '.hostname')
  counts[$backend]=$(( ${counts[$backend]:-0} + 1 ))
done
echo "Traffic distribution:"
for backend in "${!counts[@]}"; do
  echo "  $backend: ${counts[$backend]} requests"
done
```

**Failover test sequence:**
```bash
set -euo pipefail
# 1. Verify both backends serve traffic
curl -s http://lb.test.com/health  # Backend A
curl -s http://lb.test.com/health  # Backend B

# 2. Stop Backend A
docker stop backend-a

# 3. Verify all traffic goes to Backend B (no errors)
for i in $(seq 1 10); do
  curl -sf http://lb.test.com/health || echo "FAIL: request $i"
done

# 4. Restart Backend A and verify it rejoins
docker start backend-a
sleep 10  # Wait for health check interval
curl -s http://lb.test.com/health  # Should see Backend A again
```

**k6 load test against load balancer:**
```javascript
import http from 'k6/http';
import { check } from 'k6';

export const options = { vus: 50, duration: '30s' };

export default function () {
  const res = http.get('http://lb.test.com/api/data');
  check(res, {
    'status is 200': (r) => r.status === 200,  # HTTP 200 OK
    'response time < 500ms': (r) => r.timings.duration < 500,  # HTTP 500 Internal Server Error
  });
}
```

## Resources

- NGINX load balancing: https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/
- HAProxy documentation: https://www.haproxy.org/download/2.9/doc/configuration.txt
- AWS ALB documentation: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/
- k6 load testing: https://grafana.com/docs/k6/latest/
- hey HTTP load generator: https://github.com/rakyll/hey