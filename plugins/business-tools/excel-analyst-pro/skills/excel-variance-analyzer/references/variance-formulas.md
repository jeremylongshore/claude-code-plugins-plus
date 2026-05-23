# Variance Analysis Formula Templates

## Basic Variance

```excel
Variance = Actual - Budget
Variance % = (Actual - Budget) / ABS(Budget)
```

## Favorable/Unfavorable Logic

For Revenue (higher is better):

```excel
=IF(Actual > Budget, "Favorable", "Unfavorable")
```

For Expenses (lower is better):

```excel
=IF(Actual < Budget, "Favorable", "Unfavorable")
```

## Materiality Flag

```excel
=IF(ABS(Variance%) > Threshold, "Review Required", "")
```

## YTD Variance

```excel
YTD_Actual = SUM(Jan_Actual:Current_Month_Actual)
YTD_Budget = SUM(Jan_Budget:Current_Month_Budget)
YTD_Variance = YTD_Actual - YTD_Budget
```

## Waterfall Bridge Values

```excel
Start: Budget
Step 1: Revenue Variance
Step 2: COGS Variance
Step 3: OpEx Variance
End: Actual
```
