# Kubernetes Deployment

## Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: video-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: video-api
  template:
    metadata:
      labels:
        app: video-api
    spec:
      containers:
      - name: api
        image: video-platform/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_HOST
          value: redis-service
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: video-worker
spec:
  replicas: 10
  selector:
    matchLabels:
      app: video-worker
  template:
    metadata:
      labels:
        app: video-worker
    spec:
      containers:
      - name: worker
        image: video-platform/worker:latest
        env:
        - name: REDIS_HOST
          value: redis-service
        - name: KLINGAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: klingai-secrets
              key: api-key
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: video-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: video-worker
  minReplicas: 5
  maxReplicas: 50
  metrics:
  - type: External
    external:
      metric:
        name: redis_queue_length
      target:
        type: AverageValue
        averageValue: 10
```
