# Data Visualization Design

Practical guide to designing charts, tables, and data displays that communicate clearly.

## Chart Selection

### Choosing the Right Chart Type

| Data Type | Best Chart | Avoid |
|-----------|-----------|-------|
| Part-to-whole | Pie (≤5 slices), stacked bar | Pie with many slices |
| Change over time | Line chart, area chart | Pie chart |
| Comparison (few items) | Bar chart (horizontal or vertical) | Line chart |
| Comparison (many items) | Horizontal bar chart | Vertical bars (labels hard) |
| Distribution | Histogram, box plot | Pie chart |
| Correlation | Scatter plot | Line chart |
| Composition over time | Stacked area, stacked bar | Multiple pie charts |

### When NOT to Use a Chart

Sometimes a simple number is better:
- Single data point → Big number display
- Two numbers to compare → Side-by-side with % change
- Very few data points → Table might be clearer

```
❌ Pie chart with 2 slices (73% vs 27%)
✅ "73% of users completed onboarding"
```

---

## Bar Charts

### Orientation

**Vertical bars:** Best when comparing few categories with short labels
**Horizontal bars:** Best when comparing many categories or labels are long

### Bar Chart Rules

1. **Always start at zero** - Truncated axes mislead
2. **Order meaningfully** - By value (descending) or logical order (time, alphabet)
3. **Space bars correctly** - Gap between bars = 50-100% of bar width
4. **Label directly** - Put values on bars, not in legend
5. **Limit categories** - 5-7 bars maximum; group others as "Other"

### Bar Styling

```css
/* Bar appearance */
.bar {
  fill: var(--primary);
  border-radius: 2px 2px 0 0; /* Slight rounding on top only */
}

/* Hover state */
.bar:hover {
  fill: var(--primary-dark);
}

/* Spacing */
.bar-gap: 8px;
.bar-width: 32px;
```

---

## Line Charts

### When to Use

- Continuous data over time
- Trends matter more than individual values
- Comparing multiple series over same time period

### Line Chart Rules

1. **Start Y-axis at zero** (usually) - Unless all values are in narrow range
2. **Limit to 4-5 lines** - More becomes unreadable
3. **Use distinct line styles** - Different colors, consider dashes for printing
4. **Label lines directly** - Not just in legend
5. **Highlight important points** - Mark significant events or thresholds

### Line Styling

```css
/* Line appearance */
.line {
  stroke-width: 2px;
  fill: none;
}

/* Data points */
.data-point {
  r: 4px;
  fill: white;
  stroke-width: 2px;
}

/* Only show points on hover or for few data points */
.data-point { opacity: 0; }
.line-group:hover .data-point { opacity: 1; }
```

---

## Pie Charts

### When to Use (Rarely)

- Showing parts of a whole
- 2-5 slices maximum
- Exact values less important than proportions
- Users understand percentages must sum to 100%

### When NOT to Use

- Comparing values (use bar chart)
- More than 5 categories
- Values that don't sum to 100%
- Showing change over time

### Pie Chart Rules

1. **Limit slices** - Maximum 5; combine small values into "Other"
2. **Order by size** - Largest slice starting at 12 o'clock
3. **Label directly** - Put labels on or near slices, not in legend
4. **Show percentages** - Values help interpretation
5. **Consider donut** - Center can show total or key metric

### Alternative: Simple Numbers

Often clearer than a pie chart:
```
┌─────────────────────────────────┐
│ 67% Mobile   23% Desktop   10% Tablet │
└─────────────────────────────────┘
```

---

## Color in Data Visualization

### Categorical Colors

For different categories, use distinct hues:

```
Blue:    #3b82f6
Orange:  #f97316
Green:   #22c55e
Purple:  #8b5cf6
Yellow:  #eab308
```

**Rules:**
- Maximum 5-7 distinct colors
- Avoid red/green together (colorblindness)
- Test with colorblind simulator

### Sequential Colors

For continuous data (low to high), use single hue with varying lightness:

```
Light:   #dbeafe (low values)
         #93c5fd
         #60a5fa
         #3b82f6
Dark:    #1d4ed8 (high values)
```

### Diverging Colors

For data with meaningful center (positive/negative, above/below average):

```
Negative:  #ef4444 (red)
Neutral:   #f3f4f6 (gray)
Positive:  #22c55e (green)
```

### Colorblind-Safe Palettes

Test your palette with:
- Coblis Color Blindness Simulator
- Chrome DevTools rendering settings

**Safe combinations:**
- Blue + Orange (deuteranopia safe)
- Blue + Yellow
- Purple + Green + Orange

---

## Tables

### When Tables Beat Charts

- Precise values matter
- Users need to look up specific data
- Multiple attributes per item
- Data will be exported/copied

### Table Design Principles

**1. Align numbers right**
```
Revenue
────────
  $1,234
 $12,456
$123,789
```

**2. Align text left**
```
Product Name
────────────
Widget A
Premium Widget
Widget Pro Max
```

**3. Use consistent precision**
```
❌  $1234, $567.89, $2.5k
✅  $1,234.00, $567.89, $2,500.00
```

**4. Minimize borders**
```css
/* Light horizontal lines only */
tr {
  border-bottom: 1px solid #e5e7eb;
}
/* No vertical borders, no heavy lines */
```

**5. Generous padding**
```css
td {
  padding: 12px 16px;
}
```

### Table Patterns

**Zebra striping:**
```css
tr:nth-child(even) {
  background-color: #f9fafb;
}
```

**Hover highlighting:**
```css
tr:hover {
  background-color: #f3f4f6;
}
```

**Sortable columns:**
```html
<th>
  Revenue
  <button aria-label="Sort by revenue">▼</button>
</th>
```

**Sticky headers:**
```css
thead th {
  position: sticky;
  top: 0;
  background: white;
}
```

---

## Dashboard Layout

### Visual Hierarchy

```
┌──────────────────────────────────────────────────────┐
│ KEY METRICS (big numbers)                             │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│ │ $45.2K  │ │  1,234  │ │  78.3%  │ │  4.2    │      │
│ │ Revenue │ │  Users  │ │  Conv.  │ │  Rating │      │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
├──────────────────────────────────────────────────────┤
│ PRIMARY CHART (most important trend)                  │
│ ┌──────────────────────────────────────────────┐     │
│ │                                              │     │
│ │         [Line chart: Revenue over time]      │     │
│ │                                              │     │
│ └──────────────────────────────────────────────┘     │
├──────────────────────────┬───────────────────────────┤
│ SUPPORTING CHARTS        │ DETAIL TABLE              │
│ ┌──────────────────┐     │ ┌───────────────────────┐ │
│ │  [Bar chart]     │     │ │ Recent Transactions   │ │
│ └──────────────────┘     │ │ ...                   │ │
│ ┌──────────────────┐     │ │ ...                   │ │
│ │  [Donut chart]   │     │ └───────────────────────┘ │
│ └──────────────────┘     │                           │
└──────────────────────────┴───────────────────────────┘
```

### Key Metric Cards

```html
<div class="metric-card">
  <span class="label">Revenue</span>
  <span class="value">$45,234</span>
  <span class="change positive">↑ 12.3%</span>
</div>
```

```css
.metric-card {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.value {
  font-size: 2rem;
  font-weight: 600;
}

.change.positive { color: #22c55e; }
.change.negative { color: #ef4444; }
```

---

## Chart Annotations

### When to Annotate

- Explain anomalies
- Mark significant events
- Highlight thresholds
- Call out key insights

### Annotation Patterns

**Event markers:**
```
                    ╭─── Product launch
Revenue ──────────/│\──────────────
                    │
```

**Threshold lines:**
```
Revenue ──────────────────────
- - - - - Target: $50k - - - -
──────────────────────────────
```

**Callout boxes:**
```
┌──────────────────────────┐
│ 📈 Best month ever!      │
│ +47% vs. last year       │
└─────────────┬────────────┘
              │
              ▼
```

---

## Accessibility in Data Viz

### Color Considerations

- Don't rely on color alone
- Add patterns, labels, or icons
- Ensure sufficient contrast
- Test with colorblind simulators

### Screen Reader Support

```html
<figure role="img" aria-label="Bar chart showing monthly revenue">
  <figcaption class="sr-only">
    Revenue by month: January $10,000, February $12,000...
  </figcaption>
  <svg>...</svg>
</figure>
```

### Data Tables as Alternative

For complex charts, provide data table version:
```html
<details>
  <summary>View data as table</summary>
  <table>...</table>
</details>
```

---

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| 3D charts | Distorts perception | Use flat 2D |
| Dual Y-axes | Confusing comparisons | Separate charts |
| Too many colors | Visual noise | Limit to 5-7 |
| Missing zero | Misleading differences | Start at zero |
| No labels | Hard to interpret | Label directly |
| Decorative elements | Chartjunk distracts | Remove non-data ink |
| Inconsistent scales | Misleading comparison | Match scales |

---

## Quick Reference

### Chart Decision Tree

```
What do you want to show?
│
├─ Comparison → Bar chart
│
├─ Change over time → Line chart
│
├─ Part of whole → Pie (≤5) or stacked bar
│
├─ Distribution → Histogram
│
├─ Relationship → Scatter plot
│
└─ Single value → Big number
```

### Minimum Viable Chart Styling

```css
/* Axes */
.axis line, .axis path {
  stroke: #e5e7eb;
}
.axis text {
  fill: #6b7280;
  font-size: 12px;
}

/* Grid */
.grid line {
  stroke: #f3f4f6;
}

/* Data */
.bar, .line, .point {
  fill: #3b82f6;
  stroke: #3b82f6;
}

/* Labels */
.label {
  fill: #374151;
  font-size: 11px;
}
```
