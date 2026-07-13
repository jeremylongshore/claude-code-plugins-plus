Google Cloud Run deployment for Shopify apps, including multi-stage Dockerfile and gcloud commands.

```dockerfile
# Dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/package*.json ./
RUN npm ci --production
COPY --from=builder /app/build ./build
EXPOSE 3000
CMD ["npm", "start"]
```

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/shopify-app

gcloud run deploy shopify-app \
  --image gcr.io/$PROJECT_ID/shopify-app \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 3000 \
  --set-secrets="SHOPIFY_API_KEY=shopify-api-key:latest,SHOPIFY_API_SECRET=shopify-api-secret:latest" \
  --min-instances=1 \
  --max-instances=10

# Update app URL in Shopify
# Use the Cloud Run service URL in shopify.app.toml
```
