---
name: setting-up-experiment-tracking
description: |
  Implement machine learning experiment tracking using MLflow or Weights & Biases. Configures environment and provides code for logging parameters, metrics, and artifacts. Use when asked to "setup experiment tracking" or "initialize MLflow". Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Experiment Tracking Setup

This skill provides automated assistance for experiment tracking setup tasks.

## Overview


This skill provides automated assistance for experiment tracking setup tasks.
This skill streamlines the process of setting up experiment tracking for machine learning projects. It automates environment configuration, tool initialization, and provides code examples to get you started quickly.

## How It Works

1. **Analyze Context**: The skill analyzes the current project context to determine the appropriate experiment tracking tool (MLflow or W&B) based on user preference or existing project configuration.
2. **Configure Environment**: It configures the environment by installing necessary Python packages and setting environment variables.
3. **Initialize Tracking**: The skill initializes the chosen tracking tool, potentially starting a local MLflow server or connecting to a W&B project.
4. **Provide Code Snippets**: It provides code snippets demonstrating how to log experiment parameters, metrics, and artifacts within your ML code.

## When to Use This Skill

This skill activates when you need to:
- Start tracking machine learning experiments in a new project.
- Integrate experiment tracking into an existing ML project.
- Quickly set up MLflow or Weights & Biases for experiment management.
- Automate the process of logging parameters, metrics, and artifacts.

## Examples

### Example 1: Starting a New Project with MLflow

User request: "track experiments using mlflow"

The skill will:
1. Install the `mlflow` Python package.
2. Generate example code for logging parameters, metrics, and artifacts to an MLflow server.

### Example 2: Integrating W&B into an Existing Project

User request: "setup experiment tracking with wandb"

The skill will:
1. Install the `wandb` Python package.
2. Generate example code for initializing W&B and logging experiment data.

## Best Practices

- **Tool Selection**: Consider the scale and complexity of your project when choosing between MLflow and W&B. MLflow is well-suited for local tracking, while W&B offers cloud-based collaboration and advanced features.
- **Consistent Logging**: Establish a consistent logging strategy for parameters, metrics, and artifacts to ensure comparability across experiments.
- **Artifact Management**: Utilize artifact logging to track models, datasets, and other relevant files associated with each experiment.

## Integration

This skill can be used in conjunction with other skills that generate or modify machine learning code, such as skills for model training or data preprocessing. It ensures that all experiments are properly tracked and documented.

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
