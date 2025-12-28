---
name: creating-data-visualizations
description: |
  Generate plots, charts, and graphs from data with automatic visualization type selection. Use when requesting "visualization", "plot", "chart", or "graph". Trigger with phrases like 'generate', 'create', or 'scaffold'.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Data Visualization Creator

This skill provides automated assistance for data visualization creator tasks.

## Overview

This skill empowers Claude to transform raw data into compelling visual representations. It leverages intelligent automation to select optimal visualization types and generate informative plots, charts, and graphs. This skill helps users understand complex data more easily.

## How It Works

1. **Data Analysis**: Claude analyzes the provided data to understand its structure, type, and distribution.
2. **Visualization Selection**: Based on the data analysis, Claude selects the most appropriate visualization type (e.g., bar chart, scatter plot, line graph).
3. **Visualization Generation**: Claude generates the visualization using appropriate libraries and best practices for visual clarity and accuracy.

## When to Use This Skill

This skill activates when you need to:
- Create a visual representation of data.
- Generate a specific type of plot, chart, or graph (e.g., "create a bar chart").
- Explore data patterns and relationships through visualization.

## Examples

### Example 1: Visualizing Sales Data

User request: "Create a bar chart showing sales by region."

The skill will:
1. Analyze the sales data, identifying regions and corresponding sales figures.
2. Generate a bar chart with regions on the x-axis and sales on the y-axis.

### Example 2: Plotting Stock Prices

User request: "Plot the stock price of AAPL over the last year."

The skill will:
1. Retrieve historical stock price data for AAPL.
2. Generate a line graph showing the stock price over time.

## Best Practices

- **Data Clarity**: Ensure the data is clean and well-formatted before requesting a visualization.
- **Specific Requests**: Be specific about the desired visualization type and any relevant data filters.
- **Contextual Information**: Provide context about the data and the purpose of the visualization.

## Integration

This skill can be integrated with other data processing and analysis tools within the Claude Code environment. It can receive data from other skills and provide visualizations for further analysis or reporting.

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