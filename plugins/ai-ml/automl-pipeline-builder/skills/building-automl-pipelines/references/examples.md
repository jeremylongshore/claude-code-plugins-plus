# Examples

**Example: Tabular classification with a 1-hour budget**

```json
{
  "task_type": "classification",
  "time_budget_seconds": 3600,
  "algorithms": ["rf", "xgboost", "catboost"],
  "preprocessing": ["scaling", "encoding"],
  "tuning_strategy": "bayesian",
  "cv_folds": 5
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
