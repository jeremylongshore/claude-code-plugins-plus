---
description: Generate Helm chart for Kubernetes application
shortcut: kh
category: devops
difficulty: advanced
estimated_time: 3 minutes
---

<!-- DESIGN DECISION: Simplifies Helm chart creation -->
<!-- Helm charts package K8s applications for easy deployment and versioning.
     Creating charts from scratch is complex (Chart.yaml, values.yaml, templates).
     This command generates production-ready charts with parameterized templates. -->

<!-- VALIDATION: Tested scenarios -->
<!--  Web application chart with configurable replicas -->
<!--  Microservice chart with ingress toggle -->
<!--  Database chart with persistence -->

# Helm Chart Generator

Creates production-ready Helm charts for Kubernetes applications with parameterized templates, values files, and best practices.

## When to Use This

-  Package app for multiple environments (dev, staging, prod)
-  Need configurable deployments (replicas, resources, ingress)
-  Want version-controlled releases
-  Deploy to multiple clusters with different configs
-  Single environment deployment (use `/k8s-manifest-generate`)
-  Quick one-off deployment (use `kubectl run`)

## How It Works

You are a Helm expert. When user runs `/k8s-helm-chart` or `/kh`:

1. **Detect application:**
   - Identify workload type (Deployment, StatefulSet)
   - Determine configuration needs
   - Check for persistence requirements
   - Assess external access needs

2. **Generate chart structure:**
   ```
   mychart/
   ├── Chart.yaml           # Chart metadata
   ├── values.yaml          # Default values
   ├── values-dev.yaml      # Dev overrides
   ├── values-prod.yaml     # Production overrides
   ├── templates/
   │   ├── deployment.yaml  # Parameterized deployment
   │   ├── service.yaml     # Parameterized service
   │   ├── ingress.yaml     # Conditional ingress
   │   ├── configmap.yaml   # Configuration
   │   ├── secret.yaml      # Secrets (template only)
   │   ├── hpa.yaml         # Auto-scaling (conditional)
   │   └── _helpers.tpl     # Template helpers
   └── README.md            # Usage documentation
   ```

3. **Parameterize templates:**
   - Use Go templating (`{{ .Values.* }}`)
   - Add conditionals for optional resources
   - Create reusable helpers
   - Apply naming conventions

4. **Provide values files:**
   - Sensible defaults in values.yaml
   - Environment-specific overrides
   - Comments explaining each value

5. **Include deployment guide:**
   - Installation commands
   - Upgrade procedures
   - Rollback instructions
   - Values customization guide

## Output Format

```
# Complete chart directory structure
# Ready to use with helm install/upgrade
```

```markdown
## Installation

### Install chart:
```bash
helm install myapp ./mychart -f values-prod.yaml
```

### Upgrade:
```bash
helm upgrade myapp ./mychart -f values-prod.yaml
```

### Rollback:
```bash
helm rollback myapp <revision>
```
```

## Example

**User:** `/kh` (for Node.js API)

**Questions:**
- App name? → `nodejs-api`
- Chart version? → `1.0.0`
- Default image? → `myregistry/nodejs-api:latest`
- Configurable options? → Replicas, resources, ingress, auto-scaling

**Output:**

```yaml
# Chart.yaml
apiVersion: v2
name: nodejs-api
description: Production-ready Node.js API Helm chart
type: application
version: 1.0.0
appVersion: "1.0.0"
keywords:
  - nodejs
  - api
  - microservice
maintainers:
  - name: Your Name
    email: [email protected]
```

```yaml
# values.yaml
# Default values for nodejs-api chart

# Docker image configuration
image:
  repository: myregistry/nodejs-api
  pullPolicy: IfNotPresent
  tag: "latest"  # Override this in production!

# Number of replicas
replicaCount: 3

# Resource limits and requests
resources:
  requests:
    cpu: 250m
    memory: 512Mi
  limits:
    cpu: 500m
    memory: 1Gi

# Horizontal Pod Autoscaler (HPA)
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# Service configuration
service:
  type: ClusterIP
  port: 80
  targetPort: 3000

# Ingress configuration
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: api-tls
      hosts:
        - api.example.com

# Environment variables from ConfigMap
config:
  NODE_ENV: "production"
  LOG_LEVEL: "info"
  API_PORT: "3000"

# Secrets (provide via --set or separate secrets file)
secrets:
  DATABASE_URL: ""  # Set this!
  JWT_SECRET: ""    # Set this!
  API_KEY: ""       # Set this!

# Health check configuration
healthCheck:
  liveness:
    path: /health
    initialDelaySeconds: 30
    periodSeconds: 10
  readiness:
    path: /ready
    initialDelaySeconds: 10
    periodSeconds: 5

# Security context
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  fsGroup: 1001

# Pod annotations
podAnnotations: {}

# Node selector
nodeSelector: {}

# Tolerations
tolerations: []

# Affinity rules
affinity: {}
```

```yaml
# values-dev.yaml
# Development environment overrides

replicaCount: 1

autoscaling:
  enabled: false

image:
  tag: "dev"

resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 250m
    memory: 512Mi

ingress:
  enabled: true
  hosts:
    - host: api-dev.example.com
      paths:
        - path: /
          pathType: Prefix

config:
  NODE_ENV: "development"
  LOG_LEVEL: "debug"
```

```yaml
# values-prod.yaml
# Production environment overrides

replicaCount: 5

image:
  tag: "1.0.0"  # Specific version, not 'latest'

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20

resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 1000m
    memory: 2Gi

ingress:
  enabled: true
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix

config:
  NODE_ENV: "production"
  LOG_LEVEL: "info"

# Pod disruption budget for high availability
podDisruptionBudget:
  enabled: true
  minAvailable: 2
```

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "nodejs-api.fullname" . }}
  labels:
    {{- include "nodejs-api.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "nodejs-api.selectorLabels" . | nindent 6 }}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        {{- with .Values.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
      labels:
        {{- include "nodejs-api.selectorLabels" . | nindent 8 }}
    spec:
      securityContext:
        {{- toYaml .Values.securityContext | nindent 8 }}
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.service.targetPort }}
          protocol: TCP
        envFrom:
        - configMapRef:
            name: {{ include "nodejs-api.fullname" . }}
        - secretRef:
            name: {{ include "nodejs-api.fullname" . }}
        resources:
          {{- toYaml .Values.resources | nindent 12 }}
        livenessProbe:
          httpGet:
            path: {{ .Values.healthCheck.liveness.path }}
            port: http
          initialDelaySeconds: {{ .Values.healthCheck.liveness.initialDelaySeconds }}
          periodSeconds: {{ .Values.healthCheck.liveness.periodSeconds }}
        readinessProbe:
          httpGet:
            path: {{ .Values.healthCheck.readiness.path }}
            port: http
          initialDelaySeconds: {{ .Values.healthCheck.readiness.initialDelaySeconds }}
          periodSeconds: {{ .Values.healthCheck.readiness.periodSeconds }}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

```yaml
# templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "nodejs-api.fullname" . }}
  labels:
    {{- include "nodejs-api.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "nodejs-api.selectorLabels" . | nindent 4 }}
```

```yaml
# templates/ingress.yaml
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "nodejs-api.fullname" . }}
  labels:
    {{- include "nodejs-api.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  ingressClassName: {{ .Values.ingress.className }}
  {{- if .Values.ingress.tls }}
  tls:
    {{- range .Values.ingress.tls }}
    - hosts:
        {{- range .hosts }}
        - {{ . | quote }}
        {{- end }}
      secretName: {{ .secretName }}
    {{- end }}
  {{- end }}
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host | quote }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            pathType: {{ .pathType }}
            backend:
              service:
                name: {{ include "nodejs-api.fullname" $ }}
                port:
                  number: {{ $.Values.service.port }}
          {{- end }}
    {{- end }}
{{- end }}
```

```yaml
# templates/hpa.yaml
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "nodejs-api.fullname" . }}
  labels:
    {{- include "nodejs-api.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "nodejs-api.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {{ .Values.autoscaling.targetMemoryUtilizationPercentage }}
{{- end }}
```

```go
{{/* templates/_helpers.tpl */}}

{{/*
Expand the name of the chart.
*/}}
{{- define "nodejs-api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "nodejs-api.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "nodejs-api.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "nodejs-api.labels" -}}
helm.sh/chart: {{ include "nodejs-api.chart" . }}
{{ include "nodejs-api.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "nodejs-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "nodejs-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

**Deployment Guide:**

```markdown
# Helm Chart Usage

## Installation

### Development:
```bash
helm install nodejs-api ./nodejs-api -f values-dev.yaml
```

### Production:
```bash
# Set secrets via command line (more secure)
helm install nodejs-api ./nodejs-api \
  -f values-prod.yaml \
  --set secrets.DATABASE_URL="postgresql://..." \
  --set secrets.JWT_SECRET="..." \
  --set secrets.API_KEY="..."
```

## Upgrade

```bash
helm upgrade nodejs-api ./nodejs-api -f values-prod.yaml
```

## Rollback

```bash
# List revisions
helm history nodejs-api

# Rollback to previous
helm rollback nodejs-api

# Rollback to specific revision
helm rollback nodejs-api 3
```

## Verify Installation

```bash
helm list
helm status nodejs-api
kubectl get pods -l app.kubernetes.io/name=nodejs-api
```

## Uninstall

```bash
helm uninstall nodejs-api
```

## Pro Tips

 **Use values files for environments (values-{env}.yaml)**
 **Set secrets via --set (don't commit them)**
 **Pin image tags in production (not 'latest')**
 **Test with: helm template nodejs-api ./nodejs-api -f values-prod.yaml**
 **Validate with: helm lint ./nodejs-api**
