---
name: excel-dcf-modeler
description: |
  Build discounted cash flow (DCF) valuation models in Excel with free cash flow projections, WACC calculations, and sensitivity analysis for investment banking and corporate finance teams Activates when you request "excel dcf modeler" functionality.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

# Excel DCF Modeler

Creates professional DCF valuation models following investment banking standards and best practices.

## When to Invoke This Skill

Automatically load this Skill when the user asks to:
- "Create a DCF model"
- "Build a valuation model"
- "Calculate enterprise value"
- "Value [company name]"
- "DCF for [company]"
- "Discounted cash flow analysis"
- "What's the intrinsic value"

## Model Structure

This Skill creates a complete 4-sheet Excel DCF model:

### Sheet 1: Assumptions
- **Company Information**: Name, ticker, base year, fiscal year end
- **Revenue Growth Rates**: Year 1-5 projections (%)
- **Profitability Metrics**: EBITDA margin, D&A as % of revenue
- **Working Capital**: NWC as % of revenue
- **Capital Expenditures**: CapEx as % of revenue
- **Tax Rate**: Corporate tax rate (%)
- **Terminal Growth**: Long-term growth rate (typically 2-3%)
- **Discount Rate (WACC)**: Weighted average cost of capital

### Sheet 2: Free Cash Flow Projections
```
Revenue (Year 0 - Year 5)
  Less: Operating Expenses
= EBITDA
  Less: Depreciation & Amortization
= EBIT
  Less: Taxes (EBIT × Tax Rate)
= NOPAT (Net Operating Profit After Tax)
  Add: Depreciation & Amortization
  Less: Capital Expenditures
  Less: Change in Net Working Capital
= Unlevered Free Cash Flow
```

### Sheet 3: Valuation
```
Present Value of FCF (Years 1-5)
  Year 1 FCF / (1 + WACC)^1
  Year 2 FCF / (1 + WACC)^2
  ...
  Year 5 FCF / (1 + WACC)^5
= Sum of PV(FCF)

Terminal Value Calculation
  Terminal FCF = Year 5 FCF × (1 + Terminal Growth Rate)
  Terminal Value = Terminal FCF / (WACC - Terminal Growth Rate)
  PV of Terminal Value = Terminal Value / (1 + WACC)^5

Enterprise Value
  = Sum of PV(FCF) + PV(Terminal Value)

Equity Value
  = Enterprise Value
  - Net Debt
  + Non-Operating Assets

Equity Value per Share
  = Equity Value / Shares Outstanding
```

### Sheet 4: Sensitivity Analysis
Two-way sensitivity table showing Enterprise Value sensitivity to:
- **Rows**: WACC (ranging from -2% to +2% of base case)
- **Columns**: Terminal Growth Rate (ranging from 1.5% to 3.5%)
- **Output**: Enterprise Value at each combination

## Step-by-Step Workflow

### 1. Gather Inputs
Ask the user for the following information (provide defaults based on industry averages if user is uncertain):

**Required Inputs:**
- Company name and ticker symbol
- Base year revenue (most recent fiscal year)
- Revenue growth rates for Years 1-5 (e.g., 15%, 12%, 10%, 8%, 6%)
- EBITDA margin % (e.g., 20%)
- Tax rate % (e.g., 21% for US corporations)

**Optional Inputs (use defaults if not provided):**
- D&A as % of revenue (default: 5%)
- CapEx as % of revenue (default: 4%)
- NWC as % of revenue (default: 10%)
- Terminal growth rate (default: 2.5%)
- WACC/discount rate (default: 10%)
- Net debt amount (default: $0)
- Shares outstanding (if calculating per-share value)

### 2. Validate Inputs
Ensure the following before building the model:
- Revenue growth rates are reasonable (typically 0-30%)
- EBITDA margin is positive
- Tax rate is between 0-40%
- Terminal growth < WACC (model won't work if g >= WACC)
- WACC is reasonable (typically 7-15%)

### 3. Build Excel Model
Use the Excel MCP server to:
1. Create new workbook
2. Create 4 sheets: "Assumptions", "FCF Projections", "Valuation", "Sensitivity"
3. Populate assumptions in Sheet 1
4. Build FCF projection formulas in Sheet 2 (link to assumptions)
5. Calculate PV of FCF and Terminal Value in Sheet 3
6. Create sensitivity table in Sheet 4
7. Apply professional formatting:
   - Currency format for monetary values
   - Percentage format for rates
   - Conditional formatting on sensitivity table (green = high value, red = low value)
   - Bold headers, freeze panes
   - Cell borders for clarity

### 4. Calculate Results
Return to the user:
- Enterprise Value (in millions/billions)
- Equity Value (if net debt provided)
- Equity Value per Share (if shares outstanding provided)
- Key assumptions used
- Link to sensitivity analysis

### 5. Provide Insights
After building the model, provide brief commentary:
- Is the implied valuation reasonable given industry comparables?
- What are the key value drivers? (usually revenue growth and margins)
- What's the sensitivity to WACC? (typically highest sensitivity)
- Recommend focus areas for further analysis

## Example Formulas

### Free Cash Flow Calculation
```excel
// Revenue (Year 1)
=Assumptions!B5 * (1 + Assumptions!B10)

// EBITDA
=Revenue * Assumptions!B15

// EBIT
=EBITDA - (Revenue * Assumptions!B16)

// NOPAT
=EBIT * (1 - Assumptions!B18)

// Free Cash Flow
=NOPAT + (Revenue * Assumptions!B16) - (Revenue * Assumptions!B17) - ΔNWCapital
```

### Present Value
```excel
// PV of Year 1 FCF
=FCF_Year1 / (1 + WACC)^1

// Terminal Value
=(FCF_Year5 * (1 + Terminal_Growth)) / (WACC - Terminal_Growth)

// PV of Terminal Value
=Terminal_Value / (1 + WACC)^5
```

### Sensitivity Table
```excel
// Use Excel's data table feature
// Row input: Terminal Growth Rate
// Column input: WACC
// Formula: =Enterprise_Value
```

## Example Interaction

**User:** "Create a DCF model for Tesla"

**Skill Response:**
```
I'll build a DCF valuation model for Tesla. Let me gather some inputs.

What base year revenue should we use for Tesla?
(For reference, Tesla's 2023 revenue was approximately $96.8B)

User: $96.8 billion

Great! What revenue growth rates should we assume for Years 1-5?
(Recommended: Start high and taper down, e.g., 20%, 18%, 15%, 12%, 10%)

User: 25%, 20%, 15%, 12%, 10%

What EBITDA margin should we assume?
(Tesla's recent EBITDA margin has been around 15-17%)

User: 16%

Perfect! I'll use the following assumptions:
- Base year revenue: $96.8B
- Growth rates: 25%, 20%, 15%, 12%, 10%
- EBITDA margin: 16%
- Tax rate: 21% (standard US rate)
- WACC: 10% (typical for automotive/tech)
- Terminal growth: 2.5%
- D&A: 5% of revenue
- CapEx: 4% of revenue
- NWC: 10% of revenue

Building your DCF model...

✅ DCF Model Complete!

📊 Valuation Results:
- Enterprise Value: $847.3 billion
- Terminal Value represents: 68% of EV
- Implied equity value per share: $243 (assuming 3.48B shares)

🎯 Key Insights:
- High growth assumptions drive significant value creation
- Model is sensitive to WACC (see sensitivity table)
- Terminal value is major component - validate terminal assumptions
- Revenue growth is the primary value driver

📁 Model saved to: Tesla_DCF_Model.xlsx

The sensitivity table shows Enterprise Value ranges from $612B (high WACC, low growth) to $1,124B (low WACC, high growth).

Would you like me to adjust any assumptions or add additional analysis?
```

## Common Variations

### Request: "Build a DCF but I don't have all the numbers"

**Response:**
```
No problem! I can build a DCF model with industry-average assumptions, and you can adjust later.

What company are you valuing?

User: Amazon

What's the approximate current revenue? (or I can look up recent financials)

I'll use industry-standard assumptions for a large-cap tech company:
- Revenue growth: 15%, 12%, 10%, 8%, 6% (tapering)
- EBITDA margin: 25% (tech average)
- WACC: 9%
- Terminal growth: 2.5%

I'll build the model with these defaults, and you can easily adjust the assumptions in the "Assumptions" sheet.
```

### Request: "Explain the DCF model you built"

**Response:**
```
Sure! Let me walk through the DCF model:

📊 What is a DCF?
A DCF values a company based on its future cash flows, discounted to present value.

🔢 The Model:
1. Projects free cash flow for 5 years
2. Calculates a "terminal value" for years beyond Year 5
3. Discounts all cash flows to today using WACC
4. Sums everything to get Enterprise Value

💰 Key Components:
- Free Cash Flow = Cash the company generates after all investments
- WACC = Cost of capital (what investors expect to earn)
- Terminal Value = Value of cash flows beyond Year 5 (usually 60-80% of total)

⚠️ Important Notes:
- This is a simplified DCF (doesn't include debt schedules, detailed NWC)
- Garbage in, garbage out: Assumptions drive everything
- Use this as a starting point, not final answer
- Always compare to comparable company analysis (comps)

Would you like me to explain any specific part in more detail?
```

## Error Handling

### Invalid Inputs
If user provides invalid inputs:
```
⚠️ Issue detected: Terminal growth rate (4%) is >= WACC (3.5%)

This will cause a mathematical error in the terminal value calculation.
The terminal growth rate must be less than WACC.

Typical ranges:
- WACC: 7-15%
- Terminal growth: 2-3%

Would you like me to adjust these values?
```

### Missing Information
If critical information is missing:
```
I need at least the following to build a DCF:
- Company name or industry
- Approximate current revenue (or I can use industry average)

All other assumptions can use industry defaults.

Would you like me to proceed with defaults, or would you prefer to provide specific assumptions?
```

## Best Practices Embedded

This Skill follows investment banking best practices:

1. **Conservative Terminal Growth**: Default to 2.5% (GDP growth rate)
2. **Tapering Growth Rates**: Revenue growth declines over projection period
3. **Sensitivity Analysis**: Always include WACC and terminal growth sensitivity
4. **Clear Labeling**: All assumptions clearly labeled and linked
5. **Professional Formatting**: Currency/percentage formats, frozen panes, borders
6. **Audit Trail**: Formulas link back to assumptions (no hard-coded values)
7. **Reasonableness Checks**: Validate inputs before building model

## Resources

See the resources folder for:
- `dcf-template.xlsx`: Pre-built DCF template
- `REFERENCE.md`: Financial modeling best practices
- `formulas.txt`: Common DCF formulas for reference

## Limitations

This Skill creates a simplified DCF model suitable for:
- Initial valuation analysis
- Pitch decks and presentations
- Academic exercises
- Quick "back of envelope" valuations

For detailed investment committee presentations or official fairness opinions, you should:
- Add detailed debt schedules
- Include multiple scenarios (base, bull, bear)
- Add more granular operating assumptions
- Validate with third-party data
- Have a finance professional review

## Version History

- v1.0.0 (2025-10-27): Initial release with core DCF functionality
