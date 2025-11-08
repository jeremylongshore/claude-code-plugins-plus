---
name: splitting-datasets
description: |
  This skill enables Claude to split datasets into training, validation, and testing sets. It is useful when preparing data for machine learning model development. Use this skill when the user requests to split a dataset, create train-test splits, or needs data partitioning for model training. The skill is triggered by terms like "split dataset," "train-test split," "validation set," or "data partitioning."
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill automates the process of dividing a dataset into subsets for training, validating, and testing machine learning models. It ensures proper data preparation and facilitates robust model evaluation.

## How It Works

1. **Analyze Request**: The skill analyzes the user's request to determine the dataset to be split and the desired proportions for each subset.
2. **Generate Code**: Based on the request, the skill generates Python code utilizing standard ML libraries to perform the data splitting.
3. **Execute Splitting**: The code is executed to split the dataset into training, validation, and testing sets according to the specified ratios.

## When to Use This Skill

This skill activates when you need to:
- Prepare a dataset for machine learning model training.
- Create training, validation, and testing sets.
- Partition data to evaluate model performance.

## Examples

### Example 1: Splitting a CSV file

User request: "Split the data in 'my_data.csv' into 70% training, 15% validation, and 15% testing sets."

The skill will:
1. Generate Python code to read the 'my_data.csv' file.
2. Execute the code to split the data according to the specified proportions, creating 'train.csv', 'validation.csv', and 'test.csv' files.

### Example 2: Creating a Train-Test Split

User request: "Create a train-test split of 'large_dataset.csv' with an 80/20 ratio."

The skill will:
1. Generate Python code to load 'large_dataset.csv'.
2. Execute the code to split the dataset into 80% training and 20% testing sets, saving them as 'train.csv' and 'test.csv'.

## Best Practices

- **Data Integrity**: Verify that the splitting process maintains the integrity of the data, ensuring no data loss or corruption.
- **Stratification**: Consider stratification when splitting imbalanced datasets to maintain class distributions in each subset.
- **Randomization**: Ensure the splitting process is randomized to avoid bias in the resulting datasets.

## Integration

This skill can be integrated with other data processing and model training tools within the Claude Code ecosystem to create a complete machine learning workflow.