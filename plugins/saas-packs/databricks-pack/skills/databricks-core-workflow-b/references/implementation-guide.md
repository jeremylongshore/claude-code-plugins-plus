# Databricks Core Workflow B: MLflow Training - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Feature Engineering with Feature Store
```python
from databricks.feature_engineering import FeatureEngineeringClient
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, avg, count, datediff, current_date

def create_customer_features(spark: SparkSession, orders_table: str) -> DataFrame:
    """Create customer features from order history."""
    orders_df = spark.table(orders_table)

    features_df = (
        orders_df
        .groupBy("customer_id")
        .agg(
            count("*").alias("total_orders"),
            avg("amount").alias("avg_order_value"),
            sum("amount").alias("lifetime_value"),
            max("order_date").alias("last_order_date"),
            min("order_date").alias("first_order_date"),
        )
        .withColumn(
            "days_since_last_order",
            datediff(current_date(), col("last_order_date"))
        )
        .withColumn(
            "customer_tenure_days",
            datediff(current_date(), col("first_order_date"))
        )
    )

    return features_df

def register_feature_table(
    spark: SparkSession,
    df: DataFrame,
    feature_table_name: str,
    primary_keys: list[str],
    description: str,
) -> None:
    """Register DataFrame as Feature Store table."""
    fe = FeatureEngineeringClient()

    fe.create_table(
        name=feature_table_name,
        primary_keys=primary_keys,
        df=df,
        description=description,
        tags={"team": "data-science", "domain": "customer"},
    )
```

### Step 2: MLflow Experiment Tracking
```python
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pandas as pd

def train_churn_model(
    spark,
    feature_table: str,
    label_column: str = "churned",
    experiment_name: str = "/Experiments/churn-prediction",
) -> str:
    """
    Train churn prediction model with MLflow tracking.

    Returns:
        run_id: MLflow run ID
    """
    # Set experiment
    mlflow.set_experiment(experiment_name)

    # Load features
    fe = FeatureEngineeringClient()
    df = spark.table(feature_table).toPandas()

    # Prepare data
    feature_cols = [c for c in df.columns if c not in [label_column, "customer_id"]]
    X = df[feature_cols]
    y = df[label_column]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train with MLflow tracking
    with mlflow.start_run() as run:
        # Log parameters
        params = {
            "n_estimators": 100,
            "max_depth": 10,
            "min_samples_split": 5,
            "random_state": 42,
        }
        mlflow.log_params(params)

        # Train model
        model = RandomForestClassifier(**params)
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "f1": f1_score(y_test, y_pred),
        }
        mlflow.log_metrics(metrics)

        # Log model with signature
        from mlflow.models import infer_signature
        signature = infer_signature(X_train, y_pred)

        mlflow.sklearn.log_model(
            model,
            artifact_path="model",
            signature=signature,
            input_example=X_train.head(5),
            registered_model_name="churn-prediction-model",
        )

        # Log feature importance
        importance_df = pd.DataFrame({
            "feature": feature_cols,
            "importance": model.feature_importances_
        }).sort_values("importance", ascending=False)
        mlflow.log_table(importance_df, "feature_importance.json")

        print(f"Run ID: {run.info.run_id}")
        print(f"Metrics: {metrics}")

        return run.info.run_id
```

### Step 3: Model Registry and Versioning
```python
from mlflow import MlflowClient
from mlflow.entities.model_registry import ModelVersion

def promote_model(
    model_name: str,
    version: int,
    stage: str = "Production",
    archive_existing: bool = True,
) -> ModelVersion:
    """
    Promote model version to specified stage.

    Args:
        model_name: Registered model name
        version: Model version number
        stage: Target stage (Staging, Production, Archived)
        archive_existing: Archive current production model
    """
    client = MlflowClient()

    # Archive existing production model
    if archive_existing and stage == "Production":
        for mv in client.search_model_versions(f"name='{model_name}'"):
            if mv.current_stage == "Production":
                client.transition_model_version_stage(
                    name=model_name,
                    version=mv.version,
                    stage="Archived",
                )

    # Promote new version
    model_version = client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage=stage,
    )

    # Add description
    client.update_model_version(
        name=model_name,
        version=version,
        description=f"Promoted to {stage} on {pd.Timestamp.now()}",
    )

    return model_version

def compare_model_versions(model_name: str) -> pd.DataFrame:
    """Compare metrics across model versions."""
    client = MlflowClient()
    versions = client.search_model_versions(f"name='{model_name}'")

    comparisons = []
    for v in versions:
        run = client.get_run(v.run_id)
        comparisons.append({
            "version": v.version,
            "stage": v.current_stage,
            "accuracy": run.data.metrics.get("accuracy"),
            "f1": run.data.metrics.get("f1"),
            "created": v.creation_timestamp,
        })

    return pd.DataFrame(comparisons)
```

### Step 4: Model Serving and Inference
```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    EndpointCoreConfigInput,
    ServedEntityInput,
    TrafficConfig,
    Route,
)

def deploy_model_endpoint(
    model_name: str,
    endpoint_name: str,
    model_version: str = None,  # None = latest
    scale_to_zero: bool = True,
    workload_size: str = "Small",
) -> str:
    """
    Deploy model to Databricks Model Serving endpoint.

    Returns:
        endpoint_url: Serving endpoint URL
    """
    w = WorkspaceClient()

    # Create or update endpoint
    endpoint = w.serving_endpoints.create_and_wait(
        name=endpoint_name,
        config=EndpointCoreConfigInput(
            served_entities=[
                ServedEntityInput(
                    name=f"{model_name}-entity",
                    entity_name=model_name,
                    entity_version=model_version,
                    workload_size=workload_size,
                    scale_to_zero_enabled=scale_to_zero,
                )
            ],
            traffic_config=TrafficConfig(
                routes=[
                    Route(
                        served_model_name=f"{model_name}-entity",
                        traffic_percentage=100,
                    )
                ]
            ),
        ),
    )

    return endpoint.name

def batch_inference(
    spark,
    model_uri: str,
    input_table: str,
    output_table: str,
    feature_columns: list[str],
) -> None:
    """Run batch inference with logged model."""
    import mlflow.pyfunc

    # Load model
    model = mlflow.pyfunc.spark_udf(spark, model_uri)

    # Read input data
    input_df = spark.table(input_table)

    # Run inference
    predictions_df = input_df.withColumn(
        "prediction",
        model(*[col(c) for c in feature_columns])
    )

    # Write predictions
    predictions_df.write \
        .format("delta") \
        .mode("overwrite") \
        .saveAsTable(output_table)
```


## Complete Examples

### Complete ML Pipeline Job
```python
from src.ml import features, training, registry

features_df = features.create_customer_features(spark, "catalog.silver.orders")
features.register_feature_table(
    spark, features_df,
    "catalog.ml.customer_features",
    ["customer_id"],
    "Customer behavior features"
)

run_id = training.train_churn_model(
    spark,
    "catalog.ml.customer_features",
    experiment_name="/Experiments/churn-v2"
)

comparison = registry.compare_model_versions("churn-prediction-model")
best_version = comparison.sort_values("f1", ascending=False).iloc[0]["version"]
registry.promote_model("churn-prediction-model", best_version, "Production")
```
