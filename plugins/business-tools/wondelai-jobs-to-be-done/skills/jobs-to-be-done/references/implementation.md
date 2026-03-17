# Jobs to Be Done - Implementation Guide

Step-by-step methodology for discovering what customers truly need by understanding the "job" they hire your product to do.

## Step 1: Define the Job Statement

A Job to Be Done is not a feature, a task, or a demographic. It is a statement of desired progress.

**Job statement format:**
```
When [situation], I want to [motivation], so I can [expected outcome].
```

Examples:
- "When I need to align my team before a big meeting, I want to quickly share context, so I can spend the meeting solving problems instead of briefing everyone."
- "When I'm choosing a restaurant for a client dinner, I want to find somewhere impressive and reliably good, so I can make a strong impression without surprises."

**Anti-patterns to avoid:**
- Too feature-specific: "I want to create a Gantt chart" (this is a solution, not a job)
- Too broad: "I want to be more productive" (this is a life goal, not a job)
- Too demographic: "As a project manager..." (this is context, not the job itself)

## Step 2: Conduct JTBD Switch Interviews

The most valuable JTBD data comes from customers who recently made a purchase decision — especially those who switched from something else.

**2a. Who to interview**
- Recent converters (within 90 days): they remember the decision
- Recent churners: they just fired your product — why?
- People who considered you but chose a competitor

**2b. The switch interview structure (60 minutes)**

Phase 1 — First thought (10 min):
- "Tell me about the moment you first thought 'I need to do something about this.'"
- "What was happening in your life/work at that point?"

Phase 2 — Passive looking (15 min):
- "What did you try before you started actively looking for solutions?"
- "How long did you tolerate the situation before deciding to change it?"

Phase 3 — Active looking (15 min):
- "Walk me through how you searched for solutions."
- "What did you evaluate? What did you rule out and why?"

Phase 4 — Decision (10 min):
- "What was the moment you decided to choose [product]?"
- "Was there anyone else involved in the decision?"

Phase 5 — Consumption (10 min):
- "What happened the first time you used it?"
- "Were there any surprises — good or bad?"

**2c. What to listen for**
- Emotional language: anxiety, relief, excitement, frustration — these signal the job's importance
- Causality: what pushed them, what pulled them toward the solution
- The "first thought" moment: this is when the job became active and they started looking for a solution

## Step 3: Map the Forces of Progress

Every purchase decision involves four forces:

```
PUSH forces (away from current solution):
  - Frustrations with existing approach
  - Anxieties about continuing to use it
  - Trigger event that made the problem urgent

PULL forces (toward new solution):
  - Attraction to new possibilities
  - Relief from the current pain
  - Desire for the outcome the new product promises

ANXIETIES about switching:
  - Fear of it not working
  - Cost and effort of switching
  - Fear of looking foolish

HABITS holding them back:
  - "This is how we've always done it"
  - Inertia, comfort with the existing approach
```

After interviews, map each customer's statement to these four forces. The job is won when push + pull > anxieties + habits.

**Use this to improve your product and marketing:**
- If push > pull in interviews: your marketing isn't compelling enough; strengthen the vision
- If anxieties are high: your onboarding or guarantee needs work
- If habits dominate: you need stronger urgency triggers or a compelling forcing function

## Step 4: Identify Competing Solutions

In JTBD, competitors are not just other products in your category — they are anything the customer might "hire" instead.

**4a. List all competing solutions**
- Direct competitors (other products doing the same job)
- Adjacent competitors (other products hired for a similar job)
- Non-consumption (doing nothing; the status quo)
- Workarounds (spreadsheets, manual processes, duct-tape solutions)

**4b. Understand why workarounds persist**
- If customers are using a complex spreadsheet instead of your product, the spreadsheet is winning on: autonomy, familiarity, zero switching cost, or capability
- Do not dismiss workarounds. Study them. They reveal what the customer truly values.

**4c. Map the job to be hired on a timeline**
- When does the job become active? (trigger event)
- How long does the customer actively look?
- What is the decision-making process?

Understanding the buying journey prevents you from marketing to people who aren't in the "active looking" phase yet.

## Step 5: Segment by Job, Not Demographics

Traditional segmentation groups customers by who they are (age, company size, industry). JTBD segments by what they're trying to accomplish.

**5a. Create job-based segments**
- Group interview insights by job type, not customer profile
- You may find that the same demographic hires your product for completely different jobs
- Example: Slack is hired by some teams for "reduce email volume" and by others for "build remote culture" — very different jobs

**5b. Build job-based personas**
- Replace demographic personas with "jobs personas":
  - The job: "When..."
  - The context: what their day looks like when this job is active
  - The competing solutions they consider
  - Their anxieties about switching
  - Their definition of success (what does the job "done" look like?)

**5c. Prioritize your most valuable job**
- Which job are you best positioned to serve?
- Which job, if won, creates the most expansion revenue or referrals?
- Which job is most underserved by existing solutions?

## Step 6: Apply JTBD to Product Decisions

**6a. Evaluate feature requests through JTBD lens**
- Before building any feature, ask: "What job does this help the customer do?"
- If no clear job → de-prioritize
- If a job is identified → validate with 5 customers who have that job

**6b. Write job-based success criteria for features**
- Instead of: "Users can export to CSV"
- Write: "When a customer needs to share results with a stakeholder who doesn't use our tool, they can export cleanly and quickly so the stakeholder sees professional output"

**6c. Use JTBD for messaging**
- Your marketing should describe the job and the outcome, not just the feature
- Bad: "Export to 12 formats"
- Good: "Share results your clients actually open"

## Common Pitfalls

| Mistake | Consequence | Fix |
|---------|------------|-----|
| Surveying customers instead of interviewing | Surface-level data, no causal insight | Do 1:1 switch interviews, not surveys |
| Asking about wants (features) instead of jobs | Gets feature requests, not insight | Ask about the moment a need arose, not what they'd like to see |
| Conflating usage with hiring | High usage doesn't mean the right job | Interview churners, not just power users |
| Single job assumption | Leaves segments unserved | Map multiple jobs and decide which to optimize for |
| Using demographic segmentation for product strategy | Leads to demographic features, not job solutions | Segment by job, build for the job |

## Quick-Start Checklist

- [ ] Job statement written in "When/I want to/So I can" format
- [ ] 5+ switch interviews scheduled (recent purchasers and churners)
- [ ] Interview guide prepared with 5-phase structure
- [ ] Four forces mapped for at least 3 customers
- [ ] Competing solutions list includes non-consumption and workarounds
- [ ] Job-based segments created (not demographic segments)
- [ ] Top feature request evaluated through JTBD lens
- [ ] One piece of marketing copy rewritten using job language
