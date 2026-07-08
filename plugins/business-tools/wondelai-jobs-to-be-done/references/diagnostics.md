# Product Diagnostics Through JTBD Lens

This file is the deep diagnostic layer behind SKILL.md. Run the **Quick Diagnostic** table in SKILL.md first for the seven pass/fail readiness checks; come here when a symptom needs a probable cause, when you need JTBD metrics, or when you are running a churn analysis.

## Red Flags - Signs You Don't Know the Job

1. **You describe product through features** - "it's a tool for X with Y feature"
2. **Competition is only "similar products"** - you don't see non-obvious competitors
3. **You segment by demographics** - "target is men 25-35"
4. **High acquisition, low retention** - you win Big Hire, lose Little Hire
5. **Customers use product "wrong"** - they create workarounds

## Diagnostic Framework

### Why Aren't Customers Buying?

| Symptom | Probable Cause | Action |
|---------|----------------|--------|
| They don't know we exist | Job is poorly articulated in messaging | Rewrite messaging around the job |
| They know but don't try | Anxiety about new > Pull | Reduce friction, offer guarantees |
| They try but don't buy | Product doesn't do the job | Investigate gap between promise and reality |
| They buy but don't use | Little Hire lost | Redesign the moment of use |
| They use but churn | Job changed or better "employee" appeared | Investigate "firing" reasons |

For the full timeline-interview question set (first-thought -> search -> purchase -> usage), see SKILL.md section 5; for the structured churn ("firing") interview, see the Churn Interview Framework table below.

## JTBD Metrics

### Instead of Traditional Metrics:

| Traditional Metric | Problem | JTBD Metric |
|-------------------|---------|-------------|
| DAU/MAU | Doesn't tell if job is being done | % of completed "jobs" |
| Time in app | More ≠ better | Time to job completion |
| Feature adoption | Features ≠ value | Does feature help with job? |
| NPS | General satisfaction | Would you hire us again for this job? |
| Churn rate | Retrospective | Leading indicators of "searching for alternatives" |

### Job Completion Rate

Define what "job done" means and measure:
- % of sessions where job was completed
- Time to first success (Time to Value)
- Repeatability of "hiring" (hire frequency)

---

## Post-Launch Iteration

### Continuous Job Discovery

After launch, keep learning:

**Usage data signals:**
- Features used ≠ Features valued (may use out of necessity)
- Time spent ≠ Job done (frustration can increase time)
- Feature requests often describe solutions, not jobs

**Ongoing research:**
- Interview new customers within 2 weeks of purchase
- Interview churned customers within 1 week of leaving
- Observe actual usage (session recordings, support tickets)
- Track "aha moments" that predict retention

### Iteration Framework

| Signal | What It Means | Action |
|--------|---------------|--------|
| High acquisition, low retention | Win Big Hire, lose Little Hire | Investigate moment of use |
| Feature used but low satisfaction | Functional works, emotional doesn't | Research emotional dimension |
| Unexpected use patterns | Hidden jobs emerging | Interview these users |
| Power users vs. casual users | Different jobs being done | May need segmentation |

---

## Churn Analysis Through JTBD Lens

### Why "Firing" Happens

Customers fire products when:
1. **Job changed** - Circumstances evolved (company grew, life changed)
2. **Better "employee" appeared** - Competitor does job better
3. **Job wasn't being done** - Product never delivered on promise
4. **Friction accumulated** - Too hard to use, not worth the effort
5. **Priorities shifted** - Other jobs became more important

### Churn Interview Framework

**Timing:** Within 1 week of cancellation (memory fresh)

**Questions:**

| Phase | Questions |
|-------|-----------|
| Original hiring | "When you first signed up, what were you hoping to accomplish?" |
| Experience | "How well did we help you with that?" |
| The turn | "When did you start thinking about leaving?" |
| Alternatives | "What will you do instead? How did you find it?" |
| The switch | "What ultimately convinced you to leave?" |
| Retrospective | "If we could change one thing, what would make you stay?" |

### Churn Patterns to Watch

| Pattern | Probable Cause | Investigation |
|---------|----------------|---------------|
| Early churn (<30 days) | Never got job done | Onboarding + activation issues |
| Churn after initial success | Job completed, no ongoing need | Is this a one-time job? |
| Churn after competitor mention | Better employee exists | Competitive analysis |
| Churn with "too complicated" | Friction > value | UX and simplification |
| Churn without replacement | Job deprioritized | Were we targeting right customers? |

### Acting on Churn Insights

**If job changed:** Consider segments, expansion products, or accepting churn as natural
**If competitor wins:** Investigate which dimension they're serving better
**If job wasn't done:** Product or onboarding needs improvement
**If friction accumulated:** UX improvements, training, simplification
**If priorities shifted:** May be targeting wrong customer profile
