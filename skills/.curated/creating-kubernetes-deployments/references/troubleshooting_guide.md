# Kubernetes Troubleshooting Guide

Systematic approach to diagnosing and resolving Kubernetes issues.

## Troubleshooting Framework

```
1. Identify the symptom
2. Check resource status
3. Examine events
4. Review logs
5. Verify configuration
6. Test connectivity
7. Apply fix
8. Verify resolution
```

---

## Quick Diagnostic Commands

### Cluster Health

```bash
# Overall cluster status
kubectl cluster-info
kubectl get componentstatuses
kubectl get nodes

# Check for issues
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl top nodes
kubectl top pods -A
```

### Resource Status

```bash
# All resources in namespace
kubectl get all -n <namespace>

# Detailed pod status
kubectl get pods -o wide
kubectl describe pod <pod-name>

# Watch resources
kubectl get pods -w
```

### Logs

```bash
# Pod logs
kubectl logs <pod-name>
kubectl logs <pod-name> -c <container>
kubectl logs <pod-name> --previous
kubectl logs <pod-name> -f --tail=100

# Multiple pods
kubectl logs -l app=my-app --all-containers
```

---

## Pod Not Starting

### Symptom: Pod Stuck in Pending

**Check scheduling constraints:**

```bash
kubectl describe pod <pod-name> | grep -A 20 Events
kubectl get nodes -o wide
kubectl describe nodes | grep -A 10 "Allocated resources"
```

**Common causes:**

1. **Insufficient resources:** Lower requests or add nodes
2. **Node selector mismatch:** Check nodeSelector/affinity
3. **Taint not tolerated:** Add toleration
4. **PVC not bound:** Check PersistentVolumeClaim

**Fix insufficient resources:**

```yaml
resources:
  requests:
    cpu: 100m      # Lower this
    memory: 256Mi  # Lower this
```

### Symptom: ImagePullBackOff

**Check image issues:**

```bash
kubectl describe pod <pod-name> | grep -A 5 "Events"
kubectl get events --field-selector reason=Failed
```

**Common causes:**

1. **Wrong image name/tag:** Verify image exists
2. **Private registry:** Add imagePullSecrets
3. **Rate limiting:** Use authenticated pulls

**Fix with imagePullSecrets:**

```yaml
spec:
  imagePullSecrets:
  - name: my-registry-secret
```

### Symptom: CrashLoopBackOff

**Check application issues:**

```bash
kubectl logs <pod-name> --previous
kubectl describe pod <pod-name>
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[0].lastState}'
```

**Common causes:**

1. **Application error:** Check logs
2. **Missing config:** Verify ConfigMap/Secret exists
3. **Health check failing too early:** Increase initialDelaySeconds
4. **OOMKilled:** Increase memory limits

**Fix health check timing:**

```yaml
livenessProbe:
  initialDelaySeconds: 60  # Increase for slow apps
startupProbe:              # Add startup probe
  failureThreshold: 30
  periodSeconds: 10
```

### Symptom: CreateContainerConfigError

**Check config references:**

```bash
kubectl describe pod <pod-name>
kubectl get configmap -n <namespace>
kubectl get secret -n <namespace>
```

**Fix:**

```bash
# Create missing ConfigMap
kubectl create configmap my-config --from-literal=KEY=value

# Create missing Secret
kubectl create secret generic my-secret --from-literal=PASSWORD=secret
```

---

## Application Not Responding

### Symptom: Service Returns No Response

**Check service and endpoints:**

```bash
kubectl get svc <service-name>
kubectl get endpoints <service-name>
kubectl describe svc <service-name>
```

**Common causes:**

1. **No endpoints:** Pod selector doesn't match
2. **Wrong port:** Service port doesn't match container port
3. **Pods not ready:** Failing readiness probe

**Debug connectivity:**

```bash
# Test from within cluster
kubectl run debug --rm -it --image=busybox -- wget -qO- http://<service-name>:<port>

# Port forward to test locally
kubectl port-forward svc/<service-name> 8080:80
curl localhost:8080
```

### Symptom: Ingress Returns 404/502/503

**Check ingress configuration:**

```bash
kubectl describe ingress <ingress-name>
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

**Troubleshooting steps:**

1. Verify ingress class matches controller
2. Check backend service exists and has endpoints
3. Verify host and path configuration
4. Check TLS secret (if using HTTPS)

```bash
# Check ingress controller logs
kubectl logs -n ingress-nginx deploy/ingress-nginx-controller --tail=100

# Verify service has endpoints
kubectl get endpoints <backend-service>
```

### Symptom: Intermittent Timeouts

**Check resource issues:**

```bash
kubectl top pods
kubectl describe pod <pod-name> | grep -A 5 "Containers"
kubectl get hpa
```

**Common causes:**

1. **CPU throttling:** Increase CPU limits
2. **Memory pressure:** Check for OOMKilled
3. **Network policy blocking:** Check NetworkPolicy
4. **Connection pool exhaustion:** Check application config

---

## Deployment Issues

### Symptom: Rollout Stuck

**Check rollout status:**

```bash
kubectl rollout status deployment/<name>
kubectl get replicaset
kubectl describe deployment <name>
```

**Common causes:**

1. **New pods failing:** Check new pod logs
2. **Insufficient resources:** Check node capacity
3. **Image pull failure:** Verify image exists

**Recovery options:**

```bash
# Rollback to previous version
kubectl rollout undo deployment/<name>

# Rollback to specific revision
kubectl rollout history deployment/<name>
kubectl rollout undo deployment/<name> --to-revision=2

# Pause rollout for debugging
kubectl rollout pause deployment/<name>
```

### Symptom: Pods Evicted

**Check eviction reasons:**

```bash
kubectl get pods --field-selector=status.phase=Failed
kubectl describe pod <evicted-pod>
kubectl describe node <node-name> | grep -A 10 Conditions
```

**Common causes:**

1. **Node pressure (disk/memory):** Clean up or add resources
2. **PriorityClass preemption:** Higher priority pod scheduled
3. **Taints added:** Add toleration or move workload

---

## Storage Issues

### Symptom: PVC Stuck in Pending

**Check PVC status:**

```bash
kubectl describe pvc <pvc-name>
kubectl get storageclass
kubectl get pv
```

**Common causes:**

1. **No matching PV:** Create PV or use dynamic provisioning
2. **StorageClass doesn't exist:** Create or use existing class
3. **Access mode mismatch:** Verify access modes
4. **Insufficient capacity:** Request less storage

**Debug:**

```bash
# Check storage provisioner logs
kubectl logs -n kube-system -l app=ebs-csi-controller
```

### Symptom: Volume Mount Failed

**Check mount issues:**

```bash
kubectl describe pod <pod-name> | grep -A 10 "Events"
kubectl get pv,pvc
```

**Common causes:**

1. **PV not available:** Check PV status
2. **Node doesn't have access:** Check node selectors
3. **FS corruption:** Check node logs

---

## Network Issues

### Symptom: DNS Not Resolving

**Test DNS:**

```bash
kubectl run dns-test --rm -it --image=busybox -- nslookup kubernetes.default

kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns
```

**Common causes:**

1. **CoreDNS pods not running:** Check kube-system
2. **NetworkPolicy blocking DNS:** Allow UDP/TCP 53 to kube-dns
3. **Node DNS configuration:** Check /etc/resolv.conf

### Symptom: Cross-Namespace Communication Failed

**Check NetworkPolicy:**

```bash
kubectl get networkpolicy -A
kubectl describe networkpolicy <policy-name>
```

**Debug:**

```bash
# Test from source pod
kubectl exec -it <source-pod> -- nc -zv <target-service>.<target-namespace>.svc.cluster.local <port>
```

---

## Performance Issues

### Symptom: High Latency

**Check resource utilization:**

```bash
kubectl top pods
kubectl top nodes
kubectl describe pod <pod-name> | grep -A 10 "Limits"
```

**Common causes:**

1. **CPU throttling:** Increase CPU limits
2. **Insufficient replicas:** Scale up
3. **Network latency:** Check node placement
4. **Slow dependencies:** Profile application

### Symptom: OOMKilled

**Check memory usage:**

```bash
kubectl describe pod <pod-name> | grep -A 5 "Last State"
kubectl top pod <pod-name>
```

**Fix:**

```yaml
resources:
  limits:
    memory: 1Gi  # Increase based on actual usage
```

---

## Useful Debug Commands

### Interactive Debugging

```bash
# Exec into running container
kubectl exec -it <pod-name> -- /bin/sh

# Debug with ephemeral container
kubectl debug <pod-name> -it --image=busybox

# Create debug pod in same namespace
kubectl run debug --rm -it --image=nicolaka/netshoot -- /bin/bash
```

### Network Debugging

```bash
# Check connectivity
kubectl run test --rm -it --image=busybox -- wget -qO- http://service:port

# Check DNS
kubectl run test --rm -it --image=busybox -- nslookup service.namespace

# Check ports
kubectl run test --rm -it --image=busybox -- nc -zv host port
```

### Resource Inspection

```bash
# Get YAML
kubectl get pod <name> -o yaml

# Get specific field
kubectl get pod <name> -o jsonpath='{.status.phase}'

# Compare resources
kubectl diff -f manifest.yaml
```

---

## Quick Reference: Error to Solution

| Error | First Check | Likely Solution |
|-------|-------------|-----------------|
| Pending | `kubectl describe pod` | Reduce resources, fix PVC |
| ImagePullBackOff | Image name, registry | Fix image, add pullSecrets |
| CrashLoopBackOff | `kubectl logs --previous` | Fix app, increase probes |
| OOMKilled | Memory limits | Increase memory limit |
| CreateContainerConfigError | ConfigMap/Secret | Create missing config |
| No endpoints | Service selector | Fix label mismatch |
| Ingress 404 | Backend service | Verify service exists |
| PVC Pending | StorageClass | Fix storage class |
| DNS failure | kube-dns pods | Check NetworkPolicy |

---

## Escalation Checklist

Before escalating:

- [ ] Collected `kubectl describe` output
- [ ] Gathered relevant logs
- [ ] Checked events in namespace
- [ ] Verified resource configuration
- [ ] Tested network connectivity
- [ ] Documented reproduction steps
- [ ] Noted cluster/node versions
