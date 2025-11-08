# Build DCF Model

Build a discounted cash flow (DCF) valuation model in Excel with professional formatting and investment banking-grade structure.

## What This Command Does

Creates a complete 4-sheet DCF model:
1. **Assumptions** - Revenue growth, margins, WACC, terminal growth
2. **FCF Projections** - 5-year free cash flow forecast
3. **Valuation** - Present value calculations and enterprise value
4. **Sensitivity** - Two-way sensitivity table (WACC vs terminal growth)

## Instructions for Claude

When the user types `/build-dcf`, follow these steps:

### 1. Gather Inputs

Ask the user for:
- Company name and ticker
- Base year revenue (most recent fiscal year)
- Revenue growth rates for Years 1-5
- EBITDA margin %
- Tax rate %
- Optional: WACC, terminal growth, D&A %, CapEx %, NWC %

### 2. Validate Inputs

Ensure:
- Revenue growth rates are reasonable (0-30%)
- EBITDA margin is positive
- Tax rate is 0-40%
- Terminal growth < WACC

### 3. Build Model

Use Excel MCP server to:
1. Create new workbook
2. Create 4 sheets
3. Populate assumptions
4. Build FCF projection formulas (link to assumptions)
5. Calculate PV of FCF and terminal value
6. Create sensitivity table
7. Apply professional formatting

### 4. Return Results

Provide:
- Enterprise value
- Equity value (if net debt provided)
- Key assumptions used
- Link to sensitivity analysis

## Example Usage

```
User: /build-dcf

Claude: I'll build a DCF model. What company would you like to value?

User: Apple

Claude: What base year revenue should we use?

User: $383 billion (2023)

Claude: What revenue growth rates for Years 1-5?

User: 8%, 7%, 6%, 5%, 4%

Claude: [Builds complete DCF model]

✅ DCF Model Complete!
Enterprise Value: $3.24 trillion
📁 Saved to: Apple_DCF_Model.xlsx
```

## Notes

- This command manually triggers the excel-dcf-modeler Skill
- Users can also just say "Create a DCF model" for auto-invocation
- Use this command when you want explicit control over when the Skill loads
