# Small Batches and Continuous Deployment

The power of small batches is counterintuitive. Most people believe working in large batches is more efficient because it minimizes setup time and context switching. In reality, small batches dramatically reduce cycle time, catch problems earlier, reduce risk, and accelerate learning. This principle, borrowed from lean manufacturing, is one of the most practical and immediately applicable ideas in the Lean Startup.

## Why Small Batches Beat Large Batches

### The Envelope Stuffing Analogy

Imagine you need to stuff, seal, stamp, and address 100 envelopes. There are two approaches:

**Large batch approach:** Fold all 100 letters, then stuff all 100 envelopes, then seal all 100, then stamp all 100, then address all 100.

**Small batch approach:** Take one envelope through the entire process (fold, stuff, seal, stamp, address), then move to the next.

Most people intuitively believe the large batch approach is faster. They are wrong.

**Why small batches win:**

| Factor | Large Batch | Small Batch |
|--------|-------------|-------------|
| Total time | Longer (measured repeatedly in experiments) | Shorter |
| Error detection | Errors found at the very end; must redo entire batch | Errors found immediately; fix one item |
| Work in progress | 100 items in various partial states | 1 item in progress at a time |
| Feedback speed | After all 100 are done | After each one is done |
| Flexibility | Cannot change approach mid-batch | Can adapt approach after each item |

The envelope experiment has been replicated hundreds of times. Small batches win every time. The advantage increases as complexity increases.

### Applied to Startups

| Large Batch Startup | Small Batch Startup |
|--------------------|---------------------|
| Spend 6 months building 20 features | Ship 1 feature, measure, learn, then decide on the next |
| Launch with a "complete" product | Launch with an MVP, iterate based on data |
| Conduct a large market research study, then build | Interview 5 customers, build a test, interview 5 more |
| Write a full business plan, then execute | Test one assumption, adjust plan, test the next |
| Redesign the entire app at once | Change one screen, measure impact, then the next |

### The Mathematics of Small Batches

**Defect amplification:** In large batches, a defect in step 1 affects all items processed in steps 2, 3, 4, and 5 before being discovered. In small batches, a defect is caught before it propagates.

**Queue time:** In large batches, each step waits for the entire previous batch to complete. Items spend most of their time waiting, not being worked on. In small batches, items flow continuously.

**Learning delay:** In large batches, you learn nothing until the entire batch is complete. In small batches, you learn after each item, enabling course correction throughout.

## Continuous Deployment Implementation

Continuous deployment is the ultimate expression of small batch thinking in software. Every change to the codebase is automatically tested and deployed to production, often multiple times per day.

### The Continuous Deployment Pipeline

```
Code commit → Automated tests → Build → Staging deploy → Automated checks → Production deploy → Monitoring
```

### Implementation Stages

| Stage | Description | Batch Size | Deploy Frequency |
|-------|-------------|------------|-----------------|
| 1. Manual | Developer packages and deploys manually | Large (weeks of work) | Monthly or less |
| 2. Scripted | Deploy script automates the process | Medium (days of work) | Weekly |
| 3. Continuous Integration | Automated build and test on every commit | Small (hours of work) | Daily |
| 4. Continuous Delivery | Automated pipeline to staging; manual production trigger | Very small (single changes) | Multiple daily |
| 5. Continuous Deployment | Fully automated to production | Minimal (single commit) | Per commit |

### Prerequisites for Continuous Deployment

**Technical requirements:**
- Automated test suite with reasonable coverage (aim for 70%+ of critical paths)
- Automated build process
- Automated deployment scripts
- Production monitoring and alerting
- Ability to roll back quickly (under 5 minutes)

**Cultural requirements:**
- Team trusts the automated pipeline
- Everyone takes responsibility for the build
- Broken builds are fixed immediately (not "I'll fix it later")
- Small commits are valued over large ones

**Process requirements:**
- Code review before merge (pull request workflow)
- Feature flags for incomplete work
- Trunk-based development or short-lived branches
- On-call rotation for production issues

## Feature Flags and Progressive Rollout

Feature flags decouple deployment from release. You can deploy code to production without exposing it to users, then gradually roll it out.

### Feature Flag Types

| Type | Purpose | Example |
|------|---------|---------|
| Release flag | Control when a feature becomes visible | New dashboard hidden behind flag until ready |
| Experiment flag | Enable A/B testing | Show new checkout flow to 50% of users |
| Ops flag | Control system behavior in production | Disable expensive background job during peak load |
| Permission flag | Restrict access to specific users | Beta feature available only to internal team |

### Progressive Rollout Strategy

| Phase | Audience | Purpose | Duration |
|-------|----------|---------|----------|
| 1. Internal | Team members only | Catch obvious bugs and UX issues | 1-3 days |
| 2. Beta | 1-5% of users (early adopters) | Validate in real conditions with sympathetic users | 3-7 days |
| 3. Canary | 10-25% of users | Monitor for performance and stability issues | 3-7 days |
| 4. Broad rollout | 50-100% of users | Full launch with monitoring | 1-3 days |

### Progressive Rollout Checklist

- [ ] Feature flag is in place and tested (can enable and disable cleanly)
- [ ] Monitoring dashboard shows feature-specific metrics
- [ ] Rollback plan is documented and tested
- [ ] Success metrics are defined for each rollout phase
- [ ] On-call team is aware of the rollout schedule
- [ ] Customer support team is briefed on the new feature

## Small Batch Thinking for Non-Technical Contexts

Small batches apply far beyond software deployment.

### Marketing

| Large Batch | Small Batch |
|-------------|-------------|
| Plan a 6-month campaign, execute all at once | Test one ad creative per day for a week, then scale winners |
| Write 30 blog posts, publish all at once | Write and publish 1 post, measure engagement, adjust topics |
| Redesign the entire website | Change one page, measure conversion, iterate |
| Launch on 5 channels simultaneously | Start with 1 channel, optimize, then expand |

### Sales

| Large Batch | Small Batch |
|-------------|-------------|
| Build a 50-slide pitch deck, present to 20 prospects | Create a 5-slide deck, pitch to 3 prospects, revise based on feedback |
| Train the entire sales team on a new script | Test the script with 2 reps for a week, refine, then train everyone |
| Negotiate all contract terms at once | Agree on key terms first, then iterate on details |

### Hiring

| Large Batch | Small Batch |
|-------------|-------------|
| Write 10 job descriptions, post all, interview in batches | Post 1 role, refine the process, then post the next |
| Onboard 5 new hires simultaneously | Onboard 1 person, learn from their experience, improve for the next |
| Create an entire employee handbook before hiring | Document policies as they become relevant |

### Product Design

| Large Batch | Small Batch |
|-------------|-------------|
| Design 20 screens in Figma, then hand off to engineering | Design 1 screen, get engineering feedback, iterate, then next screen |
| Conduct a 50-person usability study | Test with 5 users, fix issues, test with 5 more |
| Redesign the entire product information architecture | Change 1 navigation element, measure impact, then the next |

## Reducing Batch Size in Practice

### Technique 1: Work Decomposition

Break every task into the smallest independently valuable unit.

**Before:** "Build user dashboard" (2 weeks of work)

**After:**
1. Display user's name and avatar (2 hours)
2. Show account creation date (1 hour)
3. Add usage statistics section (4 hours)
4. Add recent activity feed (6 hours)
5. Add settings shortcuts (3 hours)

Each piece can be deployed, measured, and iterated independently.

### Technique 2: Time-Boxing

Set maximum time limits for work in progress.

| Context | Maximum Batch Size |
|---------|-------------------|
| Feature development | 3 days of work before shipping something |
| Customer research | 5 interviews before synthesizing findings |
| Design iteration | 2 days before user testing |
| Content creation | 1 piece before measuring engagement |
| Experiment cycles | 2 weeks before reviewing results |

### Technique 3: Work-In-Progress Limits

Limit the number of items in progress simultaneously.

**Kanban board example:**

| To Do | In Progress (max 2) | In Review (max 1) | Done |
|-------|---------------------|-------------------|------|
| Task D | Task B | Task A | ... |
| Task E | Task C | | |
| Task F | | | |

When the "In Progress" column is full, no new work starts until something moves to "In Review." This forces completion over starting.

### Technique 4: Single-Piece Flow

Process one item completely before starting the next. In software, this means:

1. Pick one user story
2. Design it
3. Build it
4. Test it
5. Deploy it
6. Measure it
7. Then pick the next one

This feels slower per item but is faster in total throughput and dramatically faster in learning speed.

## Tools and Infrastructure for Small Batches

### Deployment Tools

| Tool Category | Purpose | Examples |
|--------------|---------|---------|
| CI/CD pipeline | Automate build, test, deploy | GitHub Actions, GitLab CI, CircleCI |
| Feature flags | Decouple deploy from release | LaunchDarkly, Unleash, Flagsmith, Statsig |
| Monitoring | Detect issues immediately after deploy | Datadog, Sentry, PagerDuty, Grafana |
| Rollback | Revert quickly when problems occur | Built into most CI/CD tools; Kubernetes rollback |
| A/B testing | Compare variations with real users | Optimizely, Statsig, PostHog, GrowthBook |

### Process Tools

| Tool Category | Purpose | Examples |
|--------------|---------|---------|
| Kanban boards | Visualize flow and WIP limits | Jira, Linear, Trello, Notion |
| Experiment tracking | Document and track experiments | Notion, Airtable, custom spreadsheet |
| Customer feedback | Collect real-time user input | Intercom, Hotjar, UserTesting |
| Analytics | Measure impact of each batch | Amplitude, Mixpanel, PostHog, Google Analytics |

## Real-World Examples

### IMVU: Continuous Deployment Pioneer

IMVU, where Eric Ries served as CTO, deployed code to production 50+ times per day. Each deploy was a tiny batch: sometimes a single line of code.

**Key practices:**
- Automated test suite ran on every commit
- Immune system: automated monitoring rolled back deploys that degraded key metrics
- Engineers deployed their own code (no separate ops team)
- Cluster immune system measured real-time customer behavior after each deploy

**Result:** Problems were caught within minutes. Each deploy was so small that root cause analysis was trivial. The team iterated faster than competitors who deployed monthly.

### Amazon: Two-Pizza Teams and Service Architecture

Amazon decomposed its monolithic application into hundreds of independent services, each owned by a small team (the "two-pizza team" - small enough to feed with two pizzas).

**Key practices:**
- Each team deploys independently
- Services communicate through well-defined APIs
- Teams own their service end-to-end (build, deploy, monitor, support)
- Average deploy frequency: every 11.7 seconds (across the company)

**Result:** Amazon can ship thousands of changes per day. Each change is small, independently deployable, and independently reversible.

### Etsy: From Quarterly to Continuous

Etsy transformed from quarterly "big bang" releases to continuous deployment over several years.

**Before (quarterly releases):**
- 4 deploys per year
- Each deploy was a massive batch of hundreds of changes
- Deploys required multi-day "war rooms" to manage
- Bugs were hard to isolate because so many changes were bundled

**After (continuous deployment):**
- 50+ deploys per day
- Each deploy is a single engineer's change
- Deploys take minutes and require no coordination
- Bugs are immediately traceable to the single change that caused them

**Key enablers:**
- Feature flags (Etsy built their own system, later open-sourced)
- Comprehensive monitoring with deploy annotations
- "Push trains" that batch deploys automatically with individual rollback capability
- Culture of "if it hurts, do it more often"

The lesson across all these examples is the same: reducing batch size feels risky but actually reduces risk. The smaller the batch, the faster the feedback, and the faster you learn.
