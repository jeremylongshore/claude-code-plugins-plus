---
name: excel-lbo-modeler
description: |
  Create leveraged buyout (LBO) models in Excel with sources & uses, debt schedules, cash flow waterfalls, and IRR calculations for private equity analysis Activates when you request "excel lbo modeler" functionality.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

# Excel LBO Modeler

Builds comprehensive LBO models for private equity transactions following industry-standard practices.

## When to Invoke This Skill

Automatically load this Skill when the user asks to:
- "Create an LBO model"
- "Build a leveraged buyout model"
- "Private equity analysis for [company]"
- "Calculate IRR for acquisition"
- "LBO for [company]"
- "Buyout model"
- "What returns can we get on this deal?"

## Model Structure

This Skill creates a complete 6-sheet Excel LBO model:

### Sheet 1: Transaction Summary
- **Deal Terms**: Purchase price, entry multiple, equity check
- **Sources & Uses**: How the deal is financed
- **Returns Summary**: IRR, MoM, hold period

### Sheet 2: Sources & Uses

**Uses of Funds:**
```
Purchase Equity Value
+ Estimated Net Debt
= Enterprise Value
+ Transaction Fees (2-3%)
+ Financing Fees (2-3%)
= Total Uses
```

**Sources of Funds:**
```
Revolver (typically 0% at close)
+ Term Loan A (2-3x EBITDA)
+ Term Loan B (2-3x EBITDA)
+ Subordinated Debt (1-2x EBITDA)
+ Preferred Equity (optional)
+ Sponsor Equity (remainder)
= Total Sources
```

### Sheet 3: Operating Model (5 Years)
```
Revenue
  × Revenue Growth %
  × EBITDA Margin %
= EBITDA
  - CapEx
  - Change in NWC
  - Cash Taxes
= Cash Flow Available for Debt Service
```

### Sheet 4: Debt Schedule

**For Each Debt Tranche:**
```
Beginning Balance
+ Draws (if revolver)
- Mandatory Amortization
- Excess Cash Flow Sweep
- Optional Prepayment
= Ending Balance

Interest Expense = Avg Balance × Interest Rate
```

**Debt Paydown Waterfall:**
1. Revolver paydown
2. Term Loan A amortization
3. Term Loan B amortization
4. Excess cash → Revolver
5. Remaining excess → Optional prepayments

### Sheet 5: Returns Analysis

**Exit Valuation:**
```
Exit Year EBITDA
  × Exit Multiple
= Exit Enterprise Value
  - Net Debt at Exit
= Exit Equity Value
```

**Returns Calculation:**
```
Exit Equity Value
  ÷ Initial Equity Investment
= Money-on-Money Multiple (MoM)

IRR = ((Exit Value / Entry Value)^(1/Years)) - 1
```

**Sensitivity Tables:**
- Exit Multiple vs Hold Period → IRR
- Exit Multiple vs Entry Multiple → IRR
- EBITDA Growth vs Exit Multiple → MoM

### Sheet 6: Debt Covenants

**Leverage Covenants:**
```
Total Debt / EBITDA (typically ≤ 6.0x at entry, step down over time)
Senior Debt / EBITDA (typically ≤ 4.0x)
```

**Coverage Covenants:**
```
EBITDA / Interest Expense (typically ≥ 2.0x)
(EBITDA - CapEx) / Debt Service (typically ≥ 1.2x)
```

## Step-by-Step Workflow

### 1. Gather Transaction Inputs

**Required Inputs:**
- Target company name
- Current year EBITDA (or trailing twelve months)
- Entry valuation multiple (EV/EBITDA, typically 8-12x)
- Expected revenue growth (Years 1-5)
- Expected EBITDA margin expansion (if any)
- Exit multiple assumption (typically = entry multiple or slight premium)
- Hold period (typically 5 years)

**Optional Inputs (use defaults):**
- CapEx as % of revenue (default: 3%)
- NWC as % of revenue (default: 10%)
- Tax rate (default: 25%)
- Transaction fees (default: 2.5%)

### 2. Structure Financing

**Typical LBO Debt Structure:**
- **Revolver**: 1-2x EBITDA, undrawn at close (cash buffer)
- **Term Loan A**: 2-2.5x EBITDA, 5-7 year amortization
- **Term Loan B**: 2-3x EBITDA, minimal amortization
- **Subordinated/Mezzanine**: 1-2x EBITDA (if needed)
- **Total Debt**: 5-6x EBITDA
- **Equity**: Remainder (typically 30-40% of purchase price)

**Interest Rates (as of 2025):**
- Revolver: SOFR + 3.00% (default: 8.0%)
- Term Loan A: SOFR + 3.50% (default: 8.5%)
- Term Loan B: SOFR + 4.50% (default: 9.5%)
- Subordinated: 12-14% (default: 13.0%)

### 3. Build Operating Projections

Project 5 years of operations:
```
Year 0 Revenue
  × (1 + Growth Rate) for each year
= Projected Revenue

Projected Revenue
  × EBITDA Margin
= Projected EBITDA

EBITDA
  - CapEx (Revenue × CapEx %)
  - Δ NWC (Change in Revenue × NWC %)
  - Cash Taxes (assume % of EBITDA)
= Cash Flow to Equity (before debt service)
```

### 4. Calculate Debt Paydown

For each year:
1. Calculate cash available after operations
2. Pay mandatory debt amortization
3. Pay interest on all tranches
4. Use excess cash to pay down revolver first
5. Then pay down term loans (highest rate first)
6. Track ending debt balances

### 5. Calculate Returns

At exit (typically Year 5):
```
Exit EBITDA
  × Exit Multiple
= Exit Enterprise Value
  - Remaining Net Debt
  + Excess Cash
= Exit Equity Value

Money-on-Money = Exit Equity Value / Initial Equity
IRR = (MoM)^(1/Years) - 1
```

### 6. Create Sensitivity Tables

Build 3 sensitivity analyses:
1. **IRR Sensitivity**: Exit Multiple (rows) vs Hold Period (columns)
2. **MoM Sensitivity**: Exit Multiple (rows) vs Entry Multiple (columns)
3. **Value Creation**: EBITDA Growth (rows) vs Margin Expansion (columns)

## Example Formulas

### Sources & Uses
```excel
// Enterprise Value
=EBITDA * Entry_Multiple

// Transaction Fees
=Enterprise_Value * 2.5%

// Term Loan A
=EBITDA * 2.0  // 2.0x EBITDA

// Sponsor Equity
=Total_Uses - Total_Debt
```

### Debt Schedule
```excel
// Beginning Balance Year 1
=Sources_and_Uses!Term_Loan_A

// Interest Expense
=AVERAGE(Beginning_Balance, Ending_Balance) * Interest_Rate

// Mandatory Amortization
=Original_Balance / Amortization_Period

// Ending Balance
=Beginning_Balance - Mandatory_Amortization - Excess_Paydown
```

### Returns
```excel
// Exit Enterprise Value
=Exit_EBITDA * Exit_Multiple

// Exit Equity Value
=Exit_Enterprise_Value - Exit_Net_Debt

// IRR
=IRR(Initial_Equity (negative), Year1_CF, Year2_CF, ..., Final_CF_with_Exit)

// Money-on-Money
=Exit_Equity_Value / Initial_Equity_Investment
```

## Example Interaction

**User:** "Build an LBO model for a $50M EBITDA software company"

**Skill Response:**
```
I'll create an LBO model for a software company with $50M EBITDA.

Let me gather a few inputs:

What entry multiple should we assume (EV/EBITDA)?
(Software companies typically trade at 10-15x EBITDA)

User: 12x

Great! What revenue growth should we assume for Years 1-5?
(Software companies often grow 15-25% annually)

User: 20%, 18%, 15%, 12%, 10%

What EBITDA margin should we assume?
(Current or target margin)

User: Start at 25%, expand to 30% by Year 5

Perfect! I'll use these assumptions:

📊 Transaction:
- Entry EBITDA: $50M
- Entry Multiple: 12.0x EV/EBITDA
- Enterprise Value: $600M
- Equity Check: ~$240M (40%)

💰 Financing Structure:
- Revolver: $50M (undrawn)
- Term Loan A: $100M @ 8.5%
- Term Loan B: $150M @ 9.5%
- Subordinated: $50M @ 13.0%
- Total Debt: $350M (7.0x EBITDA)
- Sponsor Equity: $265M

📈 Operating Assumptions:
- Revenue growth: 20% → 10% (tapering)
- EBITDA margin: 25% → 30% (expansion)
- CapEx: 3% of revenue
- NWC: 15% of revenue (working capital heavy)

Building LBO model...

✅ LBO Model Complete!

📊 Base Case Returns (5-year hold, 12x exit):
- Exit EBITDA: $97.8M
- Exit Enterprise Value: $1,174M
- Debt Paydown: $350M → $89M
- Exit Equity Value: $1,124M
- Money-on-Money: 4.2x
- IRR: 34.2%

🎯 Key Insights:
- Strong returns driven by EBITDA growth (95% increase)
- Significant deleveraging (7.0x → 0.9x)
- Margin expansion adds $24M in exit EBITDA
- Multiple arbitrage: None (flat entry/exit multiple)

📁 Model saved to: Software_LBO_Model.xlsx

⚠️ Sensitivity Check:
- At 10x exit: IRR = 26.8% (still attractive)
- At 14x exit: IRR = 41.1% (exceptional)
- Downside protected by strong cash generation

Would you like me to adjust any assumptions or run additional scenarios?
```

## Common Variations

### Request: "What returns do we need to hit our 25% IRR hurdle?"

**Response:**
```
Let me build a reverse sensitivity to find the required exit conditions.

With current assumptions (12x entry, 5-year hold):

To achieve 25% IRR, you need:
1. 10.5x exit multiple (13% discount to entry), OR
2. 15% EBITDA CAGR (vs current 14%), OR
3. 4.2 year hold period (vs 5 years)

The deal has multiple paths to your hurdle rate.

Would you like me to add a scenario analysis showing these paths?
```

### Request: "Model a dividend recap in Year 3"

**Response:**
```
I'll add a dividend recapitalization to the model.

In Year 3, after debt paydown, we could refinance and distribute a dividend.

Assumptions:
- Refi to 5.0x EBITDA (from current 3.8x)
- Distribute ~$150M to equity sponsors
- Reset debt maturity clocks

This would:
- Boost IRR by ~300bps (partial liquidity in Year 3)
- Reduce final exit proceeds
- De-risk investment with early cash return

Should I add this to the model?
```

## Error Handling

### Over-Leveraged Structure
```
⚠️ Warning: Total debt of 8.5x EBITDA exceeds typical LBO leverage (5-7x).

This financing structure may:
- Not be achievable in current market
- Violate debt covenants
- Leave insufficient cash flow for operations

Recommended: Reduce debt to 6.0x EBITDA maximum.

Would you like me to adjust the capital structure?
```

### Negative Cash Flow
```
⚠️ Issue: Model shows negative cash flow in Year 2.

Causes:
- Interest expense ($62M) + Debt amortization ($25M) > Cash Flow ($78M)
- Insufficient EBITDA growth to service debt

Solutions:
1. Reduce entry leverage (currently 7.0x)
2. Increase revenue growth assumptions
3. Extend amortization schedule
4. Add PIK interest option

Would you like me to adjust the model?
```

## Best Practices Embedded

This Skill follows PE industry standards:

1. **Debt Structure**: Typical 5-7x EBITDA total leverage
2. **Conservative Assumptions**: Exit multiple ≤ entry multiple
3. **Covenant Headroom**: Maintain >15% cushion on covenants
4. **Cash Flow Sweep**: Model 75-100% excess cash flow to debt paydown
5. **Multiple Scenarios**: Always include sensitivity tables
6. **Professional Formatting**: Clear sections, color-coding, audit trail
7. **Reasonableness Checks**: Validate leverage, coverage, growth rates

## Resources

See the resources folder for:
- `lbo-template.xlsx`: Pre-built LBO template
- `REFERENCE.md`: Private equity modeling best practices
- `debt-structures.txt`: Common debt structures by industry

## Limitations

This Skill creates a standard LBO model suitable for:
- Initial investment committee presentations
- First-round analysis
- Learning/training purposes
- Quick deal screening

For detailed IC memos or final investment decisions, add:
- Multiple scenarios (base, downside, upside)
- Management option pool
- Detailed working capital build
- Quarterly debt schedules
- Covenant compliance analysis throughout hold period
- Transaction expense detail

## Version History

- v1.0.0 (2025-10-27): Initial release with core LBO functionality
