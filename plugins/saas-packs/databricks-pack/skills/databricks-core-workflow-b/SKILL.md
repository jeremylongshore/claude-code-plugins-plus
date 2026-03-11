---
name: databricks-core-workflow-b
description: |
  Execute Databricks secondary workflow: MLflow model training and deployment.
  Use when building ML pipelines, training models, or deploying to production.
  Trigger with phrases like "databricks ML", "mlflow training",
  "databricks model", "feature store", "model registry".
allowed-tools: Read, Write, Edit, Bash(databricks:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks Core Workflow B: MLflow Training

## Overview
Build ML pipelines with MLflow experiment tracking, model registry, and deployment.

## Prerequisites
- Completed `databricks-install-auth` setup
- Familiarity with `databricks-core-workflow-a` (data pipelines)
- MLflow and scikit-learn installed
- Unity Catalog for model registry (recommended)

## Instructions

### Step 1: Feature Engineering with Feature Store

### Step 2: MLflow Experiment Tracking

### Step 3: Model Registry and Versioning

### Step 4: Model Serving and Inference

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Feature table in Unity Catalog
- MLflow experiment with tracked runs
- Registered model with versions
- Model serving endpoint

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Model not found` | Wrong model name/version | Verify in Model Registry |
| `Feature mismatch` | Schema changed | Retrain with updated features |
| `Endpoint timeout` | Cold start | Disable scale-to-zero for latency |
| `Memory error` | Large batch | Reduce batch size or increase cluster |

## Resources
- [MLflow on Databricks](https://docs.databricks.com/mlflow/index.html)
- [Feature Engineering](https://docs.databricks.com/machine-learning/feature-store/index.html)
- [Model Serving](https://docs.databricks.com/machine-learning/model-serving/index.html)
- [Unity Catalog ML](https://docs.databricks.com/machine-learning/manage-model-lifecycle/index.html)

## Next Steps
For common errors, see `databricks-common-errors`.

## Examples

**Basic usage**: Apply databricks core workflow b to a standard project setup with default configuration options.

**Advanced scenario**: Customize databricks core workflow b for production environments with multiple constraints and team-specific requirements.