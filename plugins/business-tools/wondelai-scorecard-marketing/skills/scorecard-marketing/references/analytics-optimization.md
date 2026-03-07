# Scorecard Analytics & Optimization

Metrics, A/B testing elements, funnel analysis, and CRM integration for scorecard marketing.

## Key Metrics to Track

### Landing Page Metrics

| Metric | Benchmark | What It Indicates |
|--------|-----------|-------------------|
| Page views | - | Total traffic |
| Unique visitors | - | Reach |
| Start rate | 30-50% | Landing page effectiveness |
| Time on page | 30-90s | Engagement before starting |
| Bounce rate | <50% | First impression quality |
| Traffic source conversion | Varies | Channel effectiveness |

### Questionnaire Metrics

| Metric | Benchmark | What It Indicates |
|--------|-----------|-------------------|
| Completion rate | 60-80% | Questionnaire design quality |
| Average time to complete | 2-5 min | Question difficulty/length |
| Drop-off by question | Varies | Problem questions |
| Skip rate (if allowed) | <10% | Question clarity |
| Email capture rate | 70-90% | Lead form positioning |

### Results Page Metrics

| Metric | Benchmark | What It Indicates |
|--------|-----------|-------------------|
| PDF download rate | 30-50% | Results page value |
| Time on results | 1-3 min | Engagement with recommendations |
| CTA click rate | 15-30% | Offer relevance |
| Share rate | 5-10% | Viral potential |
| Return visits | 10-20% | Ongoing interest |

### Conversion Metrics

| Metric | Benchmark | What It Indicates |
|--------|-----------|-------------------|
| Lead-to-opportunity | 10-30% | Lead quality |
| Opportunity-to-close | 20-40% | Sales effectiveness |
| Sales cycle length | Varies | Purchase complexity |
| Revenue per lead | Varies | Overall funnel value |

---

## A/B Testing Elements

### High-Impact Elements to Test

| Element | Hypothesis Examples | Typical Impact |
|---------|---------------------|----------------|
| **Headline** | Outcome-focused vs. process-focused | 20-50% |
| **Concept hook** | Different scoring angles | 30-100% |
| **Number of questions** | Shorter vs. longer | 10-30% |
| **Question order** | Easy-first vs. hard-first | 5-15% |
| **Lead form placement** | Before vs. after questions | 20-40% |
| **Results presentation** | Score-first vs. insights-first | 10-25% |
| **CTA on results** | Single vs. multiple options | 15-35% |

### Testing Priorities (ICE Framework)

**Test first (high impact, easy):**
- Headline copy
- CTA button text
- Lead form fields (less = more conversion)
- Result page CTA

**Test second (high impact, moderate effort):**
- Number of questions
- Question wording
- Results page layout
- Email subject lines

**Test later (lower impact or harder):**
- Visual design elements
- Animation/transitions
- Gamification elements
- Advanced personalization

### What NOT to A/B Test

- Questions that affect scoring (changes data meaning)
- Core scoring logic (unless starting fresh)
- Brand elements (logo, colors)
- Compliance/legal text

---

## Funnel Analysis Framework

### The Scorecard Funnel

```
Traffic → Landing Page → Start Quiz → Complete Questions → Email Capture → Results View → CTA Click → Sale
```

### Identifying Bottlenecks

| Stage | Healthy Rate | Warning Signs |
|-------|--------------|---------------|
| Landing → Start | >30% | <20%: Landing page problem |
| Start → Complete | >60% | <40%: Question/UX problem |
| Complete → Email | >70% | <50%: Value proposition problem |
| Email → Results | >80% | <60%: Delivery problem |
| Results → CTA | >15% | <10%: Results/offer mismatch |

### Question-Level Drop-off Analysis

Track completion rate at each question:

```
Q1: 100% →
Q2: 95% →
Q3: 88% →
Q4: 85% →
Q5: 70% → ← Problem question
Q6: 68% →
Q7: 65% →
```

**Fix problem questions by:**
- Simplifying wording
- Changing from open text to multiple choice
- Reordering (move difficult questions later)
- Making optional
- Removing entirely

### Cohort Analysis

Compare performance across:
- Traffic sources
- Time periods
- Score segments
- Demographic segments

Example insight: "LinkedIn traffic has 40% higher completion rate but 20% lower CTA click rate—they engage but need different offer."

---

## Score-Based Segmentation

### Segment Definitions

| Segment | Score Range | Characteristics | Follow-up Strategy |
|---------|-------------|-----------------|-------------------|
| **Low scorers** | 0-33% | Need fundamentals | Educational content, introductory offers |
| **Mid scorers** | 34-66% | Have foundation, gaps to fill | Specific solutions, consultation |
| **High scorers** | 67-100% | Advanced, optimization focused | Premium offers, strategic services |

### Category-Level Segmentation

Beyond total score, segment by category scores:

```
Marketing Score: 85% | Operations: 45% | Finance: 70%

Insight: Strong marketing, weak operations—target operations content/services
```

### Behavioral Segments

| Segment | Behavior | Strategy |
|---------|----------|----------|
| **Quick completers** | <2 min | May be rushed—send detailed PDF |
| **Thorough completers** | >5 min | Engaged—offer consultation |
| **PDF downloaders** | Downloaded report | Ready for deeper content |
| **CTA clickers** | Clicked but didn't convert | Send reminder/objection handling |
| **Returners** | Multiple quiz completions | Highly interested—priority follow-up |

---

## CRM Integration

### Data to Capture

**Standard fields:**
- Name, email, phone
- Total score
- Category scores
- Completion timestamp
- Traffic source

**Custom fields:**
- Individual question responses (high-value questions)
- Score tier (Low/Medium/High)
- Key qualifying answers
- Time to complete

### Lead Scoring Integration

Map scorecard results to CRM lead scores:

| Scorecard Element | CRM Points |
|-------------------|------------|
| High overall score | +20 |
| Urgent timeline selected | +15 |
| Large company size | +10 |
| Budget confirmed | +25 |
| Low score in service area | +10 |
| Downloaded PDF | +5 |
| Clicked consultation CTA | +30 |

### Workflow Triggers

| Trigger | Action |
|---------|--------|
| Quiz completed | Add to nurture sequence |
| High score + clicked CTA | Route to sales immediately |
| Low score | Send educational content first |
| Quiz abandoned | Send completion reminder (24h) |
| PDF downloaded | Send related content (3 days) |
| CTA clicked, not converted | Send reminder (48h) |

### Integration Best Practices

1. **Map fields before launch** - Plan CRM fields and tags in advance
2. **Test data flow** - Submit test entries through entire flow
3. **Avoid data overload** - Don't capture every answer—focus on actionable data
4. **Enable scoring flexibility** - Build in ability to adjust lead scoring

---

## Optimization Playbook

### Weekly Review Checklist

- [ ] Check completion rate (target: >60%)
- [ ] Review question drop-off points
- [ ] Compare conversion by traffic source
- [ ] Check email delivery rates
- [ ] Review CTA click rates by score tier
- [ ] Monitor qualification rate from sales

### Monthly Optimization Actions

| If... | Then... |
|-------|---------|
| Start rate <30% | A/B test headline, add testimonials |
| Completion rate <60% | Reduce questions, improve UX |
| CTA click <15% | Test different offers per tier |
| Lead quality complaints | Add qualifying questions |
| Low engagement scores | Improve results page content |

### Quarterly Review

1. **Full funnel audit** - Map conversion at every stage
2. **Question performance** - Which questions predict conversion?
3. **Offer alignment** - Are tier-specific offers converting?
4. **Benchmark comparison** - Compare to industry averages
5. **Score distribution** - Is scoring differentiating effectively?

---

## Advanced Tracking

### UTM Parameters

Track traffic sources with consistent UTM tagging:

```
?utm_source=linkedin
&utm_medium=organic
&utm_campaign=scorecard_2024
&utm_content=post_v1
```

Capture and store UTMs with lead data for attribution.

### Event Tracking Setup

| Event | Trigger | Data to Capture |
|-------|---------|-----------------|
| `quiz_started` | First question shown | utm params, timestamp |
| `question_answered` | Answer selected | question_id, answer_value, time_spent |
| `email_submitted` | Form submitted | email, name |
| `results_viewed` | Results page loaded | total_score, category_scores |
| `pdf_downloaded` | PDF button clicked | score tier |
| `cta_clicked` | Main CTA clicked | offer_type, score_tier |

### Heatmap and Session Recording

Use tools like Hotjar or FullStory to:
- Watch real users complete the quiz
- Identify confusion points
- See where users hover/pause
- Understand results page engagement

---

## Reporting Dashboard

### Executive Summary Metrics

```
┌──────────────────────────────────────────────────────────────┐
│ SCORECARD PERFORMANCE (Last 30 Days)                         │
├──────────────────────────────────────────────────────────────┤
│ Visitors:        5,234    │  Leads Generated:     1,832     │
│ Start Rate:      45.2%    │  Lead Quality Score:  7.4/10    │
│ Completion Rate: 77.4%    │  CTA Click Rate:      23.1%     │
│ Lead Cost:       $2.47    │  Pipeline Generated:  $127,500  │
└──────────────────────────────────────────────────────────────┘
```

### Trend Charts

- Weekly lead volume and quality
- Conversion rates over time
- Score distribution changes
- Traffic source performance

### Actionable Alerts

Set alerts for:
- Completion rate drops >10%
- Lead quality score drops
- Significant traffic spikes (opportunity to capitalize)
- Unusual drop-off patterns
