---
name: databricks-core-workflow-b
description: |
  Execute Databricks secondary workflow: MLflow model training and deployment.
  Use when building ML pipelines, training models, or deploying to production.
  Trigger with phrases like "databricks ML", "mlflow training",
  "databricks model", "feature store", "model registry".
allowed-tools: Read, Write, Edit, Bash(databricks:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks Core Workflow B: MLflow Training

## Overview
Build ML pipelines with MLflow experiment tracking, model registry, and deployment on Databricks. This workflow covers the full ML lifecycle from feature engineering through production model serving.

## Prerequisites
- Completed `databricks-install-auth` setup
- Familiarity with `databricks-core-workflow-a` (data pipelines)
- `databricks-sdk`, `mlflow`, `scikit-learn` installed (`pip install databricks-sdk mlflow scikit-learn`)
- Unity Catalog enabled for model registry (recommended)

## Instructions

### Step 1: Feature Engineering with Feature Store
Create a feature table in Unity Catalog so features are discoverable and reusable across models.

```python
from databricks.feature_engineering import FeatureEngineeringClient
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

spark = SparkSession.builder.getOrCreate()
fe = FeatureEngineeringClient()

# Build features from your gold layer tables
user_features = (
    spark.table("prod_catalog.gold.user_events")
    .groupBy("user_id")
    .agg(
        F.count("event_id").alias("total_events"),
        F.avg("session_duration_sec").alias("avg_session_sec"),
        F.max("event_timestamp").alias("last_active"),
        F.countDistinct("event_type").alias("unique_event_types"),
    )
)

# Register as a feature table (creates or updates)
fe.create_table(
    name="prod_catalog.ml_features.user_behavior",
    primary_keys=["user_id"],
    df=user_features,
    description="User behavioral features for churn prediction",
)
```

### Step 2: MLflow Experiment Tracking
Set up an experiment and log training runs with parameters, metrics, and artifacts.

```python
import mlflow
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score

# Point MLflow to Databricks tracking server
mlflow.set_tracking_uri("databricks")
mlflow.set_experiment("/Users/team@company.com/churn-prediction")

# Load feature table as pandas DataFrame
features_df = spark.table("prod_catalog.ml_features.user_behavior").toPandas()
X = features_df.drop(columns=["user_id", "churned"])
y = features_df["churned"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train with experiment tracking
with mlflow.start_run(run_name="gbm-baseline"):
    params = {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.1}
    mlflow.log_params(params)

    model = GradientBoostingClassifier(**params)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mlflow.log_metric("accuracy", accuracy_score(y_test, y_pred))
    mlflow.log_metric("precision", precision_score(y_test, y_pred))
    mlflow.log_metric("recall", recall_score(y_test, y_pred))

    # Log model with signature for validation
    mlflow.sklearn.log_model(
        model,
        artifact_path="model",
        input_example=X_test.iloc[:5],
        registered_model_name="prod_catalog.ml_models.churn_predictor",
    )
```

### Step 3: Model Registry and Versioning
Promote models through stages using Unity Catalog model registry.

```python
from mlflow import MlflowClient

client = MlflowClient()
model_name = "prod_catalog.ml_models.churn_predictor"

# List all versions and their stages
for mv in client.search_model_versions(f"name='{model_name}'"):
    print(f"Version {mv.version}: status={mv.status}, stage={mv.current_stage}")

# Set an alias on the best version for serving
client.set_registered_model_alias(model_name, alias="champion", version=3)

# Load model by alias in downstream code
champion = mlflow.pyfunc.load_model(f"models:/{model_name}@champion")
predictions = champion.predict(X_test)
```

### Step 4: Model Serving and Inference
Deploy a model to a Databricks Model Serving endpoint for real-time predictions.

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    EndpointCoreConfigInput,
    ServedEntityInput,
)

w = WorkspaceClient()

# Create or update a serving endpoint
w.serving_endpoints.create_and_wait(
    name="churn-predictor-prod",
    config=EndpointCoreConfigInput(
        served_entities=[
            ServedEntityInput(
                entity_name="prod_catalog.ml_models.churn_predictor",
                entity_version="3",
                workload_size="Small",
                scale_to_zero_enabled=True,
            )
        ]
    ),
)

# Query the endpoint
import requests, json

endpoint_url = f"{w.config.host}/serving-endpoints/churn-predictor-prod/invocations"
headers = {"Authorization": f"Bearer {w.config.token}", "Content-Type": "application/json"}

payload = {"dataframe_records": [{"total_events": 42, "avg_session_sec": 120.5, "unique_event_types": 7}]}
response = requests.post(endpoint_url, headers=headers, json=payload)
print(response.json())  # {"predictions": [0]}
```

## Output
- Feature table registered at `prod_catalog.ml_features.user_behavior`
- MLflow experiment with logged runs, metrics, and model artifacts
- Model versions in Unity Catalog registry with aliases (`champion`, `challenger`)
- Live serving endpoint returning predictions via REST API

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `RESOURCE_DOES_NOT_EXIST` | Experiment path wrong | Verify path with `mlflow.search_experiments()` |
| `INVALID_PARAMETER_VALUE` on log_model | Missing input_example or signature | Pass `input_example=` to `log_model()` |
| `Model not found in registry` | Wrong three-level name | Use `catalog.schema.model_name` format |
| `Endpoint timeout` | Cold start from scale-to-zero | Disable `scale_to_zero_enabled` for latency-critical endpoints |
| `FEATURE_TABLE_NOT_FOUND` | Table not created or wrong catalog | Run `fe.create_table()` first, verify catalog context |
| `Memory error during training` | Dataset too large for driver | Use distributed training with `spark-sklearn` or sample data |

## Examples

### Hyperparameter Sweep with MLflow
```python
from sklearn.model_selection import ParameterGrid

param_grid = {"n_estimators": [100, 200], "max_depth": [3, 5, 7], "learning_rate": [0.05, 0.1]}

for params in ParameterGrid(param_grid):
    with mlflow.start_run(run_name=f"gbm-d{params['max_depth']}-n{params['n_estimators']}"):
        mlflow.log_params(params)
        model = GradientBoostingClassifier(**params)
        model.fit(X_train, y_train)
        mlflow.log_metric("accuracy", accuracy_score(y_test, model.predict(X_test)))
        mlflow.sklearn.log_model(model, "model")
```

### Batch Inference Job
```python
# Run as a scheduled Databricks job for daily scoring
champion = mlflow.pyfunc.load_model(f"models:/{model_name}@champion")
new_users = spark.table("prod_catalog.gold.active_users").toPandas()
new_users["churn_score"] = champion.predict_proba(new_users[feature_cols])[:, 1]
spark.createDataFrame(new_users).write.mode("overwrite").saveAsTable("prod_catalog.gold.churn_scores")
```

## Resources
- [MLflow on Databricks](https://docs.databricks.com/mlflow/index.html)
- [Feature Engineering](https://docs.databricks.com/machine-learning/feature-store/index.html)
- [Model Serving](https://docs.databricks.com/machine-learning/model-serving/index.html)
- [Unity Catalog Models](https://docs.databricks.com/machine-learning/manage-model-lifecycle/index.html)

## Next Steps
For common errors, see `databricks-common-errors`.
