---
name: report
description: Generate comprehensive terminal report of AI experiments
shortcut: aire
---
# AI Experiments Report

When the user runs `/ai-report`, generate a comprehensive, well-formatted terminal report of their AI experiments.

## Report Sections

### 1. Summary Statistics

Display at the top:

```
╔══════════════════════════════════════════════════════════════╗
║           AI EXPERIMENT LOGGER - SUMMARY REPORT              ║
╚══════════════════════════════════════════════════════════════╝

📊 OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Experiments: [count]
Average Rating: [X.XX] ⭐
Date Range: [earliest] → [latest]
```

### 2. Top Performing AI Tools

Show the top 5 AI tools by average rating:

```
🏆 TOP AI TOOLS BY PERFORMANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ChatGPT o1-preview    ⭐ 4.85 avg  (20 experiments)
2. Claude Sonnet 3.5     ⭐ 4.75 avg  (18 experiments)
3. Gemini Pro           ⭐ 4.20 avg  (12 experiments)
```

### 3. Rating Distribution

Show distribution visually:

```
⭐ RATING DISTRIBUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5 stars ████████████████████████████ (28)
4 stars ████████████████████ (20)
3 stars ██████████ (10)
2 stars ████ (4)
1 star  ██ (2)
```

### 4. Most Used Tags

Show top 10 tags:

```
🏷️  POPULAR TAGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
code-generation (15)    debugging (12)         research (10)
creative-writing (8)    data-analysis (7)      testing (6)
```

### 5. Recent Activity

Show last 7 days:

```
📈 RECENT ACTIVITY (Last 7 Days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2025-10-13: ████████ (8 experiments)
2025-10-12: ██████ (6 experiments)
2025-10-11: ████ (4 experiments)
```

### 6. Latest Experiments

Show the 5 most recent:

```
📝 LATEST EXPERIMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Oct 13, 2:30 PM] ChatGPT o1-preview ⭐⭐⭐⭐⭐
  Prompt: Write a Python function to calculate Fibonacci
  Tags: code-generation, python

[Oct 13, 1:15 PM] Claude Sonnet 3.5 ⭐⭐⭐⭐
  Prompt: Debug React useState issue with async
  Tags: debugging, react, javascript
```

## Data Sources

Use the `get_statistics` and `list_experiments` MCP tools to gather all data.

## Optional Filters

Support these filters via arguments:

- `/ai-report tool:ChatGPT` - Show report for specific tool
- `/ai-report tag:code-generation` - Show report for specific tag
- `/ai-report days:30` - Show last 30 days only
- `/ai-report rating:5` - Show only 5-star experiments

## Error Handling

If no experiments exist:

```
╔══════════════════════════════════════════════════════════════╗
║           AI EXPERIMENT LOGGER - SUMMARY REPORT              ║
╚══════════════════════════════════════════════════════════════╝

📊 NO EXPERIMENTS YET

Get started by logging your first AI experiment:
  /log-exp

Or use the MCP tool directly:
  Use the log_experiment tool
```

## Implementation Notes

- Use Unicode box drawing characters for clean terminal output
- Ensure all sections are properly aligned
- Use emoji for visual appeal but keep it professional
- Calculate percentages and averages with 2 decimal precision
- Sort all rankings by count/rating descending
- Format dates in user-friendly format (Oct 13, 2:30 PM)
