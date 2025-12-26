---
name: building-automl-pipelines
description: |
  Build automated machine learning pipelines with feature engineering, model selection, and hyperparameter tuning.
  Use when automating ML workflows from data preparation through model deployment.
  Trigger with phrases like "build automl pipeline", "automate ml workflow", or "create automated training pipeline".
  
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(python:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## Prerequisites

Before using this skill, ensure you have:
- Python environment with AutoML libraries (Auto-sklearn, TPOT, H2O AutoML, or PyCaret)
- Training dataset in accessible format (CSV, Parquet, or database)
- Understanding of problem type (classification, regression, time-series)
- Sufficient computational resources for automated search
- Knowledge of evaluation metrics appropriate for task
- Target variable and feature columns clearly defined

## Instructions

### Step 1: Define Pipeline Requirements
Specify the machine learning task and constraints:
1. Identify problem type (binary/multi-class classification, regression, etc.)
2. Define evaluation metrics (accuracy, F1, RMSE, etc.)
3. Set time and resource budgets for AutoML search
4. Specify feature types and preprocessing needs
5. Determine model interpretability requirements

### Step 2: Prepare Data Infrastructure
Set up data access and preprocessing:
1. Load training data using Read tool
2. Perform initial data quality assessment
3. Configure train/validation/test split strategy
4. Define feature engineering transformations
5. Set up data validation checks

### Step 3: Configure AutoML Pipeline
Build the automated pipeline configuration:
- Select AutoML framework based on requirements
- Define search space for algorithms (random forest, XGBoost, neural networks, etc.)
- Configure feature preprocessing steps (scaling, encoding, imputation)
- Set hyperparameter tuning strategy (Bayesian optimization, random search, grid search)
- Establish early stopping criteria and timeout limits

### Step 4: Execute Pipeline Training
Run the automated training process:
1. Initialize AutoML pipeline with configuration
2. Execute automated feature engineering
3. Perform model selection across algorithm families
4. Conduct hyperparameter optimization for top models
5. Evaluate models using cross-validation

### Step 5: Analyze and Export Results
Evaluate pipeline performance and prepare for deployment:
- Compare model performances across metrics
- Extract best model and configuration
- Generate feature importance analysis
- Create model performance visualizations
- Export trained pipeline for deployment

## Output

The skill generates comprehensive AutoML pipeline artifacts:

### Pipeline Configuration Files
```python
# {baseDir}/automl_config.py


## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.
{
  "task_type": "classification",
  "time_budget": 3600,
  "algorithms": ["rf", "xgboost", "catboost"],
  "preprocessing": ["scaling", "encoding"],
  "tuning_strategy": "bayesian",
  "cv_folds": 5
}
```

### Pipeline Code
- Complete Python implementation of AutoML pipeline
- Data loading and preprocessing functions
- Feature engineering transformations
- Model training and evaluation logic
- Hyperparameter search configuration

### Model Performance Report
- Best model architecture and hyperparameters
- Cross-validation scores with confidence intervals
- Feature importance rankings
- Confusion matrix or residual plots
- ROC curves and precision-recall curves (for classification)

### Training Artifacts
- Serialized best model file (pickle, joblib, or ONNX)
- Feature preprocessing pipeline
- Training history and search logs
- Model performance metrics on test set
- Documentation for model deployment

### Deployment Package
- Prediction API code for serving model
- Input validation and preprocessing scripts
- Model loading and inference functions
- Example usage documentation
- Requirements file with dependencies

## Error Handling

Common issues and solutions:

**Insufficient Training Time**
- Error: AutoML search terminated before finding good model
- Solution: Increase time budget, reduce search space, or use faster algorithms

**Memory Exhaustion**
- Error: Out of memory during pipeline training
- Solution: Reduce dataset size through sampling, use incremental learning, or simplify feature engineering

**Poor Model Performance**
- Error: Best model accuracy below acceptable threshold
- Solution: Collect more data, engineer better features, expand algorithm search space, or adjust evaluation metrics

**Feature Engineering Failures**
- Error: Automated feature transformations produce invalid values
- Solution: Add data validation checks, handle missing values explicitly, restrict transformation types

**Model Convergence Issues**
- Error: Optimization fails to converge for certain algorithms
- Solution: Adjust hyperparameter ranges, increase iteration limits, or exclude problematic algorithms

## Resources

### AutoML Frameworks
- **Auto-sklearn**: Automated scikit-learn pipeline construction with metalearning
- **TPOT**: Genetic programming for pipeline optimization
- **H2O AutoML**: Scalable AutoML with ensemble methods
- **PyCaret**: Low-code ML library with automated workflows

### Feature Engineering
- Automated feature selection techniques
- Categorical encoding strategies (one-hot, target, ordinal)
- Numerical transformation methods (scaling, binning, polynomial features)
- Time-series feature extraction

### Hyperparameter Optimization
- Bayesian optimization with Gaussian processes
- Random search and grid search strategies
- Hyperband and successive halving algorithms
- Multi-objective optimization for multiple metrics

### Evaluation Strategies
- Cross-validation techniques (k-fold, stratified, time-series)
- Evaluation metrics selection guide
- Model ensembling and stacking approaches
- Bias-variance tradeoff analysis

### Best Practices
- Start with baseline models before AutoML
- Balance automation with domain knowledge
- Monitor resource consumption during search
- Validate model performance on holdout data
- Document pipeline decisions for reproducibility