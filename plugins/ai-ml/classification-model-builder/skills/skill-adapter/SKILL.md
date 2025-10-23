---
name: building-classification-models
description: |
  This skill enables Claude to construct and evaluate classification models using provided datasets or specifications. It leverages the classification-model-builder plugin to automate model creation, optimization, and reporting. Use this skill when the user requests to "build a classifier", "create a classification model", "train a classification model", or needs help with supervised learning tasks involving labeled data. The skill ensures best practices are followed, including data validation, error handling, and performance metric reporting.
---

## Overview

This skill empowers Claude to efficiently build and deploy classification models. It automates the process of model selection, training, and evaluation, providing users with a robust and reliable classification solution. The skill also provides insights into model performance and suggests potential improvements.

## How It Works

1. **Context Analysis**: Claude analyzes the user's request, identifying the dataset, target variable, and any specific requirements for the classification model.
2. **Model Generation**: The skill utilizes the classification-model-builder plugin to generate code for training a classification model based on the identified dataset and requirements. This includes data preprocessing, feature selection, model selection, and hyperparameter tuning.
3. **Evaluation and Reporting**: The generated model is trained and evaluated using appropriate metrics (e.g., accuracy, precision, recall, F1-score). Performance metrics and insights are then provided to the user.

## When to Use This Skill

This skill activates when you need to:
- Build a classification model from a given dataset.
- Train a classifier to predict categorical outcomes.
- Evaluate the performance of a classification model.

## Examples

### Example 1: Building a Spam Classifier

User request: "Build a classifier to detect spam emails using this dataset."

The skill will:
1. Analyze the provided email dataset to identify features and the target variable (spam/not spam).
2. Generate Python code using the classification-model-builder plugin to train a spam classification model, including data cleaning, feature extraction, and model selection.

### Example 2: Predicting Customer Churn

User request: "Create a classification model to predict customer churn using customer data."

The skill will:
1. Analyze the customer data to identify relevant features and the churn status.
2. Generate code to build a classification model for churn prediction, including data validation, model training, and performance reporting.

## Best Practices

- **Data Quality**: Ensure the input data is clean and preprocessed before training the model.
- **Model Selection**: Choose the appropriate classification algorithm based on the characteristics of the data and the specific requirements of the task.
- **Hyperparameter Tuning**: Optimize the model's hyperparameters to achieve the best possible performance.

## Integration

This skill integrates with the classification-model-builder plugin to automate the model building process. It can also be used in conjunction with other plugins for data analysis and visualization.