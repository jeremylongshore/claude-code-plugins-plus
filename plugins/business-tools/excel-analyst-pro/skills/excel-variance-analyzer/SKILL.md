---
name: excel-variance-analyzer
description: |
  Automate budget vs actual variance analysis in Excel with flagging, commentary, and executive summaries for financial reporting and FP&A teams Activates when you request "excel variance analyzer" functionality.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

# Excel Variance Analyzer

Automates variance analysis for monthly/quarterly financial reporting and budget reviews.

## When to Invoke This Skill

Automatically load this Skill when the user asks to:
- "Analyze budget variance"
- "Compare actual vs forecast"
- "Create variance report"
- "Explain budget differences"
- "Why are we over/under budget?"
- "Variance analysis for [period]"
- "Budget vs actual"

## Report Structure

Creates a comprehensive variance report with 3 sheets:

### Sheet 1: Variance Summary
```
| Line Item       | Budget  | Actual  | Variance | % Var | Flag | Commentary |
|-----------------|---------|---------|----------|-------|------|------------|
| Revenue         | $1,000K | $950K   | $(50K)   | -5.0% | ⚠️   | Below plan |
| COGS            | $600K   | $580K   | $(20K)   | -3.3% | ✅   | Favorable  |
| Gross Profit    | $400K   | $370K   | $(30K)   | -7.5% | 🔴   | Investigate|
| Operating Exp   | $250K   | $280K   | $30K     | 12.0% | 🔴   | Over budget|
| EBITDA          | $150K   | $90K    | $(60K)   | -40.0%| 🔴   | Miss       |
```

### Sheet 2: Executive Summary
```
📊 Performance Highlights
- Total Revenue: $950K (5.0% below budget)
- EBITDA: $90K (40.0% below budget)
- Key Driver: Operating expenses 12% over budget

🔴 Top 5 Unfavorable Variances:
1. EBITDA: $(60K) / -40.0%
2. Revenue: $(50K) / -5.0%
3. Operating Expenses: $30K / 12.0%
4. Gross Profit: $(30K) / -7.5%
5. Marketing: $25K / 25.0%

✅ Top 5 Favorable Variances:
1. COGS: $(20K) / -3.3%
2. Rent: $(5K) / -10.0%
3. Utilities: $(2K) / -8.0%
```

### Sheet 3: Trend Analysis (if multiple periods)
```
| Line Item | Jan Var% | Feb Var% | Mar Var% | Q1 Var% | Trend |
|-----------|----------|----------|----------|---------|-------|
| Revenue   | -3%      | -5%      | -7%      | -5%     | ⬇️    |
| COGS      | -2%      | -4%      | -3%      | -3%     | ➡️    |
```

## Step-by-Step Workflow

### 1. Load Data

Ask the user for:
- **Budget data**: Can be Excel file, CSV, or pasted table
- **Actual data**: Same format as budget
- **Period**: Month, quarter, YTD
- **Threshold settings** (or use defaults):
  - Percentage threshold: 10% (flag items >10% variance)
  - Dollar threshold: $50K (flag items >$50K absolute variance)
  - Categories to exclude: (e.g., non-cash items like depreciation)

### 2. Validate Data

Before analysis, check:
- Budget and actual have matching line items
- All values are numeric
- No missing data for key categories (revenue, expenses, profit)
- Budget data is reasonable (no zeros where there should be values)

### 3. Calculate Variances

For each line item:
```
Absolute Variance = Actual - Budget
Percentage Variance = (Actual - Budget) / Budget × 100%

Sign Convention:
- Positive variance for revenue/profit = Favorable (✅)
- Negative variance for revenue/profit = Unfavorable (🔴)
- Positive variance for expenses = Unfavorable (🔴)
- Negative variance for expenses = Favorable (✅)
```

### 4. Flag Material Items

Apply flagging rules:
```
🔴 Red Flag (Critical):
- Revenue/profit >10% below budget
- Expenses >10% over budget
- Absolute variance >$100K

⚠️ Yellow Flag (Warning):
- Revenue/profit 5-10% below budget
- Expenses 5-10% over budget
- Absolute variance $50K-$100K

✅ Green (On Track):
- Variance within ±5%
- Absolute variance <$50K
```

### 5. Generate Commentary

For each flagged item, provide automated commentary:

**Revenue Below Budget:**
```
Revenue is $50K (5%) below budget. Possible drivers:
- Lower than expected sales volume
- Pricing pressure
- Delayed revenue recognition
- Seasonal factors
Recommend: Review sales pipeline and backlog
```

**Expenses Over Budget:**
```
Operating expenses are $30K (12%) over budget. Breakdown:
- Marketing: $25K over (new campaign)
- Travel: $8K over
- Utilities: $2K under
Recommend: Review Q2 marketing spend and ROI
```

**Favorable Variances:**
```
COGS is $20K (3.3%) under budget. Drivers:
- Lower raw material costs
- Improved operational efficiency
- Volume discounts from suppliers
```

### 6. Create Executive Summary

Summarize for leadership:
```
📊 [Period] Financial Performance

Bottom Line:
- Revenue: [X%] vs budget ([favorable/unfavorable])
- EBITDA: [X%] vs budget ([favorable/unfavorable])
- Net Variance Impact: $[XXX]K

Key Takeaways:
1. [Primary driver of miss/beat]
2. [Secondary factor]
3. [Outlook for next period]

Action Items:
1. [Specific action needed]
2. [Follow-up required]
```

## Example Interaction

**User:** "Analyze Q1 budget vs actual"

**Skill Response:**
```
I'll analyze your Q1 variance. Let me load the data.

Do you have budget and actual data files, or would you like to paste them?

User: *pastes Excel data*

Perfect! I see data for Q1 2025. Setting analysis parameters:
- Period: Q1 2025 (Jan-Mar)
- Line items: 15 categories detected
- Materiality threshold: ±10% or ±$50K

Running variance analysis...

✅ Variance Analysis Complete!

📊 Q1 2025 PERFORMANCE SUMMARY

🎯 Overall Results:
- Revenue: $2,850K vs budget $3,000K (-5.0%) 🔴
- Gross Profit: $1,110K vs budget $1,200K (-7.5%) 🔴
- EBITDA: $270K vs budget $450K (-40.0%) 🔴

📉 Key Drivers of Underperformance:
1. Revenue Miss: $(150K) - 5% below plan
   → Slower than expected customer acquisition
   → Delayed Q1 enterprise deals to Q2

2. Operating Expenses Over: $90K - 12% above plan
   → Marketing campaign: $75K incremental spend
   → Headcount additions brought forward to Q1

🔍 Detailed Findings:

🔴 CRITICAL VARIANCES (>10%):
- Operating Expenses: $840K vs $750K (+12.0%) - $90K over
- EBITDA: $270K vs $450K (-40.0%) - $180K under
- Marketing: $325K vs $260K (+25.0%) - $65K over

⚠️ WARNING VARIANCES (5-10%):
- Revenue: $2,850K vs $3,000K (-5.0%) - $150K under
- Gross Profit: $1,110K vs $1,200K (-7.5%) - $90K under

✅ FAVORABLE VARIANCES:
- COGS: $1,740K vs $1,800K (-3.3%) - $60K favorable
- Facilities: $45K vs $50K (-10.0%) - $5K favorable

💡 RECOMMENDATIONS:

Immediate Actions:
1. Review Q2 sales pipeline - need $150K catch-up + Q2 plan
2. Evaluate marketing campaign ROI (Q1 spend +$65K)
3. Assess if Q1 revenue timing shift impacts full-year plan

Strategic Questions:
1. Is Q1 revenue miss timing (shifts to Q2) or lost?
2. Will marketing investment drive Q2-Q4 revenue?
3. Should we adjust full-year budget guidance?

📁 Report saved to: Q1_2025_Variance_Analysis.xlsx

Would you like me to:
- Add trend analysis vs Q4 2024?
- Create forecast scenarios for Q2?
- Drill into specific expense categories?
```

## Common Variations

### Request: "Why is marketing over budget?"

**Response:**
```
Let me drill into marketing expenses.

Marketing Variance Detail:
Budget: $260K
Actual: $325K
Variance: $65K (25% over)

Breakdown by subcategory:
- Digital Ads: $180K vs $150K (+$30K)
  → Google Ads campaign expanded
- Events: $75K vs $60K (+$15K)
  → Added trade show booth
- Content: $45K vs $40K (+$5K)
  → Video production
- Agencies: $25K vs $10K (+$15K)
  → New creative agency retainer

Primary driver: Digital ads campaign expansion (+$30K)

Was this spend planned but not budgeted, or truly incremental?
Would you like me to analyze marketing ROI?
```

### Request: "Compare last 3 months"

**Response:**
```
I'll create a 3-month trend analysis.

Revenue Trend (Budget vs Actual):
| Month | Budget | Actual | Variance | Var% | Trend |
|-------|--------|--------|----------|------|-------|
| Jan   | $1,000K| $970K  | $(30K)   | -3%  | ⬇️    |
| Feb   | $1,000K| $950K  | $(50K)   | -5%  | ⬇️    |
| Mar   | $1,000K| $930K  | $(70K)   | -7%  | ⬇️    |
| Q1    | $3,000K| $2,850K| $(150K)  | -5%  | ⬇️    |

⚠️ ALERT: Revenue variance is worsening month-over-month

This suggests a structural issue, not timing:
- Jan: 97% of budget
- Feb: 95% of budget
- Mar: 93% of budget

Recommendation: Immediate deep-dive on sales execution
```

## Formatting Rules

The Skill applies professional formatting:

### Conditional Formatting
```
- Green cells: Favorable variances (>5% better than budget)
- Yellow cells: Variances within ±5%
- Red cells: Unfavorable variances (>5% worse than budget)
```

### Number Formatting
```
- Currency: $1,000K or $1.0M (use K for thousands, M for millions)
- Percentages: 1 decimal place (5.0%)
- Variance: Show sign ($(50K) or $50K)
```

### Icons
```
✅ = On track / Favorable
⚠️ = Warning / Needs attention
🔴 = Critical / Unfavorable
⬆️ = Improving trend
⬇️ = Worsening trend
➡️ = Flat trend
```

## Best Practices Embedded

1. **Materiality Thresholds**: Don't flag every small variance
2. **Commentary Not Just Numbers**: Explain "why", not just "what"
3. **Action-Oriented**: Recommend next steps
4. **Executive Summary**: Leadership wants top 5-10 items
5. **Trend Analysis**: Show if variance is new or ongoing
6. **Sign Conventions**: Consistent favorable/unfavorable labeling
7. **Audit Trail**: Show calculations and formulas

## Resources

See resources folder for:
- `REFERENCE.md`: Variance analysis best practices
- `templates/`: Sample variance reports

## Limitations

This Skill provides automated variance analysis for:
- Standard income statement formats
- Monthly/quarterly reporting
- Budget vs actual comparisons

For more complex analysis, you may need:
- Statistical variance analysis (standard deviations)
- Multi-year trend analysis
- Driver-based variance decomposition
- Forecast vs forecast comparisons

## Version History

- v1.0.0 (2025-10-27): Initial release with core variance analysis functionality
