---
title: "Intent Solutions Portfolio 2025: Five Production Platforms and the Architecture Behind 4-Day Deployments"
description: "Deep dive into Intent Solutions' five production platforms: DiagnosticPro, Hustle, CostPlusDB, ClaudeCodePlugins, and the technical architecture enabling concept-to-production deployment in days, not months."
date: "2025-10-20"
tags: ["portfolio", "architecture", "deployment", "gcp", "ai-automation", "case-study"]
featured: false
---
When you see "deploy in days, not months," it sounds like marketing fluff. This is the technical breakdown of how Intent Solutions actually does it—with five production platforms serving real customers, measurable cost optimization, and architecture patterns you can replicate.

## The Portfolio: Five Production Platforms

### Platform Overview

| Platform | Purpose | Tech Stack | Status | Key Metric |
|----------|---------|-----------|--------|------------|
| **[DiagnosticPro](https://diagnosticpro.io)** | AI vehicle diagnostics | React 18, Firebase, Vertex AI | Production | 96.4% gross margin |
| **[Hustle](https://hustlestats.io)** | Youth sports recruiting stats | Next.js 15, PostgreSQL, Cloud Run | Live beta | COPPA-compliant auth |
| **[CostPlusDB](https://costplusdb.dev)** | Transparent database hosting | PostgreSQL 16, AWS, pgBackRest | Production | 68% cost savings vs AWS |
| **[ClaudeCodePlugins](https://claudecodeplugins.io)** | Plugin marketplace | Next.js 15, Cloud Run | Live | 236 production plugins |
| **Intent Solutions** | Company landing | Astro 5, Tailwind CSS 4 | Production | 4-day concept→deploy |

**Combined infrastructure:** Google Cloud Platform (primary), AWS (secondary), Netlify (static sites), Firebase (customer platforms).

## Case Study 1: DiagnosticPro - $4.99 AI Diagnostics at Scale

### The Business Problem

Traditional automotive diagnostics cost $120-200 per visit. Customers want faster, cheaper answers for common issues.

### Technical Solution

**Architecture:**

```
User Upload (Firebase Storage)
    ↓
Firestore Trigger (Cloud Function)
    ↓
Vertex AI Gemini 2.5 Flash Analysis
    ↓
14-Section Diagnostic Report (PDF)
    ↓
Email Delivery + Firestore Record
```

**Cost Structure:**

- Vertex AI Gemini: $0.15 per diagnostic
- Firebase Hosting: $0.026 per GB
- Cloud Functions: $0.40 per 1M invocations
- **Total cost per diagnostic:** ~$0.18
- **Price to customer:** $4.99
- **Gross margin:** 96.4%

**Why this works:**

1. **Vertex AI cost advantage:** 62.5% cheaper than OpenAI GPT-4 for equivalent quality
2. **Firebase auto-scaling:** Zero infrastructure management overhead
3. **Serverless architecture:** Pay-per-use eliminates fixed costs
4. **PDF generation:** Client-side with jsPDF (zero server cost)

### Data Platform Scale

**Supporting infrastructure:**

- **226+ RSS feeds:** Curated automotive content sources
- **Multiple BigQuery datasets:** Production data analytics
- **3 GCP projects:** Clean separation (prod, analytics, creatives)

**Key learning:** Data platform investment pays dividends. RSS feed curation and BigQuery analytics inform diagnostic accuracy improvements.

## Case Study 2: Hustle - Next.js 15 + COPPA Compliance

### The Technical Challenge

Build youth sports stats platform with:

- COPPA-compliant authentication (age 13+ requirement)
- Parent verification workflow
- College recruiter trust signals
- Performance at scale (1000s of players)

### Architecture Decisions

**Framework:** Next.js 15 with Turbopack

- **Why:** React 19 + App Router + Turbopack = fastest development velocity
- **Trade-off:** Bleeding edge = occasional breaking changes, but speed wins

**Authentication:** NextAuth v5 with JWT strategy

```typescript
// Simplified NextAuth v5 config
import NextAuth from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"
import { PrismaAdapter } from "@auth/prisma-adapter"

export const { handlers, auth } = NextAuth({
  adapter: PrismaAdapter(prisma),
  session: { strategy: "jwt" },
  providers: [
    CredentialsProvider({
      credentials: {
        email: { type: "email" },
        password: { type: "password" }
      },
      authorize: async (credentials) => {
        // bcrypt validation, COPPA age check
        const user = await validateUser(credentials)
        return user
      }
    })
  ]
})
```

**Database:** PostgreSQL 15 with Prisma ORM

Schema highlights:

```prisma
model Player {
  id          String   @id @default(cuid())
  userId      String   // Parent relationship
  birthday    DateTime // COPPA age validation
  firstName   String
  lastName    String
  position    String
  teamName    String
  photoUrl    String?
  games       Game[]   // Performance stats
}

model Game {
  id          String   @id @default(cuid())
  playerId    String
  gameDate    DateTime
  opponent    String
  goals       Int      @default(0)
  assists     Int      @default(0)
  verified    Boolean  @default(false) // Trust signal
  // ... additional stats
}
```

**Deployment:** Terraform-managed GCP infrastructure

```hcl
resource "google_cloud_run_v2_service" "hustle_frontend" {
  name     = "hustle-frontend"
  location = var.region

  template {
    containers {
      image = "gcr.io/${var.project_id}/hustle-frontend:latest"

      env {
        name  = "DATABASE_URL"
        value_from {
          secret_key_ref {
            secret  = "database-url"
            version = "latest"
          }
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
  }
}
```

**Key optimization:** min_instance_count = 0 for cost control during beta.

### COPPA Compliance Implementation

**Critical requirements:**

1. Age verification at signup (reject < 13 years old)
2. Parental consent for data collection
3. Privacy policy accessible before registration
4. No targeted advertising to minors
5. Data minimization (collect only necessary fields)

**Implementation:**

```typescript
// Age validation utility
export function validateCOPPAAge(birthday: Date): boolean {
  const today = new Date()
  const age = today.getFullYear() - birthday.getFullYear()
  const monthDiff = today.getMonth() - birthday.getMonth()

  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthday.getDate())) {
    age--
  }

  return age >= 13
}

// Registration flow
async function registerPlayer(data: PlayerInput) {
  if (!validateCOPPAAge(data.birthday)) {
    throw new Error("Players must be 13+ years old to register")
  }

  // Parent email verification required
  await sendParentConsentEmail(data.parentEmail)

  // Create player record (pending parent approval)
  return await prisma.player.create({
    data: { ...data, verified: false }
  })
}
```

**Lesson learned:** Legal compliance isn't a feature you bolt on—it's architecture from day one.

## Case Study 3: CostPlusDB - Radical Pricing Transparency

**Live at:** [costplusdb.dev](https://costplusdb.dev)

### The Business Hypothesis

Traditional managed PostgreSQL providers mark up costs 300-400%. What if we show exact costs and charge a fixed 25% margin?

### Pricing Model

**Traditional AWS RDS pricing (db.t3.medium):**

- Instance: $0.068/hour × 730 hours = $49.64
- Storage: 100GB SSD @ $0.115/GB = $11.50
- Backups: 100GB @ $0.095/GB = $9.50
- Data transfer: ~$20/month
- **AWS total:** ~$90.64/month
- **Typical managed provider:** $250-350/month

**CostPlusDB pricing:**

- Infrastructure cost: $70/month (AWS + overhead)
- Markup: $19/month (25% transparent margin)
- **Customer price:** $89/month
- **Customer savings:** 68% vs typical providers

### Technical Architecture

**Deployment:**

- PostgreSQL 16 on dedicated AWS EC2
- pgBackRest for automated backups (30-day retention)
- 7-day point-in-time recovery
- SSL/TLS encryption mandatory
- 24/7 monitoring with uptime tracking

**Key differentiator:** Publish operational runbooks publicly. Customers see exactly how we manage their database.

**Constraint-driven growth:** Max 5 new clients/month maintains quality. Waitlist creates urgency.

## Case Study 4: ClaudeCodePlugins - 236 Plugins at Scale

### The Scale Challenge

Managing 236 production plugins requires automation. Manual processes break at 50 plugins.

### Two-Catalog Architecture

**marketplace.extended.json** (Source of Truth):

```json
{
  "plugins": [
    {
      "id": "plugin-id",
      "name": "Plugin Name",
      "description": "Description",
      "author": "Author",
      "version": "1.0.0",
      "category": "Category",
      "tags": ["tag1", "tag2"],
      "install_url": "https://...",
      "documentation_url": "https://...",
      "pricing": "free",
      // Website-specific metadata
      "featured": true,
      "downloads": 1234,
      "rating": 4.8
    }
  ]
}
```

**marketplace.json** (Generated, CLI-compatible):

```json
{
  "plugins": [
    {
      "id": "plugin-id",
      "name": "Plugin Name",
      "description": "Description",
      // Only CLI-required fields
    }
  ]
}
```

**Generation script:**

```bash
#!/bin/bash
# Strip website metadata for CLI compatibility
jq '.plugins | map({
  id, name, description, author, version,
  category, tags, install_url, documentation_url
})' marketplace.extended.json > marketplace.json
```

### Agent Skills Generation at Scale

**Challenge:** Create 159 plugin Skills using Vertex AI Gemini without manual work.

**Solution:** Batch processing with comprehensive context

**Vertex AI prompt structure:**

```
System Context (480 lines):
- What Claude Code is (released 2025)
- What Agent Skills are (v1.1.0 feature)
- Complete skill specification
- 10+ working examples
- Quality requirements

User Prompt:
Generate Agent Skill for [plugin_name]
Plugin context: [plugin description, capabilities]
Requirements: Strict markdown, auto-triggered, 2000-4000 chars
```

**Results:**

- **159 plugins processed**
- **100% success rate** (zero errors)
- **$0 cost** (Gemini 2.0 Flash free tier)
- **3,210 bytes average SKILL.md** (17x larger than Anthropic examples)

**Key learning:** Comprehensive context engineering + free tier optimization = scalable AI content generation.

## Technical Patterns Across All Platforms

### Pattern 1: Serverless-First Architecture

**Principle:** Minimize fixed infrastructure costs. Pay only for usage.

**Implementation:**

- Cloud Run (DiagnosticPro, CCPI, Hustle)
- Firebase Functions (DiagnosticPro)
- Netlify Functions (static sites)
- Lambda@Edge (CostPlusDB monitoring)

**Cost impact:** 60-80% reduction vs. traditional VPS hosting.

### Pattern 2: Multi-Cloud by Design

**Principle:** No vendor lock-in. Use best tool for each job.

**Distribution:**

- **GCP:** Primary (Vertex AI, BigQuery, Cloud Run, Firestore)
- **AWS:** Secondary (RDS, EC2 for specific workloads)
- **Netlify:** Static hosting (Hugo blogs, marketing sites)
- **Firebase:** Customer-facing apps (real-time, easy auth)

**Trade-off:** Operational complexity vs. vendor negotiating power.

### Pattern 3: Infrastructure as Code Everywhere

**Tools:**

- Terraform (GCP, AWS infrastructure)
- Firebase CLI (deployment automation)
- GitHub Actions (CI/CD pipelines)
- Docker (containerization)

**Example GitHub Actions workflow:**

```yaml
name: Deploy to Cloud Run
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Build and deploy
        run: |
          gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE
          gcloud run deploy $SERVICE \
            --image gcr.io/$PROJECT_ID/$SERVICE \
            --region us-central1 \
            --allow-unauthenticated
```

**Result:** Every platform deploys in < 5 minutes from git push.

### Pattern 4: Comprehensive Documentation as Code

**CLAUDE.md in every repository:**

```markdown
# CLAUDE.md

## Quick Commands
```bash
npm run dev
npm run build
npm run deploy
```

## Architecture

[System diagrams, API docs, deployment flow]

## Common Tasks

[Step-by-step instructions for frequent operations]

## Troubleshooting

[Known issues, solutions, debugging guides]

```

**Why this matters:** Future developers (including future you) need context, not tribal knowledge.

### Pattern 5: Cost Optimization from Day One

**Strategies:**
1. **Use free tiers aggressively** (Vertex AI Gemini 2.0 Flash, Netlify, Firebase)
2. **Right-size infrastructure** (Cloud Run min instances = 0)
3. **Optimize data transfer** (regional deployments, CDN usage)
4. **Monitor religiously** (GCP billing alerts, cost dashboards)

**Example cost breakdown (DiagnosticPro monthly):**
- Vertex AI: ~$50 (333 diagnostics/month)
- Firebase Hosting: $5
- Cloud Functions: $10
- Firestore: $15
- **Total: $80/month**
- **Revenue: $1,665** (333 × $4.99)
- **Gross margin: 95.2%**


## Deployment Velocity: The 4-Day Pattern

### Day 1: Architecture & Setup
- Define requirements (2-3 hour session)
- Choose tech stack (optimize for speed + cost)
- Initialize repository with CLAUDE.md
- Set up CI/CD pipeline

### Day 2: Core Implementation
- Build MVP features only
- Skip polish, focus on functionality
- Write deployment scripts
- Test local deployment

### Day 3: Production Deployment
- Deploy to staging environment
- Test with real data
- Fix critical bugs only
- Deploy to production

### Day 4: Launch & Monitor
- Soft launch to limited audience
- Monitor errors, performance, costs
- Document issues (not fix everything)
- Plan iteration roadmap

**Critical principle:** Ship with bugs. Fix in production based on real usage data.


## What Doesn't Work: Honest Failures

### Failed Pattern: Over-Engineering Auth

**Mistake:** Built custom JWT auth for three platforms before standardizing on NextAuth.

**Cost:** 40+ hours wasted on reinventing solved problems.

**Lesson:** Use battle-tested libraries. Innovation belongs in business logic, not infrastructure.

### Failed Pattern: Manual Plugin Management

**Mistake:** Managed first 50 plugins manually with spreadsheets.

**Cost:** 10 hours/week on plugin catalog updates.

**Solution:** Built two-catalog automated system. Now 2 hours/month.

### Failed Pattern: Ignoring Cost Early

**Mistake:** Built first DiagnosticPro prototype on OpenAI GPT-4 without cost analysis.

**Impact:** $0.40/diagnostic made unit economics impossible at $4.99 price point.

**Fix:** Migrated to Vertex AI Gemini. Margin jumped from 20% to 96%.


## Metrics That Matter

### Deployment Velocity
- **Average time to production:** 4 days
- **Fastest deployment:** Intent Solutions landing (4 days concept → live)
- **Slowest deployment:** DiagnosticPro (evolved over 8 months with multiple migrations)

### Cost Optimization
- **Vertex AI vs OpenAI:** 62.5% savings
- **CostPlusDB vs AWS managed:** 68% savings
- **Hybrid AI Stack potential:** 60-80% cost reduction

### Scale Metrics
- **Production platforms:** 5 actively maintained
- **Claude Code plugins:** 236 production-ready
- **Agent Skills generated:** 159 via Vertex AI
- **RSS feeds curated:** 226+
- **Repositories:** 30+ across public/private

### Quality Metrics
- **Vertex AI batch success rate:** 100% (159/159 plugins)
- **DiagnosticPro uptime:** 99.5%+ (Firebase SLA)
- **CI/CD pipeline success:** >95% (GitHub Actions)


## Replicable Architecture Patterns

### Pattern: Fast Firebase Migration

**Problem:** Legacy Supabase setup becoming cost-prohibitive.

**Solution:** 4-day Firebase migration

**Steps:**
1. **Day 1:** Set up Firebase project, configure Firestore security rules
2. **Day 2:** Migrate React app to Firebase Hosting, convert API routes to Cloud Functions
3. **Day 3:** Data migration from Supabase → Firestore (scripted)
4. **Day 4:** DNS cutover, monitor, fix critical issues

**Code example (Firestore security rules):**
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /diagnosticSubmissions/{submissionId} {
      allow read, write: if request.auth != null;
    }

    match /orders/{orderId} {
      allow read: if request.auth.uid == resource.data.userId;
      allow write: if request.auth != null;
    }
  }
}
```

### Pattern: Terraform Multi-Environment Setup

**Structure:**

```
terraform/
├── environments/
│   ├── prod/
│   │   ├── main.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   │   ├── main.tf
│   │   └── terraform.tfvars
│   └── dev/
│       ├── main.tf
│       └── terraform.tfvars
├── modules/
│   ├── cloud_run/
│   ├── cloud_sql/
│   └── vpc/
└── README.md
```

**Key principle:** DRY (Don't Repeat Yourself) via modules, environment-specific via tfvars.

### Pattern: GitHub Actions Multi-Stage Deployment

**Workflow:**

```yaml
name: Multi-Stage Deployment
on:
  push:
    branches: [main, staging, dev]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        run: npm test

  deploy-dev:
    if: github.ref == 'refs/heads/dev'
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to dev
        run: ./deploy.sh dev

  deploy-staging:
    if: github.ref == 'refs/heads/staging'
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: ./deploy.sh staging

  deploy-prod:
    if: github.ref == 'refs/heads/main'
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: ./deploy.sh prod
```

**Result:** Branch-based environments with automatic deployment.

## Business Lessons from Running Five Platforms

### Lesson 1: Margin Comes from Infrastructure Decisions

**DiagnosticPro margin:** 96.4% (Vertex AI choice)
**CostPlusDB margin:** 21% (transparent pricing choice)
**Hustle margin:** TBD (freemium model, optimize for scale)

**Insight:** Technology choices directly impact profitability. Cloud provider, AI model, database—each decision affects unit economics.

### Lesson 2: Documentation Scales, Humans Don't

**CLAUDE.md adoption rate:** 100% of projects
**Onboarding time reduction:** ~70% (for new contributors)
**Bus factor improvement:** From 1 to "anyone can deploy"

**Insight:** Documentation is infrastructure. Treat it like code: version control, reviews, updates.

### Lesson 3: Constraints Force Better Decisions

**CostPlusDB constraint:** 5 clients/month max
**Result:** Higher quality service, deliberate growth, waiting list urgency

**Hustle constraint:** Solo operator, no team
**Result:** Automation-first design, clean architecture, minimal manual processes

**Insight:** Artificial constraints prevent scope creep and force focus.

## What's Next: Q4 2025 Roadmap

### ClaudeCodePlugins

- **Goal:** Community contribution system
- **Milestone:** 10 external contributors by Dec 2025
- **Technical:** GitHub-based submission workflow

### Hustle

- **Goal:** Early access beta
- **Milestone:** 10 families testing verification workflow
- **Technical:** Parent consent automation

### CostPlusDB

- **Goal:** Public case studies
- **Milestone:** 3 customer migration stories
- **Technical:** Transparent cost tracking dashboards

### Intent Solutions

- **Goal:** Consulting engagement process
- **Milestone:** 5 client engagements
- **Technical:** Standardized project templates

## For Technical Founders: Lessons Learned

### 1. Ship Early, Ship Often

Every platform launched with missing features. Every platform improved because of it.

**Corollary:** Users don't care about your feature list. They care about solving their problem.

### 2. Cost Optimization Isn't Premature

Choosing Vertex AI over OpenAI from day one made DiagnosticPro profitable immediately.

**Corollary:** Margin problems can't be fixed with scale. Fix unit economics first.

### 3. Automation Pays Compounding Returns

N8N workflows save 10+ hours/week. GitHub Actions eliminate deployment errors. Terraform prevents configuration drift.

**Corollary:** Time spent on automation is investment, not cost.

### 4. Multi-Cloud Is Realistic for Solo Operators

GCP for AI/analytics, AWS for databases, Netlify for static—each platform excels at something.

**Corollary:** Vendor lock-in is a choice, not a requirement.

### 5. Documentation Is a Product

CLAUDE.md files get more usage than some features.

**Corollary:** If you can't explain it, you can't maintain it.

## Conclusion: Deploy in Days, Learn Forever

The real achievement isn't five production platforms. It's the architecture patterns, cost optimization strategies, and deployment velocity that make the next platform faster.

**Current state:** 4-day average deployment (concept → production)
**Next goal:** 2-day deployment for standardized patterns

**For Intent Solutions customers:** This infrastructure exists to serve your deployments. Every pattern proven in production. Every cost optimized. Every deployment automated.

**Want to see the code?** Most projects are open source:

- [Claude Code Plugins](https://github.com/jeremylongshore/claude-code-plugins-plus)
- [Waygate MCP](https://github.com/jeremylongshore/waygate-mcp)
- [Bob's Brain](https://github.com/jeremylongshore/bobs-brain)
- [Local RAG Agent](https://github.com/jeremylongshore/local-rag-agent-intent-solutions)

**Ready to deploy?** [jeremy@intentsolutions.io](mailto:jeremy@intentsolutions.io)

**About Intent Solutions:** AI automation consultancy specializing in rapid deployment, cost optimization, and production-ready systems. Based in Gulf Shores, Alabama. Deployed five production platforms in 2025.

**Last updated:** October 20, 2025
