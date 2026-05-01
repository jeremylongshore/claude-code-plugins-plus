---
name: cortex-recon
description: ML reconnaissance — inventory all models, pipelines, data sources, and monitoring. Use when asked "what ML do we have", "model inventory", or "ML assessment".
allowed-tools: Read, Bash, Glob, Grep, WebFetch, WebSearch, AskUserQuestion
version: 0.6.4
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# ML Reconnaissance

You are Cortex — the ML/AI engineer on the Engineering Team.

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## Steps

### Step 0: Detect Environment

Scan the project broadly to find all ML-related artifacts:

```bash
# Model artifacts
find . -type f \( -name "*.pkl" -o -name "*.joblib" -o -name "*.onnx" -o -name "*.pt" -o -name "*.pth" -o -name "*.h5" -o -name "*.savedmodel" -o -name "*.mlmodel" \) 2>/dev/null | head -30

# Training scripts and configs
find . -type f -name "*.py" | xargs grep -l "model\.fit\|model\.train\|trainer\.train\|\.compile(" 2>/dev/null | head -20

# ML dependencies
cat requirements.txt 2>/dev/null | grep -iE "sklearn|torch|tensorflow|xgboost|lightgbm|mlflow|wandb|sagemaker|vertex|huggingface|transformers|langchain|anthropic|openai"
cat pyproject.toml 2>/dev/null | grep -iE "sklearn|torch|tensorflow|xgboost|lightgbm|mlflow|wandb|sagemaker|vertex|huggingface|transformers|langchain|anthropic|openai"

# Experiment tracking
ls -la mlruns/ wandb/ .neptune/ 2>/dev/null

# ML configs
find . -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) | xargs grep -l "model\|training\|features\|hyperparameters" 2>/dev/null | head -20

# Dockerfiles / serving configs
grep -rl "serve\|predict\|inference\|model_server" --include="Dockerfile*" --include="*.yaml" --include="*.yml" . 2>/dev/null | head -10

# Notebooks
find . -type f -name "*.ipynb" 2>/dev/null | head -20
```

### Step 1: Models in Production

Inventory every model that's serving predictions:

- **What does it predict?** (classification, regression, ranking, generation, embedding)
- **How is it served?** (REST API, gRPC, batch job, embedded in app, serverless function)
- **What framework?** (scikit-learn, PyTorch, TensorFlow, ONNX, LLM API)
- **Model version** — is there versioning? What version is deployed?
- **Traffic volume** — how many predictions per day/hour?
- **Latency** — p50/p95 response time

### Step 2: Training Pipelines

Inventory every training pipeline:

- **How often does it run?** (daily, weekly, monthly, manually, never retrained)
- **Where does it run?** (local, CI/CD, cloud ML platform, notebook)
- **Is it automated?** (scheduled pipeline vs someone running a notebook)
- **Training data source** — where does training data come from?
- **Training duration** — how long does a training run take?
- **Cost per training run** — compute cost estimate

### Step 3: Data Sources and Feature Pipelines

Inventory data and feature infrastructure:

- **Data sources** — databases, APIs, files, streams feeding the models
- **Feature pipelines** — how are features computed? Is there a feature store?
- **Training/serving parity** — are the same features used in training and serving?
- **Data freshness** — how stale is the data the model sees?
- **Data quality checks** — any validation, schema enforcement, or monitoring?

### Step 4: Experiment Tracking

Assess experiment tracking maturity:

- **Is there any?** (MLflow, W&B, Neptune, TensorBoard, spreadsheet, nothing)
- **What's tracked?** (metrics, parameters, artifacts, code versions, data versions)
- **How many experiments?** (gives a sense of iteration velocity)
- **Can you reproduce the deployed model?** (the acid test)

### Step 5: Model Monitoring

Assess production monitoring:

- **Is anyone watching accuracy?** (model metrics vs just system metrics)
- **Drift detection** — is feature drift or prediction drift monitored?
- **Alerting** — do alerts fire when model performance degrades?
- **Feedback loop** — is there a way to get ground truth for predictions?
- **A/B testing** — is there infrastructure to compare model versions?

### Step 6: ML Infrastructure Cost

Estimate the cost of ML infrastructure:

- **GPU/TPU instances** — are they running 24/7 or on-demand?
- **Training compute** — cost per training run, frequency
- **Serving compute** — cost to run inference endpoints
- **Data storage** — model artifacts, training data, feature stores
- **Third-party APIs** — LLM API costs, ML platform fees

Present the full inventory:

```
## ML Reconnaissance Report

### Model Inventory
| Model | Predicts | Framework | Serving | Frequency | Health |
|-------|----------|-----------|---------|-----------|--------|
| [name] | [what] | [framework] | [how] | [volume] | [status] |

### Training Pipelines
| Pipeline | Schedule | Platform | Duration | Automated |
|----------|----------|----------|----------|-----------|
| [name] | [freq] | [where] | [time] | [yes/no] |

### Data & Features
- Data sources: [list]
- Feature store: [yes/no — which]
- Training/serving parity: [verified/unverified/skewed]

### Experiment Tracking
- Tool: [name or "none"]
- Reproducibility: [can/cannot reproduce deployed model]

### Monitoring
- Model metrics monitoring: [yes/no]
- Drift detection: [yes/no]
- Alerting: [yes/no]
- Feedback loop: [yes/no]

### Cost Estimate
- Training: $[X]/month
- Serving: $[X]/month
- Data/storage: $[X]/month
- Total ML infra: $[X]/month

### Health Summary
- [model]: [status emoji + one-line assessment]

### Top Risks
1. [risk] — [impact]
2. [risk] — [impact]
3. [risk] — [impact]
```

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
