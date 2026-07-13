# Kubernetes Error Handling Reference

Comprehensive guide to troubleshooting common Kubernetes deployment errors.

## Pod Status Errors

### ImagePullBackOff / ErrImagePull

**Symptoms:**

- Pod stuck in `ImagePullBackOff` or `ErrImagePull` status
- Events show "Failed to pull image"

**Causes:**

- Image name or tag typo
- Image doesn't exist in registry
- Missing or invalid registry credentials
- Private registry without imagePullSecrets

**Diagnosis:**

```bash
kubectl describe pod <pod-name> | grep -A 10 Events
kubectl get events --field-selector reason=Failed
```

**Solutions:**

```yaml
# 1. Verify image exists
docker pull <image-name>:<tag>

# 2. Add imagePullSecrets for private registries
spec:
  imagePullSecrets:
  - name: registry-credentials
  containers:
  - name: app
    image: private-registry.io/app:v1.0.0

# 3. Create registry secret
kubectl create secret docker-registry registry-credentials \
  --docker-server=private-registry.io \
  --docker-username=user \
  --docker-password=pass
```

---

### CrashLoopBackOff

**Symptoms:**

- Pod repeatedly crashes and restarts
- Status cycles between `Running` and `CrashLoopBackOff`
- Restart count keeps increasing

**Causes:**

- Application crashes on startup
- Missing environment variables or config
- Failing health checks
- Insufficient resources (OOMKilled)
- Permission issues

**Diagnosis:**

```bash
# Check pod logs
kubectl logs <pod-name> --previous

# Check events
kubectl describe pod <pod-name>

# Check container exit code
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'
```

**Solutions:**

```bash
# 1. Fix application errors shown in logs
kubectl logs <pod-name> --previous

# 2. Increase initialDelaySeconds for slow-starting apps
livenessProbe:
  initialDelaySeconds: 60  # Give app more time

# 3. Add startup probe for very slow apps
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
```

---

### OOMKilled

**Symptoms:**

- Pod killed with reason `OOMKilled`
- Exit code 137

**Causes:**

- Application uses more memory than `limits.memory`
- Memory leak in application
- Limits set too low

**Diagnosis:**

```bash
kubectl describe pod <pod-name> | grep -A 5 "Last State"
kubectl top pod <pod-name>
```

**Solutions:**

```yaml
# Increase memory limits
resources:
  requests:
    memory: 512Mi
  limits:
    memory: 1Gi  # Increase this

# Or fix the memory leak in your application
```

---

### Pending (Unschedulable)

**Symptoms:**

- Pod stuck in `Pending` status
- Events show "Insufficient cpu" or "Insufficient memory"

**Causes:**

- Insufficient cluster resources
- Node selector/affinity not satisfied
- Taints and tolerations mismatch
- PersistentVolumeClaim not bound

**Diagnosis:**

```bash
kubectl describe pod <pod-name> | grep -A 10 Events
kubectl get nodes -o wide
kubectl describe nodes | grep -A 5 "Allocated resources"
```

**Solutions:**

```yaml
# 1. Reduce resource requests
resources:
  requests:
    cpu: 100m     # Lower this
    memory: 256Mi # Lower this

# 2. Add node affinity for specific nodes
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: node-type
          operator: In
          values:
          - compute

# 3. Add toleration for tainted nodes
tolerations:
- key: "dedicated"
  operator: "Equal"
  value: "special"
  effect: "NoSchedule"
```

---

### CreateContainerConfigError

**Symptoms:**

- Pod in `CreateContainerConfigError` status
- Events show "Error: configmap/secret not found"

**Causes:**

- Referenced ConfigMap doesn't exist
- Referenced Secret doesn't exist
- Incorrect ConfigMap/Secret name

**Diagnosis:**

```bash
kubectl describe pod <pod-name>
kubectl get configmap
kubectl get secret
```

**Solutions:**

```bash
# 1. Verify ConfigMap exists
kubectl get configmap <name>

# 2. Create missing ConfigMap
kubectl create configmap my-config --from-literal=KEY=value

# 3. Verify Secret exists
kubectl get secret <name>

# 4. Create missing Secret
kubectl create secret generic my-secret --from-literal=PASSWORD=secret
```

---

## Service/Networking Errors

### Service Has No Endpoints

**Symptoms:**

- Service returns connection refused or timeout
- `kubectl get endpoints` shows no addresses

**Causes:**

- No pods match the Service selector
- Pods not ready (failing readiness probe)
- Selector label mismatch

**Diagnosis:**

```bash
kubectl get endpoints <service-name>
kubectl get pods -l <selector-labels>
kubectl describe service <service-name>
```

**Solutions:**

```yaml
# 1. Verify selector matches pod labels
# Service:
spec:
  selector:
    app: my-api  # Must match pod labels

# Pod:
metadata:
  labels:
    app: my-api  # Must match service selector

# 2. Fix failing readiness probes
readinessProbe:
  httpGet:
    path: /healthz  # Verify this endpoint returns 200
    port: 8080
```

---

### Ingress 404 / 502 / 503 Errors

**Symptoms:**

- 404: Ingress rule not matching
- 502: Backend service not responding
- 503: No available backends

**Causes:**

- Incorrect Ingress path or host
- Service not available
- Backend pods not ready
- Ingress controller not installed

**Diagnosis:**

```bash
kubectl describe ingress <ingress-name>
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

**Solutions:**

```yaml
# 1. Verify Ingress class is correct
spec:
  ingressClassName: nginx  # Must match installed controller

# 2. Verify backend service exists and has endpoints
kubectl get svc <service-name>
kubectl get endpoints <service-name>

# 3. Check path and pathType
rules:
- host: api.example.com
  http:
    paths:
    - path: /
      pathType: Prefix  # Use Prefix for catch-all
      backend:
        service:
          name: my-api
          port:
            number: 80
```

---

### TLS Certificate Errors

**Symptoms:**

- "certificate signed by unknown authority"
- "certificate has expired"
- Browser shows certificate warning

**Causes:**

- Self-signed certificate
- Expired certificate
- Wrong certificate for domain
- Secret doesn't contain valid TLS data

**Diagnosis:**

```bash
kubectl get secret <tls-secret> -o yaml
openssl x509 -in <cert-file> -text -noout
kubectl describe certificate <cert-name>  # If using cert-manager
```

**Solutions:**

```bash
# 1. Create valid TLS secret
kubectl create secret tls my-tls \
  --cert=tls.crt \
  --key=tls.key

# 2. Use cert-manager for automatic certificates
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# Create ClusterIssuer
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

---

## Resource Quota Errors

### Forbidden: Exceeded Quota

**Symptoms:**

- Deployment fails with "forbidden: exceeded quota"
- Cannot create new pods or services

**Causes:**

- Namespace resource quota exceeded
- Limit range constraints

**Diagnosis:**

```bash
kubectl describe resourcequota -n <namespace>
kubectl describe limitrange -n <namespace>
kubectl get quota -n <namespace>
```

**Solutions:**

```bash
# 1. Check current quota usage
kubectl describe resourcequota -n my-namespace

# 2. Request quota increase from admin
kubectl edit resourcequota <quota-name> -n <namespace>

# 3. Reduce resource requests in deployments
resources:
  requests:
    cpu: 100m     # Lower this
    memory: 256Mi # Lower this
```

---

## PersistentVolume Errors

### PVC Pending (Unbound)

**Symptoms:**

- PersistentVolumeClaim stuck in `Pending`
- Events show "no persistent volumes available"

**Causes:**

- No matching PersistentVolume
- Storage class doesn't exist
- Insufficient storage capacity
- Access mode mismatch

**Diagnosis:**

```bash
kubectl describe pvc <pvc-name>
kubectl get pv
kubectl get storageclass
```

**Solutions:**

```yaml
# 1. Verify StorageClass exists
kubectl get storageclass

# 2. Use correct storage class
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: standard  # Must exist
  resources:
    requests:
      storage: 10Gi

# 3. Create StorageClass if needed (GKE example)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
```

---

## RBAC Errors

### Forbidden: User Cannot Get/List/Create

**Symptoms:**

- "Error from server (Forbidden)"
- "User cannot get/list/create resource"

**Causes:**

- Missing RBAC permissions
- Wrong ServiceAccount
- ClusterRole/Role not bound

**Diagnosis:**

```bash
kubectl auth can-i <verb> <resource> --as=system:serviceaccount:<ns>:<sa>
kubectl get rolebinding,clusterrolebinding -A | grep <service-account>
```

**Solutions:**

```yaml
# 1. Create ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app
  namespace: default

# 2. Create Role with needed permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: my-app-role
  namespace: default
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list", "watch"]

# 3. Bind Role to ServiceAccount
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-app-binding
  namespace: default
subjects:
- kind: ServiceAccount
  name: my-app
  namespace: default
roleRef:
  kind: Role
  name: my-app-role
  apiGroup: rbac.authorization.k8s.io
```

---

## Deployment Errors

### Deployment Rollout Stuck

**Symptoms:**

- `kubectl rollout status` hangs
- Deployment shows fewer ready replicas than desired

**Causes:**

- New pods failing health checks
- Resource constraints
- Image pull issues

**Diagnosis:**

```bash
kubectl rollout status deployment/<name>
kubectl get pods -l app=<name>
kubectl describe deployment <name>
```

**Solutions:**

```bash
# 1. Check rollout status
kubectl rollout status deployment/my-app

# 2. Rollback if needed
kubectl rollout undo deployment/my-app

# 3. Check pod events
kubectl describe pod <new-pod-name>

# 4. Adjust rollout strategy
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0    # Don't remove old pods until new ready
      maxSurge: 1          # Add one pod at a time
```

---

## Node Issues

### NodeNotReady

**Symptoms:**

- Node in `NotReady` status
- Pods evicted or stuck in `Terminating`

**Causes:**

- Node resource exhaustion
- Kubelet crashed
- Network connectivity issues
- Disk pressure

**Diagnosis:**

```bash
kubectl describe node <node-name>
kubectl get events --field-selector involvedObject.kind=Node
```

**Solutions:**

```bash
# 1. Check node conditions
kubectl describe node <node-name> | grep -A 10 Conditions

# 2. Cordon and drain if needed
kubectl cordon <node-name>
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# 3. Check kubelet logs (on the node)
journalctl -u kubelet -f
```

---

## Quick Reference: Exit Codes

| Exit Code | Meaning | Common Cause |
|-----------|---------|--------------|
| 0 | Success | Application exited normally |
| 1 | General error | Application error |
| 126 | Permission denied | Cannot execute command |
| 127 | Command not found | Missing binary |
| 137 | SIGKILL (OOMKilled) | Memory limit exceeded |
| 139 | SIGSEGV | Segmentation fault |
| 143 | SIGTERM | Graceful termination |

## Quick Reference: Pod States

| State | Description | Action |
|-------|-------------|--------|
| Pending | Waiting to be scheduled | Check resources, node selector |
| ContainerCreating | Pulling image, mounting volumes | Wait or check events |
| Running | Container executing | Check health probes |
| Succeeded | Container completed (Job) | Normal for Jobs |
| Failed | Container exited with error | Check logs |
| Unknown | Node communication lost | Check node status |
| CrashLoopBackOff | Repeated crashes | Check logs, increase probe delays |
| ImagePullBackOff | Cannot pull image | Check image name, credentials |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
