---
name: Evaluating Machine Learning Models
description: |
  This skill allows Claude to evaluate machine learning models using a comprehensive suite of metrics. It should be used when the user requests model performance analysis, validation, or testing. Claude can use this skill to assess model accuracy, precision, recall, F1-score, and other relevant metrics. Trigger this skill when the user mentions "evaluate model", "model performance", "testing metrics", "validation results", or requests a comprehensive "model evaluation".
---

## Overview

This skill empowers Claude to perform thorough evaluations of machine learning models, providing detailed performance insights. It leverages the `model-evaluation-suite` plugin to generate a range of metrics, enabling informed decisions about model selection and optimization.

## How It Works

1. **Analyzing Context**: Claude analyzes the user's request to identify the model to be evaluated and any specific metrics of interest.
2. **Executing Evaluation**: Claude uses the `/eval-model` command to initiate the model evaluation process within the `model-evaluation-suite` plugin.
3. **Presenting Results**: Claude presents the generated metrics and insights to the user, highlighting key performance indicators and potential areas for improvement.

## When to Use This Skill

This skill activates when you need to:
- Assess the performance of a machine learning model.
- Compare the performance of multiple models.
- Identify areas where a model can be improved.
- Validate a model's performance before deployment.

## Examples

### Example 1: Evaluating Model Accuracy

User request: "Evaluate the accuracy of my image classification model."

The skill will:
1. Invoke the `/eval-model` command.
2. Analyze the model's performance on a held-out dataset.
3. Report the accuracy score and other relevant metrics.

### Example 2: Comparing Model Performance

User request: "Compare the F1-score of model A and model B."

The skill will:
1. Invoke the `/eval-model` command for both models.
2. Extract the F1-score from the evaluation results.
3. Present a comparison of the F1-scores for model A and model B.

## Best Practices

- **Specify Metrics**: Clearly define the specific metrics of interest for the evaluation.
- **Data Validation**: Ensure the data used for evaluation is representative of the real-world data the model will encounter.
- **Interpret Results**: Provide context and interpretation of the evaluation results to facilitate informed decision-making.

## Integration

This skill integrates seamlessly with the `model-evaluation-suite` plugin, providing a comprehensive solution for model evaluation within the Claude Code environment. It can be combined with other skills to build automated machine learning workflows.