# Kubernetes Security Best Practices

Comprehensive security guidelines for production Kubernetes deployments.

## Pod Security

### Security Context Configuration

```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
```

### Security Context Checklist

| Setting | Recommended | Why |
|---------|-------------|-----|
| runAsNonRoot | true | Prevent root execution |
| allowPrivilegeEscalation | false | Block privilege escalation |
| readOnlyRootFilesystem | true | Prevent filesystem tampering |
| capabilities.drop | ALL | Remove all Linux capabilities |
| seccompProfile | RuntimeDefault | Restrict system calls |

### Handling Read-Only Filesystem

```yaml
containers:
- name: app
  securityContext:
    readOnlyRootFilesystem: true
  volumeMounts:
  - name: tmp
    mountPath: /tmp
  - name: cache
    mountPath: /app/cache
volumes:
- name: tmp
  emptyDir: {}
- name: cache
  emptyDir: {}
```

---

## Network Security

### Default Deny All Traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### Allow Specific Traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-to-db
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api
    ports:
    - protocol: TCP
      port: 5432
```

### Allow DNS (Required for Most Apps)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
```

### Network Policy Patterns

```yaml
# Allow from same namespace only
ingress:
- from:
  - podSelector: {}

# Allow from specific namespace
ingress:
- from:
  - namespaceSelector:
      matchLabels:
        name: frontend

# Allow from IP range
ingress:
- from:
  - ipBlock:
      cidr: 10.0.0.0/8
      except:
      - 10.0.1.0/24
```

---

## RBAC (Role-Based Access Control)

### Principle of Least Privilege

```yaml
# Create dedicated ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app
  namespace: production
---
# Define minimal Role
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: my-app-role
  namespace: production
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["my-app-config"]  # Specific resource
  verbs: ["get", "watch"]           # Read-only
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["my-app-secrets"]
  verbs: ["get"]
---
# Bind Role to ServiceAccount
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-app-binding
  namespace: production
subjects:
- kind: ServiceAccount
  name: my-app
  namespace: production
roleRef:
  kind: Role
  name: my-app-role
  apiGroup: rbac.authorization.k8s.io
```

### Use ServiceAccount in Pod

```yaml
spec:
  serviceAccountName: my-app
  automountServiceAccountToken: false  # Unless needed
```

### Common RBAC Verbs

| Verb | Description |
|------|-------------|
| get | Read single resource |
| list | Read collection |
| watch | Watch for changes |
| create | Create resource |
| update | Update existing resource |
| patch | Partial update |
| delete | Delete resource |
| deletecollection | Delete collection |

---

## Secrets Management

### Don't Store Secrets in Code

```yaml
# Bad - hardcoded secret
env:
- name: DB_PASSWORD
  value: "mysecretpassword"

# Good - reference Secret
env:
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: db-credentials
      key: password
```

### Mount Secrets as Files (More Secure)

```yaml
volumeMounts:
- name: secrets
  mountPath: /etc/secrets
  readOnly: true
volumes:
- name: secrets
  secret:
    secretName: my-secrets
    defaultMode: 0400  # Read-only for owner
```

### External Secrets Management

```yaml
# Using External Secrets Operator
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: my-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: my-secret
  data:
  - secretKey: password
    remoteRef:
      key: secret/data/myapp
      property: password
```

### Secrets Best Practices

1. **Enable encryption at rest:**

   ```yaml
   # kube-apiserver config
   --encryption-provider-config=/etc/kubernetes/encryption-config.yaml
   ```

2. **Rotate secrets regularly:**
   - Implement automatic rotation
   - Use short-lived credentials

3. **Audit secret access:**
   - Enable Kubernetes audit logging
   - Monitor secret read events

---

## Image Security

### Use Trusted Base Images

```dockerfile
# Good - official minimal image
FROM gcr.io/distroless/static-debian11

# Good - specific version
FROM python:3.11-slim-bookworm

# Bad - unverified image
FROM random-user/my-image
```

### Scan Images for Vulnerabilities

```bash
# Using trivy
trivy image my-registry.io/my-app:v1.0.0

# Using grype
grype my-registry.io/my-app:v1.0.0
```

### Image Pull Policies

```yaml
# Enforce image verification
spec:
  containers:
  - name: app
    image: my-registry.io/my-app@sha256:abc123...  # Use digest
    imagePullPolicy: Always  # Always verify
```

### Admission Control for Images

```yaml
# Kyverno policy example
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-signed-images
spec:
  validationFailureAction: Enforce
  rules:
  - name: verify-image
    match:
      resources:
        kinds:
        - Pod
    verifyImages:
    - image: "my-registry.io/*"
      key: |-
        -----BEGIN PUBLIC KEY-----
        ...
        -----END PUBLIC KEY-----
```

---

## Resource Limits (Security Aspect)

### Prevent Resource Exhaustion

```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
    ephemeral-storage: 1Gi
```

### LimitRange for Namespace

```yaml
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
    max:
      cpu: 2
      memory: 4Gi
    type: Container
```

### ResourceQuota for Namespace

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: namespace-quota
  namespace: production
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "50"
    secrets: "20"
```

---

## Audit Logging

### Enable Kubernetes Audit

```yaml
# /etc/kubernetes/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
# Log pod exec and attach
- level: RequestResponse
  resources:
  - group: ""
    resources: ["pods/exec", "pods/attach"]

# Log secret access
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets"]

# Log authentication
- level: Metadata
  users: ["system:anonymous"]
  verbs: ["get", "list"]
```

### Key Events to Monitor

| Event | Why Monitor |
|-------|-------------|
| pod/exec | Potential container escape |
| secrets access | Credential theft |
| RBAC changes | Privilege escalation |
| Failed auth | Brute force attempts |
| Resource creation | Unauthorized workloads |

---

## Pod Security Standards

### Restricted (Recommended for Production)

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted
```

### Security Standard Comparison

| Feature | Privileged | Baseline | Restricted |
|---------|------------|----------|------------|
| Host namespaces | Allowed | Forbidden | Forbidden |
| Privileged containers | Allowed | Forbidden | Forbidden |
| Capabilities | All | Drop some | Drop ALL |
| Host paths | Allowed | Forbidden | Forbidden |
| Host ports | Allowed | Some | Forbidden |
| Root user | Allowed | Allowed | Forbidden |
| Privilege escalation | Allowed | Allowed | Forbidden |
| Seccomp | None | None | Required |

---

## Security Checklist

### Pod Level

- [ ] runAsNonRoot: true
- [ ] allowPrivilegeEscalation: false
- [ ] readOnlyRootFilesystem: true
- [ ] capabilities.drop: ALL
- [ ] seccompProfile: RuntimeDefault
- [ ] ServiceAccount with minimal permissions
- [ ] automountServiceAccountToken: false (if not needed)

### Network Level

- [ ] Default deny NetworkPolicy
- [ ] Explicit allow policies only for required traffic
- [ ] Ingress TLS configured
- [ ] No hostNetwork: true

### Secrets

- [ ] No secrets in environment variables (use files)
- [ ] Secrets encrypted at rest
- [ ] External secrets manager integration
- [ ] Regular rotation

### Images

- [ ] Specific image tags (not :latest)
- [ ] Image digest verification
- [ ] Vulnerability scanning
- [ ] Trusted registry only

### Cluster Level

- [ ] RBAC enabled
- [ ] Audit logging enabled
- [ ] Pod Security Standards enforced
- [ ] Resource quotas set
