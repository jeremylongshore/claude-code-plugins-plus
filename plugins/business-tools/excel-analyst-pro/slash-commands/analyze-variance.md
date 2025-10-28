# Analyze Variance

Automate budget vs actual variance analysis with flagging, commentary, and executive summaries.

## What This Command Does

Creates a comprehensive variance report with:
1. **Variance Summary** - Line-by-line budget vs actual with flags
2. **Executive Summary** - Top variances and key insights
3. **Trend Analysis** - Multi-period variance trends (if applicable)

## Instructions for Claude

When the user types `/analyze-variance`, follow these steps:

### 1. Load Data

Ask for:
- Budget data (Excel file, CSV, or pasted table)
- Actual data (same format as budget)
- Period (month, quarter, YTD)
- Threshold settings (default: ±10% or ±$50K)

### 2. Calculate Variances

For each line item:
- Absolute Variance = Actual - Budget
- Percentage Variance = (Actual - Budget) / Budget × 100%
- Apply sign conventions (revenue unfavorable if below, expenses unfavorable if above)

### 3. Flag Material Items

Apply flagging:
- 🔴 Red: Critical variances (>10% unfavorable or >$100K)
- ⚠️ Yellow: Warning variances (5-10% unfavorable or $50K-$100K)
- ✅ Green: On track (within ±5% or <$50K)

### 4. Generate Commentary

For each flagged item:
- Explain what's driving the variance
- Provide context (is this timing or structural?)
- Recommend actions

### 5. Create Executive Summary

Summarize:
- Bottom-line performance vs budget
- Top 5 unfavorable variances
- Top 5 favorable variances
- Key takeaways and action items

## Example Usage

```
User: /analyze-variance

Claude: I'll analyze variance. Do you have budget and actual files?

User: *pastes data*

Claude: [Analyzes data]

✅ Variance Analysis Complete!

🔴 CRITICAL VARIANCES:
- EBITDA: $270K vs $450K (-40.0%)
- Operating Expenses: $840K vs $750K (+12.0%)

📁 Saved to: Q1_2025_Variance_Analysis.xlsx
```

## Notes

- This command manually triggers the excel-variance-analyzer Skill
- Users can also just say "Analyze budget variance" for auto-invocation
- Use this command for explicit control over when the Skill loads
