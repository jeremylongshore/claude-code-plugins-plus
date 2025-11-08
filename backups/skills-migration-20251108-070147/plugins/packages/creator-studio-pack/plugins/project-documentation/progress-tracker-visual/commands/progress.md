---
name: progress
description: Create visual progress updates - charts, before/after comparisons, metrics over time
---

# Progress Tracker Visual Command

Generate visual progress tracking graphics from your git history and metrics.

## Usage

```bash
/progress speed              # API response time tracking
/progress users              # User growth chart
/progress commits            # Commit frequency graph
/progress coverage           # Test coverage over time
/progress [custom-metric]    # Any custom metric
```

## Purpose

Create shareable progress visuals:
- Before/after comparisons
- Time-series charts
- Metric dashboards
- Thumbnail-ready graphics
- Social media posts

## Implementation

When user runs `/progress [metric]`:

1. **Analyze Git History**
   ```bash
   # Extract commits with metric data
   git log --all --since="30 days ago" --grep="metric" --pretty=format:"%ai|%s"
   ```

2. **Parse Metrics**
   - Look for numbers in commit messages
   - Track performance benchmarks
   - Find test coverage reports
   - Extract user counts, response times, etc.

3. **Generate Visualization**
   ```
   API RESPONSE TIME - 30 DAY TREND

   Day 1:   2000ms ████████████████████ (100%)
   Day 7:   1500ms ███████████████      (75%)
   Day 14:  800ms  ████████             (40%)
   Day 21:  200ms  ██                   (10%)

   📊 10x IMPROVEMENT
   ⬇️  90% REDUCTION
   🚀  FROM 2000ms TO 200ms
   ```

4. **Export as Image**
   - Generate PNG/SVG
   - Optimized for social media (1200x675)
   - Thumbnail-ready (1920x1080)
   - High contrast for readability

## Chart Types

### Speed/Performance
```
/progress speed

Output:
- Line graph of response times
- Before/after comparison bars
- Percentage improvement
- Key optimization milestones
```

### User Growth
```
/progress users

Output:
- Cumulative user count
- Daily/weekly/monthly growth rate
- Milestone markers (100, 1K, 10K users)
- Projected growth curve
```

### Code Quality
```
/progress coverage

Output:
- Test coverage percentage over time
- Lines covered vs total
- Coverage by module/component
- Trending direction (improving/declining)
```

### Build Activity
```
/progress commits

Output:
- Commit frequency heatmap
- Most active days/hours
- Commit types (feat/fix/refactor)
- Contribution streaks
```

## Visual Styles

### Minimal (Default)
- Clean lines
- Limited color (1-2 accent colors)
- Large text
- High contrast

### Thumbnail
- Bold text
- Bright colors
- Large numbers
- Emoji indicators

### Dashboard
- Multiple metrics
- Grid layout
- Consistent styling
- Compact information density

## Example Outputs

### API Speed Chart
```
┌─────────────────────────────────────────┐
│  API RESPONSE TIME - 3 WEEK PROGRESS   │
├─────────────────────────────────────────┤
│                                         │
│  2000ms ████████████████████            │
│         ↓                               │
│  1500ms ███████████████                 │
│         ↓                               │
│  800ms  ████████                        │
│         ↓                               │
│  200ms  ██                              │
│                                         │
│  📊 10x FASTER IN 21 DAYS              │
│  🚀 90% IMPROVEMENT                    │
│                                         │
└─────────────────────────────────────────┘

Saved to: ~/project/visuals/api-speed-progress.png
```

### User Growth
```
┌─────────────────────────────────────────┐
│      USER GROWTH - LAST 30 DAYS        │
├─────────────────────────────────────────┤
│                                     ┌─  │
│                                 ┌───┘   │
│                             ┌───┘       │
│                         ┌───┘           │
│                     ┌───┘               │
│                 ┌───┘                   │
│             ┌───┘                       │
│         ┌───┘                           │
│     ┌───┘                               │
│  ───┘                                   │
│                                         │
│  0 ─────────── 15d ─────────── 30d    │
│  47 users → 312 users (564% growth)   │
│                                         │
└─────────────────────────────────────────┘

Saved to: ~/project/visuals/user-growth.png
```

## Integration

Works with:
- **build-logger-agent**: Gets metrics from build logs
- **demo-video-generator**: Provides visuals for demos
- **thumbnail-designer**: Supplies charts for thumbnails
- **analytics-insights**: Displays performance data

Your goal: Turn progress into compelling visuals that showcase achievements and drive engagement.
