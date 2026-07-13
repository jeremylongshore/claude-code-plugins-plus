# TwinMind Deploy Integration - Detailed Implementation

## Dockerfile

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
RUN addgroup -g 1001 -S nodejs && adduser -S twinmind -u 1001 -G nodejs
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
USER twinmind
ENV NODE_ENV=production PORT=8080
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1
CMD ["node", "dist/index.js"]
```

## Docker Compose

```yaml
version: '3.8'
services:
  twinmind-service:
    build: .
    ports: ["8080:8080"]
    environment:
      - NODE_ENV=production
      - TWINMIND_API_KEY=${TWINMIND_API_KEY}
      - TWINMIND_WEBHOOK_SECRET=${TWINMIND_WEBHOOK_SECRET}
    deploy:
      replicas: 2
      resources:
        limits: { cpus: '1', memory: 512M }
    logging:
      driver: "json-file"
      options: { max-size: "10m", max-file: "3" }
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

## AWS ECS/Fargate (Terraform)

```hcl
resource "aws_secretsmanager_secret" "twinmind" {
  name = "twinmind-api-credentials"
}

resource "aws_ecs_cluster" "main" {
  name = "twinmind-cluster"
  setting { name = "containerInsights"; value = "enabled" }
}

resource "aws_ecs_task_definition" "twinmind" {
  family                   = "twinmind-service"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024

  container_definitions = jsonencode([{
    name  = "twinmind"
    image = "${aws_ecr_repository.twinmind.repository_url}:latest"
    portMappings = [{ containerPort = 8080, protocol = "tcp" }]
    secrets = [
      { name = "TWINMIND_API_KEY", valueFrom = "${aws_secretsmanager_secret.twinmind.arn}:api_key::" }
    ]
    healthCheck = { command = ["CMD-SHELL", "wget -q --spider http://localhost:8080/health || exit 1"] }
  }])
}

resource "aws_ecs_service" "twinmind" {
  name            = "twinmind-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.twinmind.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  deployment_circuit_breaker { enable = true; rollback = true }
}

resource "aws_appautoscaling_policy" "cpu" {
  name        = "cpu-autoscaling"
  policy_type = "TargetTrackingScaling"
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification { predefined_metric_type = "ECSServiceAverageCPUUtilization" }
    target_value = 70.0
  }
}
```

## GCP Cloud Run (Terraform)

```hcl
resource "google_cloud_run_v2_service" "twinmind" {
  name     = "twinmind-service"
  location = var.region
  template {
    scaling { min_instance_count = 1; max_instance_count = 10 }
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/twinmind/service:latest"
      ports { container_port = 8080 }
      env { name = "TWINMIND_API_KEY"; value_source { secret_key_ref { secret = "twinmind-api-key"; version = "latest" } } }
      resources { limits = { cpu = "1"; memory = "512Mi" } }
      startup_probe { http_get { path = "/health"; port = 8080 } }
      liveness_probe { http_get { path = "/health"; port = 8080 }; period_seconds = 30 }
    }
  }
}
```

## Kubernetes Manifests

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: twinmind-service }
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: twinmind
          image: your-registry/twinmind:latest
          ports: [{ containerPort: 8080 }]
          env:
            - { name: TWINMIND_API_KEY, valueFrom: { secretKeyRef: { name: twinmind-secrets, key: api-key } } }
          resources:
            requests: { cpu: 250m, memory: 256Mi }
            limits: { cpu: 1000m, memory: 512Mi }
          readinessProbe: { httpGet: { path: /health, port: 8080 }, initialDelaySeconds: 10 }
          livenessProbe: { httpGet: { path: /health, port: 8080 }, initialDelaySeconds: 30 }
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: twinmind-service }
  minReplicas: 2
  maxReplicas: 10
  metrics: [{ type: Resource, resource: { name: cpu, target: { type: Utilization, averageUtilization: 70 } } }]
```

## GitHub Actions Deploy

```yaml
name: Deploy
on:
  push: { branches: [main], tags: ['v*'] }

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
      - uses: aws-actions/amazon-ecr-login@v2
      - run: docker build -t $REGISTRY/$REPO:${{ github.sha }} . && docker push $REGISTRY/$REPO:${{ github.sha }}

  deploy-staging:
    needs: build-and-push
    environment: staging
    steps:
      - run: aws ecs update-service --cluster twinmind-staging --service twinmind-service --force-new-deployment
      - run: aws ecs wait services-stable --cluster twinmind-staging --services twinmind-service

  deploy-production:
    needs: deploy-staging
    environment: production
    steps:
      - run: aws ecs update-service --cluster twinmind-production --service twinmind-service --force-new-deployment
      - run: aws ecs wait services-stable --cluster twinmind-production --services twinmind-service
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
