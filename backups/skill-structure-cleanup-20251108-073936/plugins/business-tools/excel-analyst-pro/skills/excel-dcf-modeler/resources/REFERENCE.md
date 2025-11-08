# DCF Modeling Best Practices

## Overview

Discounted Cash Flow (DCF) analysis is the foundation of corporate valuation. This guide outlines best practices for building professional DCF models.

## Model Structure

### 1. Assumptions Sheet

**Layout:**
```
Company Information
├── Name
├── Ticker
├── Base Year
└── Fiscal Year End

Revenue Assumptions
├── Base Year Revenue
├── Year 1-5 Growth Rates
└── Terminal Growth Rate

Profitability Assumptions
├── EBITDA Margin %
├── D&A as % of Revenue
└── Tax Rate %

Working Capital & CapEx
├── NWC as % of Revenue
└── CapEx as % of Revenue

Discount Rate
└── WACC %
```

**Best Practices:**
- Color-code assumptions (blue = inputs, black = formulas)
- Document all assumptions with sources
- Use reasonable ranges (check industry averages)
- Include sensitivity ranges for key variables

---

### 2. Free Cash Flow Projections

**Calculation Flow:**
```
Revenue
  × EBITDA Margin
= EBITDA
  - Depreciation & Amortization
= EBIT
  × (1 - Tax Rate)
= NOPAT (Net Operating Profit After Tax)
  + Depreciation & Amortization (add back non-cash)
  - Capital Expenditures
  - Increase in Net Working Capital
= Unlevered Free Cash Flow
```

**Key Formulas:**

Revenue Projection:
```excel
=Base_Revenue * (1 + Growth_Rate_Y1) * (1 + Growth_Rate_Y2) * ...
```

Or year-by-year:
```excel
Year 1: =Base_Revenue * (1 + Growth_Rate_Y1)
Year 2: =Year1_Revenue * (1 + Growth_Rate_Y2)
```

Free Cash Flow:
```excel
=NOPAT + DA - CapEx - Delta_NWC
```

**Best Practices:**
- Link all formulas to Assumptions sheet
- Never hard-code values in projection sheet
- Use consistent time periods (fiscal years, not calendar)
- Check that FCF is positive by Year 3-5

---

### 3. Valuation Calculations

**Present Value of FCF:**
```excel
PV_Year1 = FCF_Year1 / (1 + WACC)^1
PV_Year2 = FCF_Year2 / (1 + WACC)^2
...
PV_Year5 = FCF_Year5 / (1 + WACC)^5

Sum_PV_FCF = SUM(PV_Year1:PV_Year5)
```

**Terminal Value:**
```
Gordon Growth Model:
TV = FCF_Year5 * (1 + Terminal_Growth) / (WACC - Terminal_Growth)

PV_TV = TV / (1 + WACC)^5
```

**Enterprise Value:**
```
EV = Sum_PV_FCF + PV_TV
```

**Equity Value:**
```
Equity Value = EV - Net Debt + Non-Operating Assets
```

**Best Practices:**
- Terminal value typically 60-80% of EV (if >80%, revisit assumptions)
- Terminal growth rate usually 2-3% (long-term GDP growth)
- WACC typically 7-15% depending on industry and risk
- Always sanity-check: Does the implied valuation make sense vs comps?

---

### 4. Sensitivity Analysis

**Two-Way Table:**
- **Rows**: WACC (vary ±2% from base case)
- **Columns**: Terminal Growth (vary from 1.5% to 3.5%)
- **Output**: Enterprise Value at each combination

**Excel Data Table:**
```excel
1. Create table with WACC in left column, Terminal Growth in top row
2. Reference Enterprise Value formula in top-left cell
3. Select entire table
4. Data → What-If Analysis → Data Table
5. Row input: Terminal Growth cell
6. Column input: WACC cell
7. OK → Table populates automatically
```

**Best Practices:**
- Use realistic ranges (don't test WACC of 1% or 50%)
- Apply conditional formatting (green = high value, red = low value)
- Add "base case" marker to highlight your primary assumption
- Include 3-4 variations typically

---

## Common Assumptions by Industry

### Technology (SaaS)
- Revenue Growth: 20-40% (early stage), 10-20% (mature)
- EBITDA Margin: 20-30%
- WACC: 9-12%
- Terminal Growth: 2.5-3%

### Consumer Goods
- Revenue Growth: 3-8%
- EBITDA Margin: 15-25%
- WACC: 7-9%
- Terminal Growth: 2-2.5%

### Healthcare
- Revenue Growth: 5-12%
- EBITDA Margin: 18-28%
- WACC: 8-10%
- Terminal Growth: 2.5-3%

### Industrials
- Revenue Growth: 3-7%
- EBITDA Margin: 10-18%
- WACC: 7-9%
- Terminal Growth: 2-2.5%

---

## Validation Checks

Before finalizing your DCF:

### 1. Reasonableness Checks
- [ ] Revenue CAGR is achievable (check historical and industry average)
- [ ] EBITDA margin is in line with industry (check public comps)
- [ ] CapEx as % of revenue is reasonable (3-5% typical, higher for growth)
- [ ] Terminal growth ≤ Long-term GDP growth (2-3%)
- [ ] WACC is appropriate for risk profile

### 2. Mathematical Checks
- [ ] Terminal growth < WACC (model breaks if g ≥ WACC)
- [ ] All formulas link to Assumptions (no hard-coded values)
- [ ] Sum of percentages = 100% where applicable
- [ ] No circular references

### 3. Output Checks
- [ ] Terminal value is 60-80% of EV (not >90%)
- [ ] Implied valuation is reasonable vs public comps
- [ ] Sensitivity table shows reasonable range (not wild swings)
- [ ] Sign of FCF is positive in out-years

---

## Common Mistakes to Avoid

### 1. Over-Optimistic Growth
❌ **Mistake**: Assuming 30% revenue growth indefinitely
✅ **Fix**: Taper growth rates (30% → 20% → 15% → 10% → 5%)

### 2. Ignoring Working Capital
❌ **Mistake**: Setting NWC change to zero
✅ **Fix**: Model NWC as % of revenue (typically 10-15%)

### 3. Terminal Growth Too High
❌ **Mistake**: Using 5% terminal growth
✅ **Fix**: Use 2-3% (long-term GDP growth rate)

### 4. Not Linking Formulas
❌ **Mistake**: Hard-coding values in projection sheet
✅ **Fix**: Link all cells to Assumptions sheet

### 5. Ignoring CapEx
❌ **Mistake**: Minimal CapEx assumption
✅ **Fix**: Model realistic CapEx (3-5% of revenue, higher for growth companies)

---

## Advanced Techniques

### 1. Multiple Scenarios
Create 3 scenarios in separate columns:
- **Base Case**: Most likely assumptions
- **Upside**: Optimistic assumptions (+20% growth, +200bps margin)
- **Downside**: Conservative assumptions (-20% growth, -200bps margin)

### 2. Detailed Working Capital
Instead of NWC as % of revenue, model components:
- Days Sales Outstanding (DSO) for receivables
- Days Inventory Outstanding (DIO) for inventory
- Days Payables Outstanding (DPO) for payables

### 3. Explicit CapEx Build
Instead of CapEx as % of revenue, model:
- Maintenance CapEx (keep operations running)
- Growth CapEx (support revenue growth)
- Total CapEx = Maintenance + Growth

### 4. Multiple Exit Methods
Calculate terminal value using both:
- Gordon Growth Model (perpetuity method)
- Exit Multiple Method (exit EV/EBITDA)

Compare results for reasonableness.

---

## Formatting Standards

### Colors
- **Blue**: User inputs (assumptions)
- **Black**: Formulas (calculations)
- **Green**: Positive values (revenue, profit)
- **Red**: Negative values (expenses, outflows)

### Number Formats
- **Currency**: $1,234,567 or $1.2M
- **Percentages**: 15.0% (one decimal)
- **Multipliers**: 10.5x (one decimal)

### Structure
- Freeze top row and left column
- Bold headers
- Borders around key sections
- Subtotals and totals clearly labeled

---

## Resources & Further Reading

### Industry Data
- **CapIQ / Bloomberg**: For public company data
- **PitchBook / Preqin**: For private company data
- **Damodaran (NYU)**: Industry WACC and margin data

### Academic Resources
- **"Valuation" by McKinsey**: Industry standard textbook
- **"Investment Valuation" by Aswath Damodaran**: Comprehensive guide
- **CFA Institute**: DCF methodology resources

### Online Tools
- **Damodaran Online**: Free industry data and tools
- **FRED (Federal Reserve)**: Economic data (GDP growth, interest rates)
- **Yahoo Finance / Google Finance**: Public company financials

---

## Version History
- v1.0.0 (2025-10-27): Initial best practices guide
