# DCF Model Formula Templates

## Free Cash Flow Calculation

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

## Excel Formulas

### FCF Formula

```excel
=NOPAT + D&A - CapEx - ΔWC
```

### Present Value of FCF

```excel
=FCF_Year1/(1+WACC)^1 + FCF_Year2/(1+WACC)^2 + ... + FCF_Year5/(1+WACC)^5
```

### Terminal Value (Gordon Growth)

```excel
=FCF_Year5*(1+TerminalGrowth)/(WACC-TerminalGrowth)
```

### PV of Terminal Value

```excel
=TerminalValue/(1+WACC)^5
```

### Enterprise Value

```excel
=SUM(PV_FCF) + PV_TerminalValue
```

### Equity Value

```excel
=EnterpriseValue - NetDebt + NonOperatingAssets
```

### Per Share Value

```excel
=EquityValue/SharesOutstanding
```

## WACC Calculation

```excel
WACC = (E/V) × Re + (D/V) × Rd × (1-Tc)

Where:
E = Market value of equity
D = Market value of debt
V = E + D
Re = Cost of equity (CAPM)
Rd = Cost of debt
Tc = Corporate tax rate
```

### Cost of Equity (CAPM)

```excel
Re = Rf + β × (Rm - Rf)

Where:
Rf = Risk-free rate (10Y Treasury)
β = Beta (levered)
Rm - Rf = Equity risk premium
```

## Sensitivity Table Template

| Terminal Growth | 8% WACC | 10% WACC | 12% WACC |
|-----------------|---------|----------|----------|
| 2.0% | =formula | =formula | =formula |
| 2.5% | =formula | =formula | =formula |
| 3.0% | =formula | =formula | =formula |

Use DATA TABLE function for dynamic sensitivity analysis.
