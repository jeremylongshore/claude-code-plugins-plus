---
name: building-automl-pipelines
description: |
  This skill empowers Claude to build AutoML pipelines using the automl-pipeline-builder plugin. It is triggered when the user requests the creation of an automated machine learning pipeline, specifies the use of AutoML techniques, or asks for assistance in automating the machine learning model building process. The skill analyzes the context, generates code for the ML task, includes data validation and error handling, provides performance metrics, and saves artifacts with documentation. Use this skill when the user explicitly asks to "build automl pipeline", "create automated ml pipeline", or needs help with "automating machine learning workflows".
---

## Overview

This skill automates the creation of machine learning pipelines using the automl-pipeline-builder plugin. It simplifies the process of building, training, and evaluating machine learning models by automating feature engineering, model selection, and hyperparameter tuning.

## How It Works

1. **Analyze Requirements**: The skill analyzes the user's request and identifies the specific machine learning task and data requirements.
2. **Generate Code**: Based on the analysis, the skill generates the necessary code to build an AutoML pipeline using appropriate libraries.
3. **Implement Best Practices**: The skill incorporates data validation, error handling, and performance optimization techniques into the generated code.
4. **Provide Insights**: After execution, the skill provides performance metrics, insights, and documentation for the created pipeline.

## When to Use This Skill

This skill activates when you need to:
- Build an automated machine learning pipeline.
- Automate the process of model selection and hyperparameter tuning.
- Generate code for a complete AutoML workflow.

## Examples

### Example 1: Creating a Classification Pipeline

User request: "Build an AutoML pipeline for classifying customer churn."

The skill will:
1. Generate code to load and preprocess customer data.
2. Create an AutoML pipeline that automatically selects and tunes a classification model.

### Example 2: Optimizing a Regression Model

User request: "Create an automated ml pipeline to predict house prices."

The skill will:
1. Generate code to build a regression model using AutoML techniques.
2. Automatically select the best performing model and provide performance metrics.

## Best Practices

- **Data Preparation**: Ensure data is clean, properly formatted, and relevant to the machine learning task.
- **Performance Monitoring**: Continuously monitor the performance of the AutoML pipeline and retrain the model as needed.
- **Error Handling**: Implement robust error handling to gracefully handle unexpected issues during pipeline execution.

## Integration

This skill can be integrated with other data processing and visualization plugins to create end-to-end machine learning workflows. It can also be used in conjunction with deployment plugins to automate the deployment of trained models.