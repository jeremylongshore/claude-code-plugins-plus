---
name: excel-pivot-wizard
description: Generate pivot tables and charts from raw data using natural language - analyze sales by region, summarize data by category, and create visualizations effortlessly
version: 1.0.0
dependencies: node>=18.0.0
---

# Excel Pivot Wizard

Creates pivot tables and visualizations from raw data using natural language commands.

## When to Invoke This Skill

Automatically load this Skill when the user asks to:
- "Create a pivot table"
- "Analyze [data] by [dimension]"
- "Summarize sales by region"
- "Show revenue breakdown"
- "Group data by category"
- "Cross-tab analysis"
- "Compare [X] across [Y]"

## Capabilities

### Pivot Table Generation
- **Rows**: Group data by one or more fields
- **Columns**: Cross-tabulate across another dimension
- **Values**: Aggregate functions (sum, average, count, min, max)
- **Filters**: Slice data by specific criteria
- **Calculated Fields**: Create custom formulas

### Visualization
- Column/bar charts for comparisons
- Line charts for trends over time
- Pie charts for composition
- Combo charts for multiple metrics
- Conditional formatting for heatmaps

## Common Analysis Patterns

### Pattern 1: Single Dimension Summary
**Request:** "Show total sales by region"

**Output:**
```
| Region    | Total Sales |
|-----------|-------------|
| Northeast | $1,250,000  |
| Southeast | $980,000    |
| Midwest   | $1,100,000  |
| West      | $1,450,000  |
| Total     | $4,780,000  |
```

### Pattern 2: Cross-Tabulation
**Request:** "Sales by region and product category"

**Output:**
```
| Region    | Electronics | Clothing | Home Goods | Total     |
|-----------|-------------|----------|------------|-----------|
| Northeast | $400K       | $500K    | $350K      | $1,250K   |
| Southeast | $300K       | $380K    | $300K      | $980K     |
| Midwest   | $450K       | $350K    | $300K      | $1,100K   |
| West      | $550K       | $500K    | $400K      | $1,450K   |
| Total     | $1,700K     | $1,730K  | $1,350K    | $4,780K   |
```

### Pattern 3: Time-Based Trending
**Request:** "Monthly revenue trend for 2024"

**Output:**
```
Line chart showing:
- X-axis: Jan, Feb, Mar, ..., Dec
- Y-axis: Revenue
- Line: Monthly revenue with data labels
```

### Pattern 4: Top N Analysis
**Request:** "Top 10 products by revenue"

**Output:**
```
| Rank | Product       | Revenue   | % of Total |
|------|---------------|-----------|------------|
| 1    | Product A     | $450,000  | 9.4%       |
| 2    | Product B     | $380,000  | 7.9%       |
| 3    | Product C     | $350,000  | 7.3%       |
| ...  | ...           | ...       | ...        |
| 10   | Product J     | $180,000  | 3.8%       |
|      | Top 10 Total  | $2,850,000| 59.6%      |
|      | All Others    | $1,930,000| 40.4%      |
|      | Grand Total   | $4,780,000| 100.0%     |
```

## Step-by-Step Workflow

### 1. Understand the Data

Ask clarifying questions if needed:
- What does each column represent?
- What grain is the data? (transaction-level, daily summary, etc.)
- What fields should be aggregated vs grouped?

### 2. Interpret the Request

Parse natural language into pivot table structure:

**"Show sales by region and month"** →
```
Rows: Region
Columns: Month
Values: Sum of Sales
```

**"Average order value by customer segment"** →
```
Rows: Customer Segment
Values: Average of Order Value
```

**"Count of orders by product category and sales rep"** →
```
Rows: Product Category
Columns: Sales Rep
Values: Count of Orders
```

### 3. Build the Pivot Table

Use Excel MCP server to:
1. Create pivot table on new sheet
2. Set row fields
3. Set column fields (if cross-tab)
4. Set value fields with aggregation function
5. Add filters/slicers if requested
6. Apply formatting (currency, thousands separator, etc.)

### 4. Add Enhancements

**Conditional Formatting:**
```
- Top 10% values: Dark green
- Bottom 10% values: Dark red
- Color scale for heatmap effect
```

**Calculated Fields:**
```
- Profit Margin % = (Revenue - Cost) / Revenue
- Growth % = (This Year - Last Year) / Last Year
- % of Total = Value / Grand Total
```

**Sorting:**
```
- Largest to smallest by default
- Or chronological for dates
```

### 5. Create Visualization

If visualization is requested or would be helpful:

**For Comparisons:** Column chart
**For Trends:** Line chart
**For Composition:** Pie/donut chart
**For Correlations:** Scatter plot
**For Multiple Metrics:** Combo chart (column + line)

## Example Interactions

### Example 1: Sales Analysis

**User:** "Analyze sales by region and product category"

**Skill Response:**
```
I'll create a pivot table to analyze sales by region and product category.

Looking at your data, I see:
- 5,234 transaction rows
- Date range: Jan 1 - Oct 27, 2025
- 4 regions, 12 product categories

Creating pivot table...

✅ Pivot Table Created!

📊 Sales by Region and Product Category:

Top Insights:
1. West region leads with $1.45M (30.3% of total)
2. Electronics is #1 category at $1.70M (35.6%)
3. Northeast + Electronics = $400K (highest cell)
4. Southeast underperforming in Home Goods ($300K vs avg $338K)

Visualization: Added column chart comparing regions

Would you like me to:
- Add a slicer to filter by quarter?
- Calculate % of total for each cell?
- Create a separate view for top products?
```

### Example 2: Time Trend

**User:** "Show monthly revenue trend"

**Skill Response:**
```
Creating monthly revenue trend analysis...

I see data spanning 10 months (Jan-Oct 2025).

✅ Trend Analysis Complete!

📈 Monthly Revenue:

Key Findings:
- Strong start: Q1 averaged $520K/month
- Dip in summer: Jun-Aug averaged $420K/month
- Recovery: Sep-Oct back to $510K/month
- YTD Total: $4.78M
- Average: $478K/month

Created line chart with:
- Trend line showing slight upward trajectory
- Data labels for easy reading
- Target line at $500K (if provided)

📊 Growth Rates:
- Jan-Oct: +8.3% overall
- Best month: March ($575K)
- Weakest month: August ($385K)

Recommendation: Investigate summer seasonality (Jun-Aug dip)
```

### Example 3: Customer Segmentation

**User:** "Show average order value by customer segment"

**Skill Response:**
```
Analyzing average order value (AOV) across customer segments...

✅ Customer Segmentation Analysis Complete!

| Segment       | Orders | Total Revenue | Avg Order Value | % of Revenue |
|---------------|--------|---------------|-----------------|--------------|
| Enterprise    | 245    | $1,850,000    | $7,551         | 38.7%        |
| Mid-Market    | 892    | $1,920,000    | $2,152         | 40.2%        |
| Small Business| 2,456  | $835,000      | $340           | 17.5%        |
| Consumer      | 1,641  | $175,000      | $107           | 3.7%         |
| Total         | 5,234  | $4,780,000    | $913           | 100.0%       |

🎯 Key Insights:
- Enterprise: Highest AOV ($7.5K) but only 4.7% of orders
- Mid-Market: Sweet spot (40% of revenue, $2.2K AOV)
- Small Business: High volume (47% of orders) but low AOV
- Consumer: Explore if worth serving (low AOV, high volume)

Created bar chart showing AOV by segment with order count overlay.

💡 Strategic Questions:
1. Should we focus more resources on Enterprise (high AOV)?
2. Can we up-sell Small Business to Mid-Market?
3. Is Consumer segment profitable at $107 AOV?
```

### Example 4: Product Performance

**User:** "Which products are driving the most revenue?"

**Skill Response:**
```
Creating product revenue ranking...

✅ Top Products Analysis Complete!

📊 Top 10 Products (out of 147 total):

| Rank | Product          | Revenue   | Orders | AOV    | % of Total |
|------|------------------|-----------|--------|--------|------------|
| 1    | Pro Laptop 15"   | $450,000  | 385    | $1,169 | 9.4%       |
| 2    | Business Suite   | $380,000  | 892    | $426   | 7.9%       |
| 3    | Smart Display    | $350,000  | 1,245  | $281   | 7.3%       |
| 4    | Wireless Buds    | $310,000  | 2,156  | $144   | 6.5%       |
| 5    | Office Chair Pro | $295,000  | 428    | $689   | 6.2%       |
| 6    | Standing Desk    | $280,000  | 356    | $787   | 5.9%       |
| 7    | Monitor 27"      | $265,000  | 487    | $544   | 5.5%       |
| 8    | Keyboard Mech    | $245,000  | 1,823  | $134   | 5.1%       |
| 9    | Webcam 4K        | $220,000  | 678    | $324   | 4.6%       |
| 10   | Mouse Wireless   | $195,000  | 2,145  | $91    | 4.1%       |
|      | **Top 10 Total** | **$2,990,000** | | | **62.5%** |
|      | All Others (137) | $1,790,000 |    |        | 37.5%       |
|      | **Grand Total**  | **$4,780,000** | | | **100.0%** |

🎯 Insights:
- Top 10 products = 62.5% of revenue (strong concentration)
- Pro Laptop alone = 9.4% of total revenue
- High-volume low-AOV products: Wireless Buds, Keyboard, Mouse
- High-AOV low-volume products: Pro Laptop, Standing Desk

Created:
- Bar chart: Top 10 products by revenue
- Pareto chart: Cumulative % of revenue

💡 Strategic Implications:
1. Focus inventory on Top 20 products (likely 80% of revenue)
2. Bundle high-volume + high-margin items
3. Wireless Buds: Explore upsell to Pro Buds (higher margin?)
```

## Advanced Features

### Calculated Fields

**Request:** "Show profit margin by product category"

**Response:**
```
I'll add a calculated field for profit margin.

Assuming you have Cost and Revenue columns, I'll calculate:
Profit Margin % = (Revenue - Cost) / Revenue × 100%

| Category    | Revenue | Cost    | Profit  | Margin % |
|-------------|---------|---------|---------|----------|
| Electronics | $1,700K | $1,020K | $680K   | 40.0%    |
| Clothing    | $1,730K | $1,125K | $605K   | 35.0%    |
| Home Goods  | $1,350K | $945K   | $405K   | 30.0%    |
| Total       | $4,780K | $3,090K | $1,690K | 35.4%    |

Electronics has the highest margin (40%) despite not being the highest revenue category.
```

### Slicers & Filters

**Request:** "Add filters for date range and region"

**Response:**
```
I've added slicers for:
1. Date Range (select quarters or specific months)
2. Region (select one or multiple regions)
3. Product Category (filter to specific categories)

These slicers are linked to the pivot table - any selection will update the data automatically.

Try clicking Q3 in the date slicer to see summer performance!
```

### Multiple Aggregations

**Request:** "Show sum and average of sales by region"

**Response:**
```
| Region    | Total Sales | Avg Sale | Order Count |
|-----------|-------------|----------|-------------|
| Northeast | $1,250,000  | $625     | 2,000       |
| Southeast | $980,000    | $490     | 2,000       |
| Midwest   | $1,100,000  | $524     | 2,100       |
| West      | $1,450,000  | $690     | 2,100       |

Interesting: Southeast has lowest average sale despite same order count as Northeast.
This suggests smaller basket sizes in Southeast - worth investigating!
```

## Formatting Best Practices

The Skill applies professional formatting:

### Numbers
```
Revenue: $1,250,000 or $1.25M (use M for millions)
Counts: 2,000 (thousands separator)
Percentages: 35.0% (1 decimal)
```

### Conditional Formatting
```
Top performers: Green highlight
Bottom performers: Red highlight
Heatmap: Color gradient from red (low) to green (high)
```

### Layout
```
- Bold headers
- Freeze top row and left column
- Subtotals and grand totals
- Alternating row colors for readability
```

## Resources

See resources folder for:
- `REFERENCE.md`: Pivot table best practices
- `examples/`: Sample pivot tables for common analyses

## Limitations

This Skill creates standard pivot tables for:
- Summarization and aggregation
- Cross-tabulation
- Basic calculations (sum, average, count)

For advanced analysis, you may need:
- Power Pivot (for complex data models)
- Pivot charts with custom formatting
- Integration with external data sources
- Real-time data refresh

## Version History

- v1.0.0 (2025-10-27): Initial release with core pivot table generation
