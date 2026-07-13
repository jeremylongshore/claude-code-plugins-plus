# Kubernetes Deployments - Implementation Details

## Configuration

### Namespace Setup

Always deploy workloads into dedicated namespaces with resource quotas:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    env: production
    team: backend
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    pods: "50"
    services: "20"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: production
spec:
  limits:
  - default:
      cpu: 500m
      memory: 512Mi
    defaultRequest:
      cpu: 100m
      memory: 256Mi
    type: Container
```

### Kustomize Project Layout

```
k8s/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── hpa.yaml
│   └── network-policy.yaml
├── overlays/
│   ├── dev/
│   │   ├── kustomization.yaml
│   │   └── patch-replicas.yaml
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   └── patch-resources.yaml
│   └── prod/
│       ├── kustomization.yaml
│       ├── patch-replicas.yaml
│       └── patch-resources.yaml
└── components/
    ├── monitoring/
    │   └── kustomization.yaml
    └── istio/
        └── kustomization.yaml
```

## Advanced Patterns

### Pod Disruption Budget

Maintain availability during voluntary disruptions (node upgrades, scaling):

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-api-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: my-api
```

### Topology Spread Constraints

Distribute pods across zones for high availability:

```yaml
spec:
  template:
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: my-api
      - maxSkew: 1
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: my-api
```

### Init Containers for Dependencies

Wait for database or external service before starting main container:

```yaml
spec:
  template:
    spec:
      initContainers:
      - name: wait-for-db
        image: busybox:1.36
        command: ['sh', '-c',
          'until nc -z postgres-svc 5432; do echo "waiting for db"; sleep 2; done']
      - name: run-migrations
        image: my-registry/my-api:v1.0.0
        command: ['npm', 'run', 'migrate']
        envFrom:
        - secretRef:
            name: db-credentials
```

### Graceful Shutdown

Configure `preStop` hooks and `terminationGracePeriodSeconds`:

```yaml
spec:
  template:
    spec:
      terminationGracePeriodSeconds: 60
      containers:
      - name: my-api
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 10"]
        # Connections drain during the sleep period
```

### Network Policy for Zero Trust

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: my-api-netpol
spec:
  podSelector:
    matchLabels:
      app: my-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - port: 8080
      protocol: TCP
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - port: 5432
      protocol: TCP
  - to:  # Allow DNS
    - namespaceSelector: {}
    ports:
    - port: 53
      protocol: UDP
```

## Troubleshooting

### Debugging Pod Scheduling

```bash
# Check why pod is pending
kubectl describe pod POD_NAME -n NAMESPACE | grep -A 10 Events

# Check node resources
kubectl top nodes
kubectl describe node NODE_NAME | grep -A 5 "Allocated resources"

# Check for taints preventing scheduling
kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, taints: .spec.taints}'
```

### Debugging CrashLoopBackOff

```bash
# Check current logs
kubectl logs POD_NAME -n NAMESPACE --tail=50

# Check previous container logs
kubectl logs POD_NAME -n NAMESPACE --previous

# Get container exit code
kubectl get pod POD_NAME -n NAMESPACE -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'

# Run shell in a debug container
kubectl debug POD_NAME -n NAMESPACE --image=busybox -it -- sh
```

### Rollback a Failed Deployment

```bash
# Check rollout history
kubectl rollout history deployment/my-api -n NAMESPACE

# Rollback to previous revision
kubectl rollout undo deployment/my-api -n NAMESPACE

# Rollback to specific revision
kubectl rollout undo deployment/my-api -n NAMESPACE --to-revision=3
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
