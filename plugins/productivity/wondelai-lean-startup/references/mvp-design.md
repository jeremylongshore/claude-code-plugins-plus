# MVP Design Guide

A Minimum Viable Product is not a minimal product. It is the smallest experiment that lets you collect the maximum amount of validated learning about customers with the least effort. The purpose of an MVP is to test a fundamental business hypothesis, not to satisfy customers or generate revenue (though both may happen). Every design decision about the MVP should flow from a single question: what do we need to learn, and what is the fastest way to learn it?

## MVP Types in Detail

### Concierge MVP

Deliver the product experience entirely by hand to a small number of customers. No technology. No automation. Just humans doing the work the software would eventually do.

**How it works:** Find 5-10 target customers. Manually deliver the service your product would automate. Charge for it (or at least get commitment). Observe what customers actually value.

**Real example:** Food on the Table founder Manuel Rosso personally created grocery lists and meal plans for one family by visiting their home, learning their preferences, and checking local store sales. He scaled from 1 to dozens of families before writing a line of code.

**Best for:** Service-based products, marketplace supply/demand validation, understanding workflows.

**Strengths:** Deep customer insight, immediate feedback, zero technical risk.

**Limitations:** Does not scale. Cannot test technical feasibility. Labor-intensive.

### Wizard of Oz MVP

The customer sees what appears to be a working product, but behind the scenes, humans perform the work manually.

**How it works:** Build the front-end experience (website, app, chatbot). When the customer interacts, a human fulfills the request instead of software.

**Real example:** Zappos founder Nick Swinmurn posted photos of shoes from local stores on a website. When someone ordered, he went to the store, bought the shoes, and shipped them. Customers thought they were buying from an online retailer.

**Best for:** Testing demand and user experience before building the back-end. Products where the interface matters but the engine is complex.

**Strengths:** Tests real purchasing behavior. Feels like a real product. Can validate pricing.

**Limitations:** Requires front-end build. Hard to sustain for high-volume use cases.

### Smoke Test (Landing Page) MVP

A marketing page that describes the product and captures a commitment signal (email, pre-order, click) before the product exists.

**How it works:** Create a landing page with a clear value proposition, feature descriptions, and a call-to-action. Drive targeted traffic. Measure conversion rate.

**Real example:** Buffer's Joel Gascoigne created a landing page describing a social media scheduling tool with a pricing page. When visitors clicked a plan, they saw "we're not quite ready yet" and an email signup. Enough signups validated demand before development began.

**Best for:** Validating demand and value proposition. Testing messaging and positioning. Gauging willingness to pay.

**Strengths:** Fast (can be live in hours). Cheap. Generates quantitative data.

**Limitations:** Measures intent, not behavior. No product learning. Can produce false positives with compelling copy.

### Single Feature MVP

Build one core feature exceptionally well rather than many features poorly.

**How it works:** Identify the single feature that best tests your value hypothesis. Build only that feature. Strip away everything else (no settings, no profiles, no dashboards).

**Real example:** Early Foursquare launched with just one feature: check-ins. No recommendations, no city guides, no brand pages. Just the ability to check in at a location and see who else was there.

**Best for:** Products where the core interaction is the hypothesis. When you need real usage data, not just intent.

**Strengths:** Tests actual product behavior. Generates real usage metrics. Can evolve into the actual product.

**Limitations:** Requires real development work. Risk of scope creep.

### Piecemeal MVP

Combine existing tools, platforms, and services to deliver the product experience without building custom technology.

**How it works:** Stitch together Airtable, Zapier, Typeform, Calendly, Stripe, email, and other off-the-shelf tools to create a functional product.

**Real example:** Groupon started as a WordPress blog with manually generated PDF coupons emailed to subscribers. The "platform" was a blog, an email list, and Apple Mail.

**Best for:** Validating the full customer journey. Products that integrate existing capabilities in a new way.

**Strengths:** Very fast to build. Low cost. Tests real customer behavior.

**Limitations:** Clunky user experience. Hard to scale. Maintenance overhead with multiple tools.

### Video MVP

A video demonstration of how the product works (or would work), used to gauge interest and explain complex value propositions.

**How it works:** Create a 2-4 minute video showing the product in action (can be real, simulated, or animated). Share it with the target audience. Measure engagement, shares, signups, or pre-orders.

**Real example:** Dropbox created a 3-minute screencast demonstrating the file-syncing experience. The video drove their beta waitlist from 5,000 to 75,000 overnight. The product barely worked at the time.

**Best for:** Products with complex value propositions. Technical products hard to explain in text. Viral consumer products.

**Strengths:** Can go viral. Explains complex products quickly. Low build cost.

**Limitations:** Measures interest, not commitment. Production quality matters. Does not test actual usage.

### Pre-Order MVP

Ask customers to pay before the product exists.

**How it works:** Describe the product. Set a price. Accept payment (or refundable deposits). Deliver later if funded.

**Real example:** Pebble Watch raised over $10 million on Kickstarter before manufacturing a single unit. 68,929 people pre-ordered based on renderings and a prototype video.

**Best for:** Hardware products. High-commitment purchase decisions. Validating willingness to pay at a specific price.

**Strengths:** Strongest signal of demand (actual money). Can fund development. Tests pricing.

**Limitations:** Sets delivery expectations. Legal and ethical obligations. Reputational risk if you cannot deliver.

## MVP Type Decision Matrix

| Situation | Recommended MVP Types | Why |
|-----------|----------------------|-----|
| Uncertain if problem exists | Concierge, Smoke Test | Direct customer contact reveals real vs imagined problems |
| Problem validated, solution uncertain | Wizard of Oz, Single Feature | Test the actual solution experience |
| Solution clear, demand uncertain | Smoke Test, Video, Pre-Order | Measure market-level interest |
| Complex B2B workflow | Concierge, Piecemeal | Must understand workflow before automating |
| Consumer mobile app | Single Feature, Video, Smoke Test | Consumer attention is scarce; test one hook |
| Marketplace | Concierge (supply side), Smoke Test (demand side) | Must validate both sides separately |
| Hardware product | Video, Pre-Order, Wizard of Oz | Physical prototyping is expensive; validate demand first |
| API / developer tool | Single Feature, Piecemeal | Developers want working tools, not promises |

## MVP Sizing: How Small Is Too Small?

### The Lower Bound

An MVP is too small when it cannot generate the data needed to make a decision. Ask:

- Can a customer understand the value proposition?
- Can a customer take a meaningful action (sign up, pay, use)?
- Can you distinguish signal from noise in the data?

If the answer to any of these is no, the MVP is too small.

### The Upper Bound

An MVP is too big when it includes anything that does not directly serve the current hypothesis. Warning signs:

- You are building features "while we are at it"
- The build phase exceeds 3-4 weeks
- You are debating polish, edge cases, or error handling
- You are building for scale before validating demand

### The Right Size

| Stage | Appropriate MVP Scope | Time to Build |
|-------|----------------------|---------------|
| Problem validation | Landing page, customer interviews, concierge for 5 customers | 1-5 days |
| Solution validation | Wizard of Oz, clickable prototype, single feature for 20 users | 1-3 weeks |
| Business model validation | Piecemeal MVP, pre-order campaign, working product for 50-100 users | 2-4 weeks |
| Growth validation | Instrumented product for 500+ users with A/B testing capability | 4-8 weeks |

## MVP Design Canvas

Use this canvas to design your next MVP:

```
MVP DESIGN CANVAS
=================

1. HYPOTHESIS
   What we believe: ____________________
   For whom: ____________________
   The riskiest assumption: ____________________

2. MVP TYPE
   Selected type: ____________________
   Why this type: ____________________

3. SCOPE
   Included:
   - ____________________
   - ____________________
   - ____________________

   Explicitly excluded:
   - ____________________
   - ____________________

4. SUCCESS CRITERIA
   Primary metric: ____________________
   Success threshold: ____________________
   Sample size needed: ____________________
   Time to collect data: ____________________

5. BUILD PLAN
   Resources needed: ____________________
   Time-box: ____________________
   Launch date: ____________________

6. RISK MITIGATION
   Biggest risk: ____________________
   Mitigation: ____________________
```

## Common MVP Mistakes

### Mistake 1: The Feature-Stuffed MVP

**What happens:** Team builds 15 features because "users expect a complete product." The build takes 4 months. When it launches, they cannot tell which feature drove engagement.

**Fix:** One hypothesis per MVP. One primary metric. If you cannot explain the MVP in one sentence, it is too complex.

### Mistake 2: The Invisible MVP

**What happens:** Team builds something minimal but shows it to no one. "We need to make it a little better first."

**Fix:** Set a launch date before you start building. Announce it publicly. Ship on that date regardless of how "ready" it feels.

### Mistake 3: The Wrong Audience MVP

**What happens:** Team tests the MVP with friends, family, or colleagues instead of actual target customers.

**Fix:** Define your early adopter profile before building. Recruit from channels where real customers exist. Friends will tell you what you want to hear.

### Mistake 4: The No-Metric MVP

**What happens:** Team launches the MVP but has no instrumentation. Learning is based on gut feel and anecdotes.

**Fix:** Define your metric and instrument the MVP before launch. Use analytics tools, manual tracking, or direct observation. Data collection is not optional.

### Mistake 5: The Perfectionist MVP

**What happens:** Team keeps polishing because "our brand reputation is at stake." MVP never launches.

**Fix:** Remember that the MVP is for early adopters, not the mass market. Early adopters tolerate rough edges if the core value is there. Use a separate brand if reputation is a concern.

### Mistake 6: The Scale-Ready MVP

**What happens:** Team builds for 100,000 users when they need 100. Invests in infrastructure, security, and compliance before validating demand.

**Fix:** Do things that do not scale. Manual processes are fine. Technical debt is acceptable. Scaling problems are a luxury you earn by proving demand.

## From MVP to Product: Graduation Criteria

An MVP graduates to product development when:

| Criterion | Signal | Threshold Example |
|-----------|--------|-------------------|
| Problem-Solution Fit | Customers actively use the MVP and express disappointment at the idea of losing it | 40%+ say "very disappointed" on Sean Ellis test |
| Repeatable Demand | New customers arrive through identifiable, repeatable channels | 3+ consistent acquisition channels |
| Willingness to Pay | Customers pay (or demonstrate clear intent) at a sustainable price point | Positive unit economics on paper |
| Retention | Customers return and use the product repeatedly | Week 4 retention above 20% (varies by category) |
| Organic Growth | Some customers refer others without prompting | Viral coefficient above 0.2 |

### Graduation Checklist

- [ ] Core value hypothesis validated with paying customers
- [ ] Growth hypothesis has initial evidence
- [ ] Unit economics are viable (or have a clear path to viability)
- [ ] Early adopters are retained and engaged
- [ ] The team can articulate what they learned and why they are confident
- [ ] At least 3 Build-Measure-Learn loops have been completed
- [ ] Pivot or persevere decision has been explicitly made (and persevere was chosen)

Do not graduate the MVP prematurely. The most expensive mistake in startups is scaling something that has not been validated.
