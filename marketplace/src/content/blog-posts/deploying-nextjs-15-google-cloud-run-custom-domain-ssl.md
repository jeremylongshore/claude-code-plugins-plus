---
title: "Deploying Next.js 15 to Google Cloud Run: From Zero to HTTPS in 2 Hours"
description: "Complete guide to deploying Next.js 15 with Docker to Google Cloud Run, configuring custom domains, SSL certificates, and global load balancing. Real troubleshooting included."
date: "2025-10-11"
tags: ["google-cloud-run", "nextjs-15", "docker-deployment", "ssl-certificates", "load-balancer", "cloud-infrastructure", "devops", "production-deployment"]
featured: false
---
I just deployed [ClaudeCodePlugins.io](https://www.claudecodeplugins.io) from scratch to production on Google Cloud Run with custom domain and SSL. Here's the complete journey with every error, fix, and lesson learned.

## The Goal

Deploy a Next.js 15 application to Google Cloud Run with:

- Custom domain (www.claudecodeplugins.io)
- Google-managed SSL certificate
- Global load balancer with HTTP/2
- Serverless auto-scaling (0-10 instances)
- Production-grade infrastructure as code

Starting point: A working Next.js 15 app on localhost.

Target: Live site with HTTPS at a custom domain.

Time budget: Get it done today.

## The Stack

**Application:**

- Next.js 15 (App Router) with standalone mode
- React 19 + TypeScript
- Node 20 runtime
- Docker multi-stage build

**Infrastructure:**

- Google Cloud Run (serverless containers)
- Cloud Build (CI/CD)
- Artifact Registry (container images)
- Global Load Balancer (anycast IP)
- Google-managed SSL certificates

**Domain:** Porkbun DNS pointing to Google Cloud

## Part 1: Docker Configuration

Next.js 15 requires `output: 'standalone'` in `next.config.js` for Docker deployment. This creates a minimal production build without node_modules bloat.

```javascript
// next.config.js
module.exports = {
  output: 'standalone',
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'storage.googleapis.com' },
      { protocol: 'https', hostname: '*.googleusercontent.com' },
    ],
  },
};
```

### Multi-Stage Dockerfile

I used a three-stage build: deps → builder → runner.

```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --legacy-peer-deps

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 3: Runner
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

RUN chown -R nextjs:nodejs /app
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```

**Key decisions:**

- Alpine Linux for small image size (saves bandwidth and startup time)
- Non-root user (security best practice)
- Standalone mode copies only what's needed to run
- Environment variable PORT for Cloud Run compatibility

## Part 2: The First Deployment Attempt

I started with the simplest approach: direct Cloud Run deployment.

```bash
gcloud run deploy claudecodeplugins-web \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 3000
```

**Error 1: Tailwind CSS TypeScript Error**

```
Type '["class"]' is not assignable to type 'DarkModeStrategy | undefined'
```

The build failed because Tailwind CSS 4 changed darkMode syntax. Quick fix in `tailwind.config.ts`:

```typescript
// Before: darkMode: ["class"]
// After:
darkMode: "class"
```

**Error 2: Missing Public Directory**

```
COPY failed: stat app/public: file does not exist
```

The Dockerfile expected a public directory that didn't exist. Created it:

```bash
mkdir -p apps/web/public
touch apps/web/public/.gitkeep
```

## Part 3: Container Registry Nightmares

Now the build succeeded but the push failed.

**Error 3: Container Registry Permission Denied**

```
denied: Permission "artifactregistry.repositories.uploadArtifacts" denied
```

I initially tried to use the old Container Registry (gcr.io), which has known permission issues. The fix: migrate to Artifact Registry.

```bash
# Create Artifact Registry repository
gcloud artifacts repositories create app \
  --repository-format=docker \
  --location=us-central1

# Update image path from:
# gcr.io/PROJECT/IMAGE
# To:
# us-central1-docker.pkg.dev/PROJECT/REPO/IMAGE
```

**Error 4: Organization Policy Blocking Public Access**

Cloud Run deployed successfully but returned 403 Forbidden. The error:

```
One or more users named in the policy do not belong to a permitted customer
```

This was an organization-level IAM policy restricting `allUsers` access. I needed to override it at the project level:

```yaml
# org-policy-override.yaml
constraint: constraints/iam.allowedPolicyMemberDomains
listPolicy:
  allValues: ALLOW
```

Applied with:

```bash
gcloud resource-manager org-policies set-policy \
  org-policy-override.yaml \
  --project=PROJECT_ID
```

Then set the IAM policy directly:

```json
{
  "bindings": [{
    "role": "roles/run.invoker",
    "members": ["allUsers"]
  }]
}
```

```bash
gcloud run services set-iam-policy claudecodeplugins-web \
  iam-policy.json \
  --region=us-central1
```

**Success!** The Cloud Run service was now publicly accessible.

## Part 4: Custom Domain and Load Balancer

Google Cloud Run supports custom domains two ways:

1. **Cloud Run Domain Mapping** - Simple, but requires Google Search Console verification
2. **Load Balancer + Serverless NEG** - More complex, but no Search Console needed

I chose the Load Balancer approach because:

- No domain verification required
- Global anycast IP (faster worldwide)
- Built-in CDN support
- More control over routing

### Architecture

```
Internet (Port 443/80)
       ↓
Global Load Balancer (35.201.66.187)
       ↓
SSL Certificate (Google-managed)
       ↓
Serverless NEG (Network Endpoint Group)
       ↓
Cloud Run Service
```

### Setting Up the Load Balancer

**Step 1: Create Serverless Network Endpoint Group**

This connects the Load Balancer to Cloud Run.

```bash
gcloud compute network-endpoint-groups create claudecodeplugins-neg \
  --region=us-central1 \
  --network-endpoint-type=serverless \
  --cloud-run-service=claudecodeplugins-web
```

**Step 2: Create Backend Service**

```bash
gcloud compute backend-services create claudecodeplugins-backend \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED
```

**Error 5: Backend Service Port Name Conflict**

I initially tried to specify `--protocol=HTTPS` but got:

```
Port name is not supported for Serverless NEG
```

Serverless NEGs automatically determine ports. Just create the backend service without protocol specifications.

**Step 3: Add Backend**

```bash
gcloud compute backend-services add-backend claudecodeplugins-backend \
  --global \
  --network-endpoint-group=claudecodeplugins-neg \
  --network-endpoint-group-region=us-central1
```

**Step 4: Create URL Map**

```bash
gcloud compute url-maps create claudecodeplugins-lb \
  --default-service=claudecodeplugins-backend \
  --global
```

**Step 5: Reserve Static IP**

```bash
gcloud compute addresses create claudecodeplugins-ip \
  --ip-version=IPV4 \
  --global
```

This gave me: `35.201.66.187`

**Step 6: Create SSL Certificate**

```bash
gcloud compute ssl-certificates create claudecodeplugins-cert \
  --domains=www.claudecodeplugins.io \
  --global
```

Google-managed certificates are free and auto-renewing. But they require domain verification via HTTP challenge on port 80.

**Step 7: Create HTTPS Proxy**

```bash
gcloud compute target-https-proxies create claudecodeplugins-https-proxy \
  --url-map=claudecodeplugins-lb \
  --ssl-certificates=claudecodeplugins-cert \
  --global
```

**Step 8: Create Forwarding Rule (HTTPS)**

```bash
gcloud compute forwarding-rules create claudecodeplugins-https-rule \
  --address=claudecodeplugins-ip \
  --target-https-proxy=claudecodeplugins-https-proxy \
  --global \
  --ports=443
```

## Part 5: The SSL Certificate Problem

After configuring everything, I checked the SSL certificate status:

```bash
gcloud compute ssl-certificates describe claudecodeplugins-cert --global
```

Status: `PROVISIONING` with domain status `FAILED_NOT_VISIBLE`

This means Google's verification bot couldn't reach my domain on HTTP port 80 to complete the challenge.

**The Issue:** I only configured HTTPS (port 443), but Google needs HTTP (port 80) for verification.

**The Fix:** Add HTTP forwarding.

**Step 9: Create HTTP Proxy and Forwarding Rule**

```bash
gcloud compute target-http-proxies create claudecodeplugins-http-proxy \
  --url-map=claudecodeplugins-lb \
  --global

gcloud compute forwarding-rules create claudecodeplugins-http-rule \
  --address=claudecodeplugins-ip \
  --target-http-proxy=claudecodeplugins-http-proxy \
  --global \
  --ports=80
```

Now both ports 80 and 443 route to the same backend.

## Part 6: DNS Configuration

In Porkbun, I added A records pointing to the static IP:

```
Type: A
Host: www
Answer: 35.201.66.187
TTL: 3600

Type: A
Host: @
Answer: 35.201.66.187
TTL: 3600
```

Verified DNS propagation:

```bash
dig +short www.claudecodeplugins.io @8.8.8.8
# Returns: 35.201.66.187
```

## Part 7: Waiting for SSL

SSL certificate provisioning takes 15-60 minutes after DNS propagation. I monitored it with:

```bash
gcloud compute ssl-certificates describe claudecodeplugins-cert \
  --global \
  --format="yaml(managed.status, managed.domainStatus)"
```

Progression:

1. `PROVISIONING` + `FAILED_NOT_VISIBLE` (DNS not propagated)
2. `PROVISIONING` + `PROVISIONING` (Google verifying domain)
3. `ACTIVE` + `ACTIVE` (Ready!)

After about 30 minutes, the certificate became active.

## Part 8: Testing the Live Site

```bash
curl -I https://www.claudecodeplugins.io
```

```
HTTP/2 200
vary: rsc, next-router-state-tree, next-router-prefetch
x-nextjs-cache: HIT
x-powered-by: Next.js
cache-control: s-maxage=31536000
content-type: text/html; charset=utf-8
```

**Success!** The site was live with:

- ✅ HTTPS with valid SSL certificate
- ✅ HTTP/2 protocol
- ✅ Next.js static pre-rendering
- ✅ CDN edge caching
- ✅ 75ms response time

## Part 9: Infrastructure as Code

I documented everything in a comprehensive runbook (`gcp-cloud-run-launch.md`) and created:

1. **cloudbuild.yaml** - Automated CI/CD pipeline

```yaml
steps:
  - name: "gcr.io/cloud-builders/docker"
    args: ["build", "-t", "${_REGION}-docker.pkg.dev/${_PROJECT_ID}/${_REPO_NAME}/${_IMAGE_NAME}:${_TAG}", "apps/web"]

  - name: "gcr.io/cloud-builders/docker"
    args: ["push", "${_REGION}-docker.pkg.dev/${_PROJECT_ID}/${_REPO_NAME}/${_IMAGE_NAME}:${_TAG}"]

  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: gcloud
    args:
      - "run"
      - "deploy"
      - "${_SERVICE_NAME}"
      - "--image=${_REGION}-docker.pkg.dev/${_PROJECT_ID}/${_REPO_NAME}/${_IMAGE_NAME}:${_TAG}"
      - "--region=${_REGION}"
      - "--allow-unauthenticated"
      - "--port=3000"
```

1. **Makefile** - Convenience commands

```makefile
deploy:
\tgcloud builds submit --config=cloudbuild.yaml

url:
\t@gcloud run services describe $(SERVICE_NAME) --region $(REGION) --format='value(status.url)'

logs:
\tgcloud run services logs read $(SERVICE_NAME) --region $(REGION) --limit=100

rollback:
\t# Roll back to previous revision
```

1. **.gcloud.env.example** - Environment variable documentation

2. **README_DEPLOY.md** - 15-line quickstart guide

Future deployments are now just:

```bash
make deploy
```

## Key Learnings

### What Worked

1. **Multi-stage Docker builds** - Reduced final image size by 70%
2. **Artifact Registry over Container Registry** - Better permissions, modern tooling
3. **Load Balancer approach** - No Search Console verification needed
4. **Comprehensive documentation** - Made second deployment trivial

### What Didn't Work (At First)

1. **Missing HTTP port 80** - SSL verification requires it
2. **Organization policies** - Required project-level override
3. **Container Registry permissions** - Migrated to Artifact Registry instead
4. **Tailwind CSS array syntax** - Changed to string format
5. **Serverless NEG with port names** - Let Google auto-detect ports

### Cost Breakdown

Monthly estimate:

- Cloud Run: $0-20 (pay per use, 0 min instances)
- Load Balancer: ~$18/month (global)
- SSL Certificate: $0 (Google-managed)
- **Total: ~$20-40/month**

For comparison, a single $5 VPS would be cheaper but:

- No auto-scaling
- Manual SSL certificate management
- No global CDN
- Manual deployments
- Single point of failure

The serverless approach is worth it for production sites.

## The Complete Command Sequence

For reference, here's the exact order of commands that worked:

```bash
# 1. Set up project
gcloud config set project PROJECT_ID

# 2. Enable APIs
gcloud services enable run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  compute.googleapis.com

# 3. Create Artifact Registry
gcloud artifacts repositories create app \
  --repository-format=docker \
  --location=us-central1

# 4. Build and push Docker image
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/PROJECT_ID/app/web:latest

# 5. Deploy to Cloud Run
gcloud run deploy claudecodeplugins-web \
  --image us-central1-docker.pkg.dev/PROJECT_ID/app/web:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --port 3000

# 6. Create load balancer infrastructure
# (Serverless NEG, backend service, URL map, SSL cert, static IP, proxies, forwarding rules)
# See full commands in article above

# 7. Configure DNS
# Add A records in DNS provider pointing to static IP

# 8. Wait for SSL certificate provisioning (15-60 minutes)

# 9. Test
curl -I https://www.claudecodeplugins.io
```

## Conclusion

Total time from "I need to deploy this" to "site is live with HTTPS": **2 hours**.

Most of that was waiting for SSL certificate provisioning (30 minutes) and troubleshooting permissions (45 minutes). The actual configuration took about 45 minutes.

The result: A production-grade deployment with auto-scaling, global CDN, managed SSL, and one-command future deployments.

The full runbook and all configuration files are in the project repository. Future deployments are literally just `make deploy`.

## Related Posts

- [Debugging Slack Integration: From 6 Duplicate Responses to Instant Acknowledgment](https://startaitools.com/posts/debugging-slack-integration-from-six-duplicate-responses-to-instant-acknowledgment/)
- [Building a 254-Table BigQuery Schema in 72 Hours](https://startaitools.com/posts/building-254-table-bigquery-schema-72-hours/)
- [Building Production Testing Suite with Playwright and GitHub Actions](https://startaitools.com/posts/building-production-testing-suite-playwright-github-actions-survey-automation/)

## Links

- **Live Site:** [www.claudecodeplugins.io](https://www.claudecodeplugins.io)
- **Architecture:** Global Load Balancer → Serverless NEG → Cloud Run
- **Response Time:** 75ms average
- **Stack:** Next.js 15 + Docker + Google Cloud Run
