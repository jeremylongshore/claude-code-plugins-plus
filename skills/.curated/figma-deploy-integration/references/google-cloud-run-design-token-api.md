# Step 2: Google Cloud Run (Design Token API)

Deep-dive reference for the `figma-deploy-integration` skill — extracted from the 'Step 2: Google Cloud Run (Design Token API)' step of the workflow.

```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY dist/ ./dist/
ENV PORT=8080
CMD ["node", "dist/server.js"]
```

```bash
PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
SERVICE="figma-token-api"
REGION="us-central1"

# Store PAT in Secret Manager
echo -n "${FIGMA_PAT}" | gcloud secrets create figma-pat --data-file=-

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE
gcloud run deploy $SERVICE \
  --image gcr.io/$PROJECT_ID/$SERVICE \
  --region $REGION \
  --platform managed \
  --set-secrets="FIGMA_PAT=figma-pat:latest" \
  --allow-unauthenticated \
  --max-instances=5 \
  --timeout=30s
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
