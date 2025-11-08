---
name: performing-regression-analysis
description: |
  This skill empowers Claude to perform regression analysis and modeling using the regression-analysis-tool plugin. It analyzes datasets, generates appropriate regression models (linear, polynomial, etc.), validates the models, and provides performance metrics. Use this skill when the user explicitly requests regression analysis, prediction based on data, or mentions terms like "linear regression," "polynomial regression," "regression model," or "predictive modeling." This skill is also helpful when the user needs to understand the relationship between variables in a dataset.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill enables Claude to analyze data, build regression models, and provide insights into the relationships between variables. It leverages the regression-analysis-tool plugin to automate the process and ensure best practices are followed.

## How It Works

1. **Data Analysis**: Claude analyzes the provided data to understand its structure and identify potential relationships between variables.
2. **Model Generation**: Based on the data, Claude generates appropriate regression models (e.g., linear, polynomial).
3. **Model Validation**: Claude validates the generated models to ensure their accuracy and reliability.
4. **Performance Reporting**: Claude provides performance metrics and insights into the model's effectiveness.

## When to Use This Skill

This skill activates when you need to:
- Perform regression analysis on a given dataset.
- Predict future values based on existing data using regression models.
- Understand the relationship between independent and dependent variables.
- Evaluate the performance of a regression model.

## Examples

### Example 1: Predicting House Prices

User request: "Can you build a regression model to predict house prices based on square footage and number of bedrooms?"

The skill will:
1. Analyze the provided data on house prices, square footage, and number of bedrooms.
2. Generate a regression model (likely multiple to compare) to predict house prices.
3. Provide performance metrics such as R-squared and RMSE.

### Example 2: Analyzing Sales Trends

User request: "I need to analyze the sales data for the past year and identify any trends using regression analysis."

The skill will:
1. Analyze the provided sales data.
2. Generate a regression model to identify trends and patterns in the sales data.
3. Visualize the trend and report the equation and R-squared value.

## Best Practices

- **Data Preparation**: Ensure the data is clean and preprocessed before performing regression analysis.
- **Model Selection**: Choose the appropriate regression model based on the data and the problem.
- **Validation**: Always validate the model to ensure its accuracy and reliability.

## Integration

This skill works independently using the regression-analysis-tool plugin. It can be used in conjunction with other data analysis and visualization tools to provide a comprehensive understanding of the data.