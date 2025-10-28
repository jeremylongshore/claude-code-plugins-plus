# Build LBO Model

Build a leveraged buyout (LBO) model in Excel with sources & uses, debt schedules, cash flow waterfalls, and IRR calculations.

## What This Command Does

Creates a complete 6-sheet LBO model:
1. **Transaction Summary** - Deal terms and returns overview
2. **Sources & Uses** - How the deal is financed
3. **Operating Model** - 5-year revenue and EBITDA projections
4. **Debt Schedule** - Debt paydown waterfall for all tranches
5. **Returns Analysis** - Exit valuation, IRR, money-on-money
6. **Debt Covenants** - Leverage and coverage covenants

## Instructions for Claude

When the user types `/build-lbo`, follow these steps:

### 1. Gather Transaction Inputs

Ask for:
- Target company name
- Current year EBITDA
- Entry valuation multiple (EV/EBITDA)
- Revenue growth rates (Years 1-5)
- EBITDA margin assumptions
- Exit multiple assumption
- Hold period (default: 5 years)

### 2. Structure Financing

Build typical LBO capital structure:
- Revolver: 1-2x EBITDA (undrawn at close)
- Term Loan A: 2-2.5x EBITDA
- Term Loan B: 2-3x EBITDA
- Subordinated/Mezz: 1-2x if needed
- Total Debt: 5-6x EBITDA
- Equity: Remainder (30-40% of price)

### 3. Build Complete Model

Use Excel MCP server to:
1. Calculate sources & uses
2. Build operating projections
3. Create debt schedules with amortization
4. Calculate cash flow waterfall
5. Determine exit value and returns
6. Add sensitivity tables

### 4. Return Results

Provide:
- Entry and exit enterprise values
- Equity check size
- Debt paydown over hold period
- IRR and money-on-money multiple
- Key sensitivities

## Example Usage

```
User: /build-lbo

Claude: I'll build an LBO model. What's the target company?

User: Software company with $50M EBITDA

Claude: What entry multiple (EV/EBITDA)?

User: 12x

Claude: [Builds complete LBO model]

✅ LBO Model Complete!
IRR: 34.2%
Money-on-Money: 4.2x
📁 Saved to: Software_LBO_Model.xlsx
```

## Notes

- This command manually triggers the excel-lbo-modeler Skill
- Users can also just say "Create an LBO model" for auto-invocation
- Use this command for explicit control over Skill loading
