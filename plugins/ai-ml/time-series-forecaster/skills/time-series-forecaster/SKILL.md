---
name: forecasting-time-series-data
description: |
  This skill enables AI assistant to forecast future values based on historical time series data. it analyzes time-dependent data to identify trends, seasonality, and other patterns. use this skill when the user asks to predict future values of a time ser... Use when appropriate context detected. Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## Overview


This skill provides automated assistance for time series forecaster tasks.
This skill empowers Claude to perform time series forecasting, providing insights into future trends and patterns. It automates the process of data analysis, model selection, and prediction generation, delivering valuable information for decision-making.

## How It Works

1. **Data Analysis**: Claude analyzes the provided time series data, identifying key characteristics such as trends, seasonality, and autocorrelation.
2. **Model Selection**: Based on the data characteristics, Claude selects an appropriate forecasting model (e.g., ARIMA, Prophet).
3. **Prediction Generation**: The selected model is trained on the historical data, and future values are predicted along with confidence intervals.

## When to Use This Skill

This skill activates when you need to:
- Forecast future sales based on past sales data.
- Predict website traffic for the next month.
- Analyze trends in stock prices over the past year.

## Examples

### Example 1: Forecasting Sales

User request: "Forecast sales for the next quarter based on the past 3 years of monthly sales data."

The skill will:
1. Analyze the historical sales data to identify trends and seasonality.
2. Select and train a suitable forecasting model (e.g., ARIMA or Prophet).
3. Generate a forecast of sales for the next quarter, including confidence intervals.

### Example 2: Predicting Website Traffic

User request: "Predict weekly website traffic for the next month based on the last 6 months of data."

The skill will:
1. Analyze the website traffic data to identify patterns and seasonality.
2. Choose an appropriate time series forecasting model.
3. Generate a forecast of weekly website traffic for the next month.

## Best Practices

- **Data Quality**: Ensure the time series data is clean, complete, and accurate for optimal forecasting results.
- **Model Selection**: Choose a forecasting model appropriate for the characteristics of the data (e.g., ARIMA for stationary data, Prophet for data with strong seasonality).
- **Evaluation**: Evaluate the performance of the forecasting model using appropriate metrics (e.g., Mean Absolute Error, Root Mean Squared Error).

## Integration

This skill can be integrated with other data analysis and visualization tools within the Claude Code ecosystem to provide a comprehensive solution for time series analysis and forecasting.

## Prerequisites

- Appropriate file access permissions
- Required dependencies installed

## Instructions

1. Invoke this skill when the trigger conditions are met
2. Provide necessary context and parameters
3. Review the generated output
4. Apply modifications as needed

## Output

The skill produces structured output relevant to the task.

## Error Handling

- Invalid input: Prompts for correction
- Missing dependencies: Lists required components
- Permission errors: Suggests remediation steps

## Resources

- Project documentation
- Related skills and commands