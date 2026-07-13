# Google Cloud Run

## Google Cloud Run

### Dockerfile

```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
CMD ["npm", "start"]
```

### Deploy Script

```bash
#!/bin/bash
# deploy-cloud-run.sh

PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
SERVICE_NAME="supabase-service"
REGION="us-central1"

# Build and push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets=SUPABASE_API_KEY=supabase-api-key:latest
```
