---
name: creating-kubernetes-deployments
description: |
  Use when generating Kubernetes deployment manifests and services. Trigger with phrases like "create kubernetes deployment", "generate k8s manifest", "deploy app to kubernetes", or "create service and ingress". Produces production-ready YAML with health checks, auto-scaling, resource limits, ingress configuration, and TLS termination.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(kubectl:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## Prerequisites

Before using this skill, ensure:
- Kubernetes cluster is accessible and kubectl is configured
- Container image is built and pushed to registry
- Understanding of application resource requirements
- Namespace exists or will be created
- Ingress controller is installed (if using ingress)
- TLS certificates are available (if using HTTPS)

## Instructions

1. **Gather Requirements**: Application name, image, replicas, ports, environment
2. **Create Deployment**: Generate YAML with container spec and resource limits
3. **Add Health Checks**: Configure liveness and readiness probes
4. **Define Service**: Create ClusterIP, NodePort, or LoadBalancer service
5. **Configure Ingress**: Set up routing rules and TLS termination
6. **Add ConfigMaps/Secrets**: Externalize configuration and sensitive data
7. **Enable Auto-scaling**: Create HorizontalPodAutoscaler if needed
8. **Apply Manifests**: Use kubectl apply to deploy resources

## Output

**Deployment Manifest:**
```yaml
# {baseDir}/k8s/deployment.yaml


## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-web-app
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-web-app
  template:
    metadata:
      labels:
        app: my-web-app
    spec:
      containers:
      - name: app
        image: registry/my-web-app:v1.0.0
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
```

**Service and Ingress:**
```yaml
# {baseDir}/k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: my-web-app
  namespace: production
spec:
  type: ClusterIP
  selector:
    app: my-web-app
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-web-app
  namespace: production
spec:
  tls:
  - hosts:
    - app.example.com
    secretName: tls-cert
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-web-app
            port:
              number: 80
```

## Error Handling

**Image Pull Error**
- Error: "ErrImagePull" or "ImagePullBackOff"
- Solution: Verify image name, tag, and registry credentials in imagePullSecrets

**CrashLoopBackOff**
- Error: Pod repeatedly crashes and restarts
- Solution: Check application logs with `kubectl logs` and review container health

**Resource Quota Exceeded**
- Error: "forbidden: exceeded quota"
- Solution: Reduce resource requests or increase namespace quota

**Ingress Not Working**
- Error: 404 or 503 on ingress domain
- Solution: Verify ingress controller is running and service endpoints are ready

**TLS Certificate Error**
- Error: "certificate signed by unknown authority"
- Solution: Create or update TLS secret with valid certificate

## Resources

- Kubernetes documentation: https://kubernetes.io/docs/
- kubectl reference: https://kubernetes.io/docs/reference/kubectl/
- Deployment best practices: https://kubernetes.io/docs/concepts/workloads/
- Example manifests in {baseDir}/k8s-examples/