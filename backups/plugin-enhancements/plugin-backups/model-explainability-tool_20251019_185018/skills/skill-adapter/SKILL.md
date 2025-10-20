---
name: Explaining Machine Learning Models
description: |
  This skill enables Claude to provide interpretability and explainability for machine learning models. It is triggered when the user requests explanations for model predictions, insights into feature importance, or help understanding model behavior. The skill leverages techniques like SHAP and LIME to generate explanations. It is useful when debugging model performance, ensuring fairness, or communicating model insights to stakeholders. Use this skill when the user mentions "explain model", "interpret model", "feature importance", "SHAP values", or "LIME explanations".
---

## Overview

This skill empowers Claude to analyze and explain machine learning models. It helps users understand why a model makes certain predictions, identify the most influential features, and gain insights into the model's overall behavior.

## How It Works

1. **Analyze Context**: Claude analyzes the user's request and the available model data.
2. **Select Explanation Technique**: Claude chooses the most appropriate explanation technique (e.g., SHAP, LIME) based on the model type and the user's needs.
3. **Generate Explanations**: Claude uses the selected technique to generate explanations for model predictions.
4. **Present Results**: Claude presents the explanations in a clear and concise format, highlighting key insights and feature importances.

## When to Use This Skill

This skill activates when you need to:
- Understand why a machine learning model made a specific prediction.
- Identify the most important features influencing a model's output.
- Debug model performance issues by identifying unexpected feature interactions.
- Communicate model insights to non-technical stakeholders.
- Ensure fairness and transparency in model predictions.

## Examples

### Example 1: Understanding Loan Application Decisions

User request: "Explain why this loan application was rejected."

The skill will:
1. Analyze the loan application data and the model's prediction.
2. Calculate SHAP values to determine the contribution of each feature to the rejection decision.
3. Present the results, highlighting the features that most strongly influenced the outcome, such as credit score or debt-to-income ratio.

### Example 2: Identifying Key Factors in Customer Churn

User request: "Interpret the customer churn model and identify the most important factors."

The skill will:
1. Analyze the customer churn model and its predictions.
2. Use LIME to generate local explanations for individual customer churn predictions.
3. Aggregate the LIME explanations to identify the most important features driving churn, such as customer tenure or service usage.

## Best Practices

- **Model Type**: Choose the explanation technique that is most appropriate for the model type (e.g., tree-based models, neural networks).
- **Data Preprocessing**: Ensure that the data used for explanation is properly preprocessed and aligned with the model's input format.
- **Visualization**: Use visualizations to effectively communicate model insights and feature importances.

## Integration

This skill integrates with other data analysis and visualization plugins to provide a comprehensive model understanding workflow. It can be used in conjunction with data cleaning and preprocessing plugins to ensure data quality and with visualization tools to present the explanation results in an informative way.