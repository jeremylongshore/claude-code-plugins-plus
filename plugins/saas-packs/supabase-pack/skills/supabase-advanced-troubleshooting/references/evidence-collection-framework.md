# Evidence Collection Framework

## Evidence Collection Framework

### Comprehensive Debug Bundle

```bash
#!/bin/bash
# advanced-supabase-debug.sh

BUNDLE="supabase-advanced-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"/{logs,metrics,network,config,traces}

# 1. Extended logs (1 hour window)
kubectl logs -l app=supabase-integration --since=1h > "$BUNDLE/logs/pods.log"
journalctl -u supabase-service --since "1 hour ago" > "$BUNDLE/logs/system.log"

# 2. Metrics dump
curl -s localhost:9090/api/v1/query?query=supabase_requests_total > "$BUNDLE/metrics/requests.json"
curl -s localhost:9090/api/v1/query?query=supabase_errors_total > "$BUNDLE/metrics/errors.json"

# 3. Network capture (30 seconds)
timeout 30 tcpdump -i any port 443 -w "$BUNDLE/network/capture.pcap" &

# 4. Distributed traces
curl -s localhost:16686/api/traces?service=supabase > "$BUNDLE/traces/jaeger.json"

# 5. Configuration state
kubectl get cm supabase-config -o yaml > "$BUNDLE/config/configmap.yaml"
kubectl get secret supabase-secrets -o yaml > "$BUNDLE/config/secrets-redacted.yaml"

tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
echo "Advanced debug bundle: $BUNDLE.tar.gz"
```
