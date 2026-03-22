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
tags: [saas, databricks, deployment, ml, workflow]

---
# Databricks Core Workflow B: MLflow Training & Serving

## Overview
Full ML lifecycle on Databricks: Feature Engineering Client for discoverable features, MLflow experiment tracking with auto-logging, Unity Catalog model registry with aliases (`champion`/`challenger`), and Mosaic AI Model Serving endpoints for real-time inference via REST API.

## Prerequisites
- Completed `databricks-install-auth` and `databricks-core-workflow-a`
- `databricks-sdk`, `mlflow`, `scikit-learn` installed
- Unity Catalog enabled (required for model registry)

## Instructions

### Step 1: Feature Engineering with Feature Store
Create a feature table in Unity Catalog so features are discoverable and reusable.

```python
from databricks.feature_engineering import FeatureEngineeringClient
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

spark = SparkSession.builder.getOrCreate()
fe = FeatureEngineeringClient()

# Build features from gold layer tables
user_features = (
    spark.table("prod_catalog.gold.user_events")
    .groupBy("user_id")
    .agg(
        F.count("event_id").alias("total_events"),
        F.avg("session_duration_sec").alias("avg_session_sec"),
        F.max("event_timestamp").alias("last_active"),
        F.countDistinct("event_type").alias("unique_event_types"),
        F.datediff(F.current_date(), F.max("event_timestamp")).alias("days_since_last_active"),
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
```python
import mlflow
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Point MLflow to Databricks tracking server
mlflow.set_tracking_uri("databricks")
mlflow.set_experiment("/Users/team@company.com/churn-prediction")

# Load features
features_df = spark.table("prod_catalog.ml_features.user_behavior").toPandas()
X = features_df.drop(columns=["user_id", "churned"])
y = features_df["churned"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train with experiment tracking
with mlflow.start_run(run_name="gbm-baseline") as run:
    params = {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.1}
    mlflow.log_params(params)

    model = GradientBoostingClassifier(**params)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
    }
    mlflow.log_metrics(metrics)

    # Log model with signature for serving validation
    mlflow.sklearn.log_model(
        model,
        artifact_path="model",
        input_example=X_test.iloc[:5],
        registered_model_name="prod_catalog.ml_models.churn_predictor",
    )
    print(f"Run {run.info.run_id}: accuracy={metrics['accuracy']:.3f}")
```

### Step 3: Model Registry with Aliases
Unity Catalog model registry replaces legacy stages with aliases (`champion`, `challenger`).

```python
from mlflow import MlflowClient

client = MlflowClient()
model_name = "prod_catalog.ml_models.churn_predictor"

# List versions
for mv in client.search_model_versions(f"name='{model_name}'"):
    print(f"v{mv.version}: status={mv.status}, aliases={mv.aliases}")

# Promote best version to champion
client.set_registered_model_alias(model_name, alias="champion", version="3")

# Load model by alias in downstream code
champion = mlflow.pyfunc.load_model(f"models:/{model_name}@champion")
predictions = champion.predict(X_test)
```

### Step 4: Deploy Model Serving Endpoint
Mosaic AI Model Serving creates a REST API endpoint with auto-scaling.

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    EndpointCoreConfigInput, ServedEntityInput,
)

w = WorkspaceClient()

# Create or update a serving endpoint
endpoint = w.serving_endpoints.create_and_wait(
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
print(f"Endpoint ready: {endpoint.name} ({endpoint.state.ready})")
```

### Step 5: Query the Serving Endpoint
```python
import requests

# Score via REST API
url = f"{w.config.host}/serving-endpoints/churn-predictor-prod/invocations"
headers = {
    "Authorization": f"Bearer {w.config.token}",
    "Content-Type": "application/json",
}
payload = {
    "dataframe_records": [
        {"total_events": 42, "avg_session_sec": 120.5,
         "unique_event_types": 7, "days_since_last_active": 3},
    ]
}
response = requests.post(url, headers=headers, json=payload)
print(response.json())  # {"predictions": [0]}

# Or use the SDK
result = w.serving_endpoints.query(
    name="churn-predictor-prod",
    dataframe_records=[
        {"total_events": 42, "avg_session_sec": 120.5,
         "unique_event_types": 7, "days_since_last_active": 3},
    ],
)
print(result.predictions)
```

### Step 6: Batch Inference Job
```python
# Scheduled Databricks job for daily batch scoring
model_name = "prod_catalog.ml_models.churn_predictor"
champion = mlflow.pyfunc.load_model(f"models:/{model_name}@champion")

# Score all active users
active_users = spark.table("prod_catalog.gold.active_users").toPandas()
feature_cols = ["total_events", "avg_session_sec", "unique_event_types", "days_since_last_active"]
active_users["churn_probability"] = champion.predict_proba(active_users[feature_cols])[:, 1]

# Write scores back to Delta
(spark.createDataFrame(active_users[["user_id", "churn_probability"]])
    .write.mode("overwrite")
    .saveAsTable("prod_catalog.gold.churn_scores"))
```

## Output
- Feature table in Unity Catalog (`prod_catalog.ml_features.user_behavior`)
- MLflow experiment with logged runs, metrics, and artifacts
- Model versions in registry with `champion` alias
- Live serving endpoint at `/serving-endpoints/churn-predictor-prod/invocations`
- Batch scoring pipeline writing to `prod_catalog.gold.churn_scores`

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `RESOURCE_DOES_NOT_EXIST` | Wrong experiment path | Verify with `mlflow.search_experiments()` |
| `INVALID_PARAMETER_VALUE` on `log_model` | Missing signature | Pass `input_example=` to auto-infer signature |
| `Model not found in registry` | Wrong three-level name | Use `catalog.schema.model_name` format |
| `Endpoint FAILED` | Model loading error | Check endpoint events: `w.serving_endpoints.get("name").pending_config` |
| `429 on serving endpoint` | Rate limit exceeded | Increase `workload_size` or add traffic splitting |
| `FEATURE_TABLE_NOT_FOUND` | Table not created | Run `fe.create_table()` first |

## Examples

### Hyperparameter Sweep
```python
from sklearn.model_selection import ParameterGrid

grid = {"n_estimators": [100, 200], "max_depth": [3, 5, 7], "learning_rate": [0.05, 0.1]}
for params in ParameterGrid(grid):
    with mlflow.start_run(run_name=f"gbm-d{params['max_depth']}-n{params['n_estimators']}"):
        mlflow.log_params(params)
        model = GradientBoostingClassifier(**params)
        model.fit(X_train, y_train)
        mlflow.log_metric("accuracy", accuracy_score(y_test, model.predict(X_test)))
        mlflow.sklearn.log_model(model, "model")
```

## Resources
- [MLflow on Databricks](https://docs.databricks.com/aws/en/mlflow/)
- [Feature Engineering](https://docs.databricks.com/aws/en/machine-learning/feature-store/)
- [Model Serving](https://docs.databricks.com/aws/en/machine-learning/model-serving/)
- [Unity Catalog Models](https://docs.databricks.com/aws/en/mlflow/models)

## Next Steps
For common errors, see `databricks-common-errors`.
