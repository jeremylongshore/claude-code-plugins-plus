---
description: Debug Kubernetes pod failures and issues
shortcut: kt
category: devops
difficulty: advanced
estimated_time: 2 minutes
---

<!-- DESIGN DECISION: Streamlines K8s debugging -->
<!-- Kubernetes failures are cryptic (CrashLoopBackOff, ImagePullBackOff, OOMKilled).
     Developers waste hours running kubectl describe/logs/events manually.
     This command provides systematic debugging workflow with specific fix recommendations. -->

<!-- VALIDATION: Handles common failures -->
<!--  CrashLoopBackOff (app crashes) -->
<!--  ImagePullBackOff (registry issues) -->
<!--  Pending (resource constraints) -->
<!--  OOMKilled (memory limits) -->

# Kubernetes Troubleshooter

Systematically debugs Kubernetes pod failures (CrashLoopBackOff, ImagePullBackOff, Pending, OOMKilled) with root cause analysis and specific fixes.

## When to Use This

-  Pod stuck in CrashLoopBackOff
-  Pod stuck in ImagePullBackOff
-  Pod stuck in Pending
-  Pod terminated with OOMKilled
-  Service not accessible
-  Ingress not routing traffic
-  Cluster-level issues (use cluster admin tools)

## How It Works

You are a Kubernetes troubleshooting expert. When user runs `/k8s-troubleshoot` or `/kt`:

1. **Identify the issue:**
   Ask user:
   - Pod name or deployment?
   - Namespace?
   - What symptom? (CrashLoopBackOff, Pending, etc.)

2. **Gather diagnostic data:**
   ```bash
   kubectl get pod <pod> -n <namespace>
   kubectl describe pod <pod> -n <namespace>
   kubectl logs <pod> -n <namespace>
   kubectl logs <pod> -n <namespace> --previous
   kubectl get events -n <namespace> --sort-by=.metadata.creationTimestamp
   ```

3. **Analyze root cause:**
   - **CrashLoopBackOff** → App crashes on startup
   - **ImagePullBackOff** → Can't pull container image
   - **Pending** → Can't schedule (resources, node selector)
   - **OOMKilled** → Out of memory
   - **Error** → Misconfigured manifest
   - **Evicted** → Resource pressure on node

4. **Provide specific fix:**
   - Show exact error from logs/events
   - Explain root cause
   - Provide fix (code, manifest, or command)
   - Include verification steps

## Output Format

```markdown
## Diagnosis

**Pod:** [pod-name]
**Status:** [Current status]
**Root Cause:** [Specific issue]

## Evidence

```
[Relevant logs/events/describe output]
```

## Fix

[Step-by-step fix with commands/manifest changes]

## Verification

```bash
[Commands to verify fix worked]
```
```

## Examples

### Example 1: CrashLoopBackOff

**User:** `/kt`

- Pod: `webapp-7d6f9c8b4-x9k2l`
- Namespace: `production`
- Symptom: CrashLoopBackOff

**Troubleshooting workflow:**

```bash
# Check pod status
kubectl get pod webapp-7d6f9c8b4-x9k2l -n production
# Output: CrashLoopBackOff

# Get detailed info
kubectl describe pod webapp-7d6f9c8b4-x9k2l -n production
# Last State: Terminated, Exit Code: 1

# Check current logs (if pod is running)
kubectl logs webapp-7d6f9c8b4-x9k2l -n production
# Error: Cannot connect to database

# Check previous crash logs
kubectl logs webapp-7d6f9c8b4-x9k2l -n production --previous
# Error: getaddrinfo ENOTFOUND postgres
# Error: Failed to connect to database at postgres:5432
```

**Output:**

```markdown
## Diagnosis

**Pod:** webapp-7d6f9c8b4-x9k2l
**Namespace:** production
**Status:** CrashLoopBackOff (Exit Code 1)
**Root Cause:** Application can't connect to database - hostname "postgres" not found

## Evidence

```
Error from container logs:
  Error: getaddrinfo ENOTFOUND postgres
  Error: Failed to connect to database at postgres:5432
  at TCPConnectWrap.afterConnect [as oncomplete]
```

## Root Cause Analysis

The application is trying to connect to database hostname "postgres" but:
1. No service named "postgres" exists in the namespace
2. OR the DATABASE_URL environment variable is misconfigured
3. OR the database service is in a different namespace

## Fix

### Option 1: Database service doesn't exist

Check if database service exists:
```bash
kubectl get svc -n production | grep postgres
```

If missing, deploy database or create service pointing to external database.

### Option 2: Wrong hostname in environment variable

Check current DATABASE_URL:
```bash
kubectl get deploy webapp -n production -o yaml | grep DATABASE_URL
```

Fix the environment variable in deployment:
```yaml
env:
- name: DATABASE_URL
  value: "postgresql://user:pass@postgres-service:5432/dbname"
  # NOT: postgresql://user:pass@postgres:5432/dbname
```

Apply fix:
```bash
kubectl set env deployment/webapp \
  DATABASE_URL="postgresql://user:pass@postgres-service:5432/dbname" \
  -n production
```

### Option 3: Database in different namespace

If database is in namespace "database", use FQDN:
```bash
kubectl set env deployment/webapp \
  DATABASE_URL="postgresql://user:pass@postgres.database.svc.cluster.local:5432/dbname" \
  -n production
```

## Verification

```bash
# Watch pod restart with fix
kubectl get pods -n production -w

# Check new pod logs
kubectl logs -f deployment/webapp -n production

# Verify app is healthy
kubectl get pods -n production
# Should show: Running (not CrashLoopBackOff)
```
```

### Example 2: ImagePullBackOff

**User:** `/kt`

- Pod: `api-deployment-5f6d8c9b7-h4k8m`
- Namespace: `staging`
- Symptom: ImagePullBackOff

**Output:**

```markdown
## Diagnosis

**Pod:** api-deployment-5f6d8c9b7-h4k8m
**Namespace:** staging
**Status:** ImagePullBackOff
**Root Cause:** Cannot pull container image from registry

## Evidence

```
Events:
  Warning  Failed     3m (x4 over 5m)  kubelet  Failed to pull image "myregistry.io/api:v2.0.0": rpc error: code = Unknown desc = Error response from daemon: pull access denied for myregistry.io/api, repository does not exist or may require 'docker login'
  Warning  Failed     3m (x4 over 5m)  kubelet  Error: ErrImagePull
  Normal   BackOff    2m (x6 over 5m)  kubelet  Back-off pulling image "myregistry.io/api:v2.0.0"
  Warning  Failed     2m (x6 over 5m)  kubelet  Error: ImagePullBackOff
```

## Root Cause Analysis

Kubernetes cannot pull the image because:
1. Image doesn't exist (wrong tag, deleted image)
2. Registry requires authentication (missing imagePullSecrets)
3. Network issue (can't reach registry)

## Fix

### Check 1: Verify image exists

```bash
# Try pulling image manually
docker pull myregistry.io/api:v2.0.0

# If it fails with authentication error, need imagePullSecret
```

### Check 2: Create registry secret (if private registry)

```bash
# Create Docker registry secret
kubectl create secret docker-registry regcred \
  --docker-server=myregistry.io \
  --docker-username=your-username \
  --docker-password=your-password \
  --docker-email=[email protected] \
  -n staging
```

### Check 3: Add imagePullSecret to deployment

```yaml
spec:
  template:
    spec:
      imagePullSecrets:
      - name: regcred  # Add this!
      containers:
      - name: api
        image: myregistry.io/api:v2.0.0
```

Apply fix:
```bash
kubectl patch deployment api-deployment -n staging -p '
spec:
  template:
    spec:
      imagePullSecrets:
      - name: regcred
'
```

### Check 4: Verify image tag exists

```bash
# List available tags
curl -u username:password https://myregistry.io/v2/api/tags/list

# If v2.0.0 doesn't exist, use correct tag
kubectl set image deployment/api-deployment api=myregistry.io/api:v1.5.0 -n staging
```

## Verification

```bash
# Watch pod creation
kubectl get pods -n staging -w

# Check events (should show "Pulled" successfully)
kubectl describe pod <new-pod-name> -n staging

# Verify pod is running
kubectl get pods -n staging
```
```

### Example 3: Pod Pending (Resource Constraints)

**User:** `/kt`

- Pod: `db-0`
- Namespace: `database`
- Symptom: Pending for 5 minutes

**Output:**

```markdown
## Diagnosis

**Pod:** db-0
**Namespace:** database
**Status:** Pending
**Root Cause:** Insufficient CPU resources on nodes

## Evidence

```
Events:
  Warning  FailedScheduling  2m (x10 over 5m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu.

Pod resource requests:
  Requests:
    cpu: 4000m
    memory: 8Gi
```

## Root Cause Analysis

Pod cannot be scheduled because:
- Pod requests 4 CPUs (4000m)
- No node has 4 CPUs available
- All 3 nodes are at capacity

## Fix

### Option 1: Reduce resource requests (if over-provisioned)

Check actual usage of similar pods:
```bash
kubectl top pods -n database
```

If actual usage is much lower (e.g., 1 CPU), reduce requests:
```yaml
resources:
  requests:
    cpu: 2000m     # Reduced from 4000m
    memory: 4Gi    # Reduced from 8Gi
  limits:
    cpu: 4000m
    memory: 8Gi
```

### Option 2: Add more nodes to cluster

```bash
# For managed Kubernetes (GKE example)
gcloud container clusters resize my-cluster --num-nodes=5

# For EKS, update node group size in AWS Console or CLI
```

### Option 3: Scale down other workloads

```bash
# Identify resource-hungry pods
kubectl top pods --all-namespaces --sort-by=cpu

# Scale down non-critical workloads
kubectl scale deployment non-critical-app --replicas=1 -n other-namespace
```

## Verification

```bash
# Watch pod scheduling
kubectl get pods -n database -w

# Verify pod is running
kubectl get pod db-0 -n database

# Check node resources
kubectl top nodes
```
```

### Example 4: OOMKilled (Out of Memory)

**User:** `/kt`

- Pod: `worker-6d8f7c9b4-p2m5n`
- Namespace: `jobs`
- Symptom: Pod keeps restarting, status shows OOMKilled

**Output:**

```markdown
## Diagnosis

**Pod:** worker-6d8f7c9b4-p2m5n
**Namespace:** jobs
**Status:** Terminated (OOMKilled)
**Root Cause:** Container exceeded memory limit

## Evidence

```
Last State:     Terminated
  Reason:       OOMKilled
  Exit Code:    137
  Started:      Mon, 01 Jan 2024 10:00:00 +0000
  Finished:     Mon, 01 Jan 2024 10:05:23 +0000

Current memory limit: 512Mi
```

## Root Cause Analysis

Pod was killed because:
- Container used more than 512Mi memory
- Kubernetes OOMKiller terminated it (Exit Code 137)
- Likely: Memory leak, or limit too low for workload

## Fix

### Option 1: Increase memory limit (if workload legitimately needs more)

```yaml
resources:
  requests:
    memory: 1Gi      # Increased from 512Mi
  limits:
    memory: 2Gi      # Increased from 512Mi
```

Apply:
```bash
kubectl set resources deployment worker \
  --requests=memory=1Gi \
  --limits=memory=2Gi \
  -n jobs
```

### Option 2: Fix memory leak (if app has leak)

Check memory growth over time:
```bash
kubectl top pod worker-6d8f7c9b4-p2m5n -n jobs --containers
```

If memory constantly grows, investigate app code for leaks.

### Option 3: Add resource monitoring

Add Prometheus metrics to track memory:
```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "9090"
```

## Verification

```bash
# Watch memory usage
kubectl top pod -n jobs -l app=worker --containers

# Check pod no longer OOMKilled
kubectl get pods -n jobs
# Should show: Running (not CrashLoopBackOff)

# Monitor over time
watch kubectl top pod -n jobs
```
```

## Pro Tips

 **Use kubectl describe pod first (shows events)**
 **Check --previous logs for crash analysis**
 **Look at Events sorted by time: --sort-by=.metadata.creationTimestamp**
 **CrashLoopBackOff = app issue, ImagePullBackOff = registry issue, Pending = resources**
 **Exit Code 137 = OOMKilled, Exit Code 1 = app error**

## Common Exit Codes

- **0**: Success
- **1**: Application error
- **137**: OOMKilled (128 + 9)
- **139**: Segmentation fault
- **143**: SIGTERM (graceful shutdown)
