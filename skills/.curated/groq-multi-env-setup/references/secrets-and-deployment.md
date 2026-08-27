# Secret Management & Deployment by Environment

How to source the Groq API key per environment, wire it into Docker Compose
profiles, and inspect the live rate-limit budget for a key.

## Step 3: Secret Management by Platform

Development reads a git-ignored `.env.local`; staging uses CI/CD secrets;
production pulls from a dedicated secret manager. Never commit a real key.

```bash
set -euo pipefail

# === Development ===
# .env.local (git-ignored)
cat > .env.example << 'EOF'
# Get your API key at https://console.groq.com/keys
GROQ_API_KEY=gsk_your_dev_key_here
EOF

# === Staging (GitHub Actions) ===
gh secret set GROQ_API_KEY_STAGING --body "gsk_staging_key"

# === Production (Cloud Platforms) ===
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name groq/prod/api-key \
  --secret-string "gsk_prod_key"

# GCP Secret Manager
echo -n "gsk_prod_key" | gcloud secrets create groq-api-key-prod --data-file=-

# HashiCorp Vault
vault kv put secret/groq/prod api_key="gsk_prod_key"
```

## Step 4: Docker Compose Multi-Env

One compose file, three profiles. `dev`/`staging` inject the key as an env var;
`prod` mounts it as an external Docker secret so it never lands in the process
environment table.

```yaml
# docker-compose.yml
services:
  app-dev:
    build: .
    environment:
      - NODE_ENV=development
      - GROQ_API_KEY=${GROQ_API_KEY}
    profiles: ["dev"]

  app-staging:
    build: .
    environment:
      - NODE_ENV=staging
      - GROQ_API_KEY=${GROQ_API_KEY_STAGING}
    profiles: ["staging"]

  app-prod:
    build: .
    environment:
      - NODE_ENV=production
    secrets:
      - groq_api_key
    profiles: ["prod"]

secrets:
  groq_api_key:
    external: true
```

## Step 6: Rate Limit Awareness by Environment

Groq returns your remaining budget in `x-ratelimit-*` response headers. Check
them per key so dev keys (free tier) and prod keys (higher limits) are tuned
independently.

```bash
set -euo pipefail
# Check current rate limits for your key
curl -si https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"ping"}],"max_tokens":1}' \
  2>/dev/null | grep -iE "^x-ratelimit"
```
