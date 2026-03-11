# Evernote Deploy Integration - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Docker Deployment

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

RUN npm run build --if-present

FROM node:20-alpine AS production

WORKDIR /app

RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist
COPY --from=builder --chown=appuser:appgroup /app/package.json ./

USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

EXPOSE 3000

CMD ["node", "dist/index.js"]
```

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - EVERNOTE_CONSUMER_KEY=${EVERNOTE_CONSUMER_KEY}
      - EVERNOTE_CONSUMER_SECRET=${EVERNOTE_CONSUMER_SECRET}
      - EVERNOTE_SANDBOX=false
      - SESSION_SECRET=${SESSION_SECRET}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    restart: unless-stopped

volumes:
  redis-data:
```

### Step 2: AWS Deployment (ECS/Fargate)

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Evernote Integration Service

Parameters:
  Environment:
    Type: String
    AllowedValues: [staging, production]

  EvernoteConsumerKey:
    Type: String
    NoEcho: true

  EvernoteConsumerSecret:
    Type: String
    NoEcho: true

Resources:
  # ECS Cluster
  Cluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: !Sub evernote-${Environment}

  # Task Definition
  TaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: !Sub evernote-app-${Environment}
      Cpu: '256'
      Memory: '512'
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
      ExecutionRoleArn: !GetAtt ExecutionRole.Arn
      TaskRoleArn: !GetAtt TaskRole.Arn
      ContainerDefinitions:
        - Name: app
          Image: !Sub ${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/evernote-app:latest
          PortMappings:
            - ContainerPort: 3000
          Environment:
            - Name: NODE_ENV
              Value: production
            - Name: EVERNOTE_SANDBOX
              Value: 'false'
          Secrets:
            - Name: EVERNOTE_CONSUMER_KEY
              ValueFrom: !Ref ConsumerKeySecret
            - Name: EVERNOTE_CONSUMER_SECRET
              ValueFrom: !Ref ConsumerSecretSecret
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-group: !Ref LogGroup
              awslogs-region: !Ref AWS::Region
              awslogs-stream-prefix: ecs
          HealthCheck:
            Command:
              - CMD-SHELL
              - wget -q --spider http://localhost:3000/health || exit 1
            Interval: 30
            Timeout: 5
            Retries: 3
            StartPeriod: 60

  # Secrets Manager
  ConsumerKeySecret:
    Type: AWS::SecretsManager::Secret
    Properties:
      Name: !Sub /evernote/${Environment}/consumer-key
      SecretString: !Ref EvernoteConsumerKey

  ConsumerSecretSecret:
    Type: AWS::SecretsManager::Secret
    Properties:
      Name: !Sub /evernote/${Environment}/consumer-secret
      SecretString: !Ref EvernoteConsumerSecret

  # ECS Service
  Service:
    Type: AWS::ECS::Service
    Properties:
      Cluster: !Ref Cluster
      ServiceName: !Sub evernote-app-${Environment}
      TaskDefinition: !Ref TaskDefinition
      DesiredCount: 2
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          AssignPublicIp: ENABLED
          SecurityGroups:
            - !Ref SecurityGroup
          Subnets:
            - !Ref PublicSubnet1
            - !Ref PublicSubnet2
      LoadBalancers:
        - ContainerName: app
          ContainerPort: 3000
          TargetGroupArn: !Ref TargetGroup

  # Application Load Balancer
  LoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: !Sub evernote-alb-${Environment}
      Scheme: internet-facing
      Type: application
      SecurityGroups:
        - !Ref ALBSecurityGroup
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2

  # CloudWatch Logs
  LogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub /ecs/evernote-app-${Environment}
      RetentionInDays: 30
```

### Step 3: GitHub Actions Deployment

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: evernote-app
  ECS_SERVICE: evernote-app-production
  ECS_CLUSTER: evernote-production

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:latest .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service $ECS_SERVICE \
            --force-new-deployment

      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster $ECS_CLUSTER \
            --services $ECS_SERVICE

      - name: Notify deployment
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Evernote Integration deployed: ${{ job.status }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### Step 4: Google Cloud Run Deployment

```yaml
steps:
  # Build container
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/evernote-app:$COMMIT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/evernote-app:latest'
      - '.'

  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/evernote-app:$COMMIT_SHA']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'evernote-app'
      - '--image'
      - 'gcr.io/$PROJECT_ID/evernote-app:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--set-secrets'
      - 'EVERNOTE_CONSUMER_KEY=evernote-consumer-key:latest,EVERNOTE_CONSUMER_SECRET=evernote-consumer-secret:latest'
      - '--set-env-vars'
      - 'NODE_ENV=production,EVERNOTE_SANDBOX=false'

images:
  - 'gcr.io/$PROJECT_ID/evernote-app:$COMMIT_SHA'
  - 'gcr.io/$PROJECT_ID/evernote-app:latest'
```

### Step 5: Serverless Deployment (AWS Lambda)

```javascript
// serverless.yml
service: evernote-integration

provider:
  name: aws
  runtime: nodejs20.x
  stage: ${opt:stage, 'dev'}
  region: us-east-1
  environment:
    NODE_ENV: production
    EVERNOTE_SANDBOX: false
  iam:
    role:
      statements:
        - Effect: Allow
          Action:
            - secretsmanager:GetSecretValue
          Resource:
            - !Sub arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:evernote/*

functions:
  oauth:
    handler: src/handlers/oauth.handler
    events:
      - http:
          path: /auth/evernote
          method: get
      - http:
          path: /auth/evernote/callback
          method: get

  createNote:
    handler: src/handlers/notes.create
    events:
      - http:
          path: /notes
          method: post
          authorizer:
            type: COGNITO_USER_POOLS
            authorizerId: !Ref ApiGatewayAuthorizer

  searchNotes:
    handler: src/handlers/notes.search
    events:
      - http:
          path: /notes/search
          method: get
          authorizer:
            type: COGNITO_USER_POOLS
            authorizerId: !Ref ApiGatewayAuthorizer

plugins:
  - serverless-offline
  - serverless-prune-plugin

custom:
  prune:
    automatic: true
    number: 3
```

### Step 6: Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: evernote-app
  labels:
    app: evernote-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: evernote-app
  template:
    metadata:
      labels:
        app: evernote-app
    spec:
      containers:
        - name: app
          image: your-registry/evernote-app:latest
          ports:
            - containerPort: 3000
          env:
            - name: NODE_ENV
              value: production
            - name: EVERNOTE_SANDBOX
              value: 'false'
            - name: EVERNOTE_CONSUMER_KEY
              valueFrom:
                secretKeyRef:
                  name: evernote-secrets
                  key: consumer-key
            - name: EVERNOTE_CONSUMER_SECRET
              valueFrom:
                secretKeyRef:
                  name: evernote-secrets
                  key: consumer-secret
          resources:
            requests:
              memory: '256Mi'
              cpu: '100m'
            limits:
              memory: '512Mi'
              cpu: '500m'
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: evernote-app
spec:
  selector:
    app: evernote-app
  ports:
    - port: 80
      targetPort: 3000
  type: LoadBalancer
---
apiVersion: v1
kind: Secret
metadata:
  name: evernote-secrets
type: Opaque
stringData:
  consumer-key: ${EVERNOTE_CONSUMER_KEY}
  consumer-secret: ${EVERNOTE_CONSUMER_SECRET}
```

### Step 7: Deployment Verification

```javascript
// scripts/verify-deployment.js
const https = require('https');

const checks = [
  {
    name: 'Health Check',
    url: `${process.env.APP_URL}/health`,
    expectedStatus: 200
  },
  {
    name: 'OAuth Endpoint',
    url: `${process.env.APP_URL}/auth/evernote`,
    expectedStatus: 302 // Redirect
  }
];

async function verifyDeployment() {
  console.log('Verifying deployment...\n');

  for (const check of checks) {
    try {
      const response = await fetch(check.url, { redirect: 'manual' });

      if (response.status === check.expectedStatus) {
        console.log(`[PASS] ${check.name}`);
      } else {
        console.log(`[FAIL] ${check.name} - Expected ${check.expectedStatus}, got ${response.status}`);
        process.exit(1);
      }
    } catch (error) {
      console.log(`[FAIL] ${check.name} - ${error.message}`);
      process.exit(1);
    }
  }

  console.log('\nDeployment verification passed!');
}

verifyDeployment();
```


## Deployment Checklist

```markdown


## Pre-Deployment

- [ ] All tests passing
- [ ] Production API key configured
- [ ] Secrets stored securely
- [ ] Health check endpoint working
- [ ] Logging configured


## Deployment

- [ ] Container built and pushed
- [ ] Infrastructure provisioned
- [ ] Secrets mounted
- [ ] Service deployed
- [ ] Load balancer configured


## Post-Deployment

- [ ] Verify health check
- [ ] Test OAuth flow
- [ ] Monitor error rates
- [ ] Check metrics
- [ ] Update documentation
```
