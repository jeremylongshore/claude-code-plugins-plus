---
name: Engineering Features for Machine Learning
description: |
  This skill empowers Claude to perform feature engineering tasks for machine learning. It creates, selects, and transforms features to improve model performance. Use this skill when the user requests feature creation, feature selection, feature transformation, or any request that involves improving the features used in a machine learning model. Trigger terms include "feature engineering", "feature selection", "feature transformation", "create features", "select features", "transform features", "improve model performance", and similar phrases related to feature manipulation.
---

## Overview

This skill enables Claude to leverage the feature-engineering-toolkit plugin to enhance machine learning models. It automates the process of creating new features, selecting the most relevant ones, and transforming existing features to better suit the model's needs. By using this skill, you can improve the accuracy, efficiency, and interpretability of your machine learning models.

## How It Works

1. **Analyzing Requirements**: Claude analyzes the user's request and identifies the specific feature engineering task required.
2. **Generating Code**: Claude generates Python code using the feature-engineering-toolkit plugin to perform the requested task. This includes data validation and error handling.
3. **Executing Task**: The generated code is executed, creating, selecting, or transforming features as requested.
4. **Providing Insights**: Claude provides performance metrics and insights related to the feature engineering process, such as the importance of newly created features or the impact of transformations on model performance.

## When to Use This Skill

This skill activates when you need to:
- Create new features from existing data to improve model accuracy.
- Select the most relevant features from a dataset to reduce model complexity and improve efficiency.
- Transform features to better suit the assumptions of a machine learning model (e.g., scaling, normalization, encoding).

## Examples

### Example 1: Improving Model Accuracy

User request: "Create new features from the existing 'age' and 'income' columns to improve the accuracy of a customer churn prediction model."

The skill will:
1. Generate code to create interaction terms between 'age' and 'income' (e.g., age * income, age / income).
2. Execute the code and evaluate the impact of the new features on model performance.

### Example 2: Reducing Model Complexity

User request: "Select the top 10 most important features from the dataset to reduce the complexity of a fraud detection model."

The skill will:
1. Generate code to calculate feature importance using a suitable method (e.g., Random Forest, SelectKBest).
2. Execute the code and select the top 10 features based on their importance scores.

## Best Practices

- **Data Validation**: Always validate the input data to ensure it is clean and consistent before performing feature engineering.
- **Feature Scaling**: Scale numerical features to prevent features with larger ranges from dominating the model.
- **Encoding Categorical Features**: Encode categorical features appropriately (e.g., one-hot encoding, label encoding) to make them suitable for machine learning models.

## Integration

This skill integrates with the feature-engineering-toolkit plugin, providing a seamless way to create, select, and transform features for machine learning models. It can be used in conjunction with other Claude Code skills to build complete machine learning pipelines.