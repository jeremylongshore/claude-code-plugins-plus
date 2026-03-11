---
name: running-chaos-tests
description: |
  Execute chaos engineering experiments to test system resilience.
  Use when performing specialized testing.
  Trigger with phrases like "run chaos tests", "test resilience", or "inject failures".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:chaos-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Chaos Engineering Toolkit

## Overview

Execute controlled chaos engineering experiments to test system resilience, fault tolerance, and recovery capabilities. Injects failures including network latency, service crashes, resource exhaustion, and dependency outages to verify that systems degrade gracefully and recover automatically. Supports Chaos Monkey principles, Litmus Chaos (Kubernetes), Pumba (Docker), toxiproxy (network failures), and custom fault injection scripts.

## Prerequisites

- Distributed system or microservice architecture deployed in a staging/test environment
- Monitoring and alerting configured (Grafana, Datadog, CloudWatch, or Prometheus)
- Rollback capability for the target environment (manual or automated)
- Chaos engineering tool installed (toxiproxy, Pumba, Litmus, or Chaos Mesh)
- Explicit approval from the team to run chaos experiments
- Steady-state hypothesis defined (what "healthy" looks like in metrics)

## Instructions

1. Define the steady-state hypothesis:
   - Identify measurable indicators of normal system behavior (e.g., p99 latency < 500ms, error rate < 0.1%, all health checks pass).
   - Record baseline metrics before injecting any failures.
   - Define the blast radius -- which services and users are affected by the experiment.
2. Design chaos experiments by category:
   - **Network**: Inject latency (200-2000ms), packet loss (5-50%), DNS failure, connection timeout.
   - **Process**: Kill a service instance, exhaust CPU or memory, fill disk.
   - **Dependency**: Block access to database, cache, or external API.
   - **State**: Corrupt data, introduce clock skew, simulate split-brain scenarios.
3. Start with minimal impact and increase gradually:
   - Begin with read-only experiments (network latency on non-critical path).
   - Progress to service-level failures (kill one instance of a multi-instance service).
   - Only move to data-level chaos after infrastructure chaos is validated.
4. Execute each experiment with safeguards:
   - Set a maximum experiment duration (5-15 minutes).
   - Configure automatic rollback triggers (error rate > 5% triggers abort).
   - Monitor system metrics in real-time during the experiment.
   - Have a manual kill switch ready (script to remove all injected failures immediately).
5. Observe and record system behavior during the experiment:
   - Did circuit breakers activate? How quickly?
   - Did auto-scaling trigger? How long until new instances were healthy?
   - Did retries succeed? Were they idempotent?
   - Did fallback mechanisms engage (cached responses, degraded mode)?
   - Were alerts triggered? Did on-call receive notification?
6. After the experiment, verify full recovery:
   - Remove all injected failures.
   - Verify steady-state hypothesis holds again within expected recovery time.
   - Check for data inconsistencies or orphaned state.
7. Document findings and create action items for resilience improvements.

## Output

- Chaos experiment definition files (YAML or JSON) with hypothesis, method, and rollback
- Experiment execution log with timeline of injected failures and observed effects
- System behavior report covering circuit breakers, retries, fallbacks, and alerts
- Recovery timeline showing time-to-detection and time-to-recovery
- Action items for resilience improvements (retry policies, circuit breaker tuning, fallback additions)

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Experiment caused production outage | Blast radius larger than expected or missing safeguards | Always run in staging first; reduce scope; add automatic abort triggers; require approval |
| System did not recover after experiment | Auto-healing mechanisms not configured or too slow | Add health-check-based restarts; configure auto-scaling; implement circuit breaker patterns |
| Monitoring missed the failure | Alerting thresholds too lenient or wrong metrics monitored | Tighten alert thresholds; add specific alerts for the failure mode tested; verify alert channels |
| Chaos tool cannot access target | Network segmentation or security policies blocking the tool | Deploy chaos agent inside the target network; add security group rules for the chaos controller |
| Data corruption persists after rollback | Stateful failure injection without transaction protection | Use read-only chaos first; snapshot databases before stateful experiments; implement compensating transactions |

## Examples

**toxiproxy network latency injection:**
```bash
# Create a proxy for the database connection
toxiproxy-cli create postgres_proxy -l 0.0.0.0:15432 -u postgres-host:5432

# Inject 500ms latency
toxiproxy-cli toxic add postgres_proxy -t latency -a latency=500 -a jitter=100

# Run tests while latency is active
npm test -- --grep "handles slow database"

# Remove the toxic
toxiproxy-cli toxic remove postgres_proxy -n latency_downstream
```

**Kubernetes pod kill experiment (Litmus Chaos):**
```yaml
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: api-pod-kill
spec:
  appinfo:
    appns: default
    applabel: "app=api-server"
  chaosServiceAccount: litmus-admin
  experiments:
    - name: pod-delete
      spec:
        components:
          env:
            - name: TOTAL_CHAOS_DURATION
              value: "60"
            - name: CHAOS_INTERVAL
              value: "10"
            - name: FORCE
              value: "true"
```

**Custom chaos script (process kill and verify recovery):**
```bash
#!/bin/bash
echo "=== Chaos Experiment: API server kill ==="
echo "Hypothesis: System recovers within 30 seconds"

# Record baseline
BASELINE=$(curl -s -o /dev/null -w '%{http_code}' http://app.test/health)
echo "Baseline health: $BASELINE"

# Kill one API instance
docker kill api-server-1

# Monitor recovery
for i in $(seq 1 30); do
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 http://app.test/health)
  echo "T+${i}s: HTTP $STATUS"
  if [ "$STATUS" = "200" ]; then
    echo "RECOVERED at T+${i}s"
    break
  fi
  sleep 1
done
```

## Resources

- Principles of Chaos Engineering: https://principlesofchaos.org/
- toxiproxy: https://github.com/Shopify/toxiproxy
- Litmus Chaos: https://litmuschaos.io/
- Chaos Mesh (Kubernetes): https://chaos-mesh.org/
- Pumba (Docker chaos): https://github.com/alexei-led/pumba
- Netflix Chaos Engineering: https://netflixtechblog.com/tagged/chaos-engineering
