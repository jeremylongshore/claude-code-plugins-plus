# LBO Model Formula Templates

## Sources & Uses

### Sources

- Senior Debt
- Mezzanine Debt
- Sponsor Equity
- Rollover Equity

### Uses

- Purchase Price (Enterprise Value)
- Transaction Fees
- Financing Fees
- Cash to Balance Sheet

## Debt Schedule Template

```
Opening Balance
+ Draws
- Mandatory Amortization
- Optional Prepayment (Cash Sweep)
= Closing Balance

Interest Expense = Opening Balance × Interest Rate
```

## IRR Calculation

```excel
=XIRR(cash_flows, dates)
```

### Cash Flow Series

- Year 0: -Equity_Contribution
- Year 1-N: Dividends (if any)
- Exit Year: Exit_Equity_Value

## MOIC Calculation

```excel
=Exit_Equity_Value / Initial_Equity_Contribution
```

## Exit Value

```excel
Exit_EV = Exit_EBITDA × Exit_Multiple
Exit_Equity = Exit_EV - Net_Debt_at_Exit
```
