# Leap-of-Faith Assumptions

Every startup is built on a stack of unproven assumptions. Most founders treat these assumptions as facts. The Lean Startup treats them as hypotheses that must be tested systematically. Leap-of-faith assumptions are the assumptions that must be true for the business to succeed but have the least evidence supporting them. Identifying, prioritizing, and testing these assumptions is the foundation of validated learning.

## Value Hypothesis vs Growth Hypothesis

The two most critical assumptions for any new product:

### Value Hypothesis

Tests whether the product delivers value to customers once they start using it.

**Core question:** Do customers find this product valuable enough to keep using it (and eventually pay for it)?

| Dimension | What to Validate | Example Signals |
|-----------|-----------------|-----------------|
| Problem existence | The problem is real and painful enough to motivate action | Customers describe the problem unprompted in interviews |
| Solution fit | Your specific solution addresses the problem effectively | Users complete core tasks successfully; retention is strong |
| Willingness to pay | Customers value the solution enough to exchange money for it | Pre-orders, paid pilots, conversion from free to paid |
| Frequency | Customers need the solution repeatedly, not just once | Return usage within expected timeframe |

### Growth Hypothesis

Tests how new customers discover and adopt the product.

**Core question:** How will this product spread from early adopters to a broader market?

| Dimension | What to Validate | Example Signals |
|-----------|-----------------|-----------------|
| Discoverability | Target customers can find the product | Organic search traffic, word-of-mouth referrals |
| Acquisition cost | You can acquire customers at a sustainable cost | CAC below projected LTV |
| Virality | Existing users bring in new users | Viral coefficient, referral rates, social sharing |
| Market size | Enough potential customers exist | TAM analysis validated by early traction patterns |

**Critical insight:** Validate the value hypothesis before the growth hypothesis. Growing something people do not value is the most expensive way to fail.

## Assumption Mapping

### Step 1: List All Assumptions

Brainstorm every assumption your business relies on. Use these categories as prompts:

**Customer assumptions:**
- Our target customer is [specific persona]
- They experience [specific problem]
- They currently solve it by [current alternative]
- They are dissatisfied with the current solution because [reason]

**Problem assumptions:**
- The problem is frequent enough to justify a solution
- The problem is painful enough that people will pay to solve it
- The problem is not adequately solved by existing alternatives

**Solution assumptions:**
- Our solution effectively addresses the problem
- Customers can use our solution without extensive training
- The solution is significantly better than alternatives

**Business model assumptions:**
- Customers will pay [price] for this solution
- We can acquire customers for less than [amount]
- Customer lifetime value exceeds acquisition cost
- Our market is large enough to build a viable business

**Technical assumptions:**
- We can build this technology with our team
- The technology can scale to serve our target market
- Performance will meet customer expectations

### Step 2: Prioritize With the Impact-Uncertainty Matrix

Plot each assumption on a 2x2 matrix:

```
                    HIGH IMPACT
                        |
         TEST FIRST     |     MONITOR
      (High Impact,     |  (High Impact,
       High Uncertainty) |   Low Uncertainty)
                        |
  HIGH UNCERTAINTY -----+------ LOW UNCERTAINTY
                        |
         EXPLORE        |      IGNORE
      (Low Impact,      |   (Low Impact,
       High Uncertainty) |   Low Uncertainty)
                        |
                    LOW IMPACT
```

**Test First (top-left):** These are your leap-of-faith assumptions. If wrong, the business fails. And you have little evidence they are true. Test these immediately.

**Monitor (top-right):** Important but you have reasonable evidence. Keep an eye on them but do not spend experiment cycles here yet.

**Explore (bottom-left):** Uncertain but not critical. Explore casually through customer conversations.

**Ignore (bottom-right):** Low impact and well-understood. Move on.

## Assumption Prioritization Scoring

For a more structured approach, score each assumption:

| Assumption | Impact (1-5) | Uncertainty (1-5) | Priority Score | Test Order |
|-----------|-------------|-------------------|---------------|------------|
| Customers will pay $29/month | 5 | 5 | 25 | 1 |
| Problem is frequent (weekly+) | 5 | 4 | 20 | 2 |
| Can acquire via content marketing | 4 | 4 | 16 | 3 |
| Team can build ML model | 4 | 3 | 12 | 4 |
| Users will share with colleagues | 3 | 4 | 12 | 5 |
| Market size is $1B+ | 3 | 2 | 6 | 6 |

**Impact (1-5):** How critical is this assumption to the business succeeding?
**Uncertainty (1-5):** How little evidence do you have?
**Priority Score:** Impact multiplied by Uncertainty. Higher score = test sooner.

## Testing Methods by Assumption Type

### Customer Existence Assumptions

| Method | Duration | Cost | Signal Strength |
|--------|----------|------|-----------------|
| Customer discovery interviews (20+) | 2-3 weeks | Low | Medium |
| Landing page with targeted ads | 1-2 weeks | Low-Medium | Medium-High |
| Community/forum observation | 1 week | Free | Medium |
| Competitor customer analysis | 1 week | Free | Low-Medium |
| Survey to target demographic | 1-2 weeks | Low | Low (stated vs revealed preference) |

### Problem Severity Assumptions

| Method | Duration | Cost | Signal Strength |
|--------|----------|------|-----------------|
| Problem interviews (focus on current behavior) | 2-3 weeks | Low | High |
| Current spending on alternatives | 1 week | Free | High |
| Time spent on workarounds | 1-2 weeks | Low | High |
| Support ticket analysis (competitor or own) | 1 week | Free | Medium |
| Job-to-be-done interviews | 2-3 weeks | Low | High |

### Solution Effectiveness Assumptions

| Method | Duration | Cost | Signal Strength |
|--------|----------|------|-----------------|
| Concierge MVP (5-10 customers) | 2-4 weeks | Low-Medium | Very High |
| Wizard of Oz MVP | 2-4 weeks | Medium | High |
| Clickable prototype usability test | 1-2 weeks | Low | Medium |
| A/B test (existing product) | 1-3 weeks | Low | High |
| Competitor product teardown | 1 week | Low | Low-Medium |

### Business Model Assumptions

| Method | Duration | Cost | Signal Strength |
|--------|----------|------|-----------------|
| Pre-sell / pre-order | 2-4 weeks | Medium | Very High |
| Pricing page test (before product) | 1-2 weeks | Low | High |
| Willingness-to-pay interviews | 1-2 weeks | Low | Medium |
| Competitive pricing analysis | 1 week | Free | Low-Medium |
| Paid pilot with letter of intent | 2-6 weeks | Medium | Very High |

### Growth Assumptions

| Method | Duration | Cost | Signal Strength |
|--------|----------|------|-----------------|
| Paid acquisition test ($500-2000) | 1-2 weeks | Medium | High |
| Referral program MVP | 2-4 weeks | Low | High |
| Content marketing experiment | 4-8 weeks | Low | Medium |
| Partnership outreach (10+ partners) | 2-4 weeks | Low | Medium |
| Viral loop prototype | 2-3 weeks | Medium | High |

## Assumption Mapping Template

```
ASSUMPTION MAP
==============
Product: ____________________
Date: ____________________
Team: ____________________

LEAP-OF-FAITH ASSUMPTIONS (Test First)
---------------------------------------
1. Assumption: ____________________
   Category: [ ] Customer  [ ] Problem  [ ] Solution  [ ] Business Model  [ ] Growth
   Impact: ___/5    Uncertainty: ___/5    Priority: ___
   Test method: ____________________
   Success criteria: ____________________
   Timeline: ____________________

2. Assumption: ____________________
   Category: [ ] Customer  [ ] Problem  [ ] Solution  [ ] Business Model  [ ] Growth
   Impact: ___/5    Uncertainty: ___/5    Priority: ___
   Test method: ____________________
   Success criteria: ____________________
   Timeline: ____________________

3. Assumption: ____________________
   Category: [ ] Customer  [ ] Problem  [ ] Solution  [ ] Business Model  [ ] Growth
   Impact: ___/5    Uncertainty: ___/5    Priority: ___
   Test method: ____________________
   Success criteria: ____________________
   Timeline: ____________________

IMPORTANT BUT LESS UNCERTAIN (Monitor)
--------------------------------------
4. ____________________
5. ____________________

EXPLORE LATER
-------------
6. ____________________
7. ____________________
```

## Industry-Specific Common Assumptions

### SaaS

| Assumption | Typical Risk Level | Testing Approach |
|-----------|-------------------|------------------|
| Users will adopt a new tool (switching cost) | High | Free trial conversion rate |
| Monthly subscription is preferred over annual | Medium | Pricing page A/B test |
| Self-serve onboarding is sufficient | High | Onboarding completion funnel |
| Integration with existing tools is required | Medium | Customer interviews about workflow |
| Freemium will drive paid conversions | High | Cohort analysis of free-to-paid |
| SMBs will pay without a sales call | Medium | Self-serve purchase funnel test |

### Marketplace

| Assumption | Typical Risk Level | Testing Approach |
|-----------|-------------------|------------------|
| Supply side will join the platform | Very High | Manual recruitment of 20-50 suppliers |
| Demand exists at the listed price | High | Smoke test landing page |
| Both sides show up at the same time | Very High | Single-geography concierge test |
| Trust can be established between strangers | High | Review/rating system MVP |
| Take rate is acceptable to both sides | Medium | Pricing experiments with early users |
| Network effects will kick in at scale | High | Measure engagement vs density |

### B2B Enterprise

| Assumption | Typical Risk Level | Testing Approach |
|-----------|-------------------|------------------|
| Budget holder will champion internally | Very High | Pilot with 3-5 companies |
| IT will approve the integration | High | Technical review with 5 IT leaders |
| ROI justifies the price point | High | Case study from pilot |
| Procurement timeline is acceptable | Medium | Sales cycle measurement |
| End users will adopt without mandate | High | User adoption in pilot companies |
| Data security requirements can be met | Medium | Security audit and certification plan |

### Consumer Mobile

| Assumption | Typical Risk Level | Testing Approach |
|-----------|-------------------|------------------|
| Users will download yet another app | Very High | App store listing test or landing page |
| Daily active usage will occur | Very High | Day-1, Day-7, Day-30 retention cohorts |
| Notifications will not be disabled | High | Notification opt-in rate tracking |
| Users will create content/data | High | First-session completion rate |
| Monetization will not kill engagement | High | A/B test monetization features |
| Organic sharing will occur | Medium | Share button usage, invite rate |

## From Assumptions to Experiments

### The Bridge

Each high-priority assumption must be converted into a testable experiment using this process:

1. **State the assumption clearly.** "We assume that ____."
2. **Identify the riskiest element.** What part of this assumption, if wrong, would be most damaging?
3. **Formulate a falsifiable hypothesis.** "If we ____, then ____ will happen within ____."
4. **Choose the fastest test method.** What is the minimum effort that generates a meaningful signal?
5. **Set pass/fail criteria in advance.** "Success = ____. Failure = ____."
6. **Run the experiment.**
7. **Record the result and decide.** Persevere, pivot, or dig deeper.

### Example Bridge

**Assumption:** Remote teams need asynchronous video messaging.

**Riskiest element:** Do remote teams actually feel pain around asynchronous communication, or are Slack and email sufficient?

**Hypothesis:** If we post a landing page describing async video messaging in 5 remote-work communities, at least 3% of visitors will sign up for the waitlist within 2 weeks.

**Test method:** Landing page with Mailchimp signup. $200 in targeted ads as supplement to organic posts.

**Pass/fail:** Above 3% signup rate with 500+ visitors = proceed. Below 3% = interview signups to understand why, then reassess.

**Result:** 4.2% signup rate. 21 signups. 8 responded to follow-up email. 5 described specific pain points with existing tools.

**Decision:** Assumption partially validated. Proceed to concierge MVP with the 8 respondents to validate solution fit.

### Sequencing Experiments

Test assumptions in this order:

1. **Customer and problem assumptions first.** If the problem does not exist or the customer does not care, nothing else matters.
2. **Solution assumptions second.** Does your approach actually solve the problem?
3. **Business model assumptions third.** Can you make money?
4. **Growth assumptions last.** Can you scale?

This sequence prevents the most expensive mistake: building and scaling a solution to a problem nobody has.
