---
name: training-machine-learning-models
description: |
  This skill trains machine learning models using automated workflows. It analyzes datasets, selects appropriate model types (classification, regression, etc.), configures training parameters, trains the model with cross-validation, generates performance metrics, and saves the trained model artifact. Use this skill when the user requests to "train" a model, needs to evaluate a dataset for machine learning purposes, or wants to optimize model performance. The skill supports common frameworks like scikit-learn.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to automatically train and evaluate machine learning models. It streamlines the model development process by handling data analysis, model selection, training, and evaluation, ultimately providing a persisted model artifact.

## How It Works

1. **Data Analysis and Preparation**: The skill analyzes the provided dataset and identifies the target variable, determining the appropriate model type (classification, regression, etc.).
2. **Model Selection and Training**: Based on the data analysis, the skill selects a suitable machine learning model and configures the training parameters. It then trains the model using cross-validation techniques.
3. **Performance Evaluation and Persistence**: After training, the skill generates performance metrics to evaluate the model's effectiveness. Finally, it saves the trained model artifact for future use.

## When to Use This Skill

This skill activates when you need to:
- Train a machine learning model on a given dataset.
- Evaluate the performance of a machine learning model.
- Automate the machine learning model training process.

## Examples

### Example 1: Training a Classification Model

User request: "Train a classification model on this dataset of customer churn data."

The skill will:
1. Analyze the customer churn data, identify the churn status as the target variable, and determine that a classification model is appropriate.
2. Select a suitable classification algorithm (e.g., Logistic Regression, Random Forest), train the model using cross-validation, and generate performance metrics such as accuracy, precision, and recall.

### Example 2: Training a Regression Model

User request: "Train a regression model to predict house prices based on features like size, location, and number of bedrooms."

The skill will:
1. Analyze the house price data, identify the price as the target variable, and determine that a regression model is appropriate.
2. Select a suitable regression algorithm (e.g., Linear Regression, Support Vector Regression), train the model using cross-validation, and generate performance metrics such as Mean Squared Error (MSE) and R-squared.

## Best Practices

- **Data Quality**: Ensure the dataset is clean and properly formatted before training the model.
- **Feature Engineering**: Consider feature engineering techniques to improve model performance.
- **Hyperparameter Tuning**: Experiment with different hyperparameter settings to optimize model performance.

## Integration

This skill can be used in conjunction with other data analysis and manipulation tools to prepare data for training. It can also integrate with model deployment tools to deploy the trained model to production.