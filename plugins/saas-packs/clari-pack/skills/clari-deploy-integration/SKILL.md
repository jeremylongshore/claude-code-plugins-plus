---
name: clari-deploy-integration
description: |
  Deploy Clari export pipelines to production with Airflow, Cloud Functions, or Lambda.
  Use when scheduling automated exports, deploying to cloud platforms,
  or setting up serverless Clari sync.
  Trigger with phrases like "deploy clari", "clari airflow",
  "clari lambda", "clari cloud function", "clari scheduled export".
allowed-tools: Read, Write, Edit, Bash(gcloud:*), Bash(aws:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, revenue-intelligence, forecasting, clari]
compatible-with: claude-code
---

# Clari Deploy Integration

## Overview

Deploy Clari export pipelines to production environments: Airflow DAGs, AWS Lambda, or Google Cloud Functions for scheduled, serverless execution.

## Instructions

### Airflow DAG

```python
# dags/clari_export_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime, timedelta

def export_clari_forecast(**context):
    from clari_client import ClariClient, ClariConfig

    client = ClariClient(ClariConfig(
        api_key=Variable.get("clari_api_key"),
    ))

    period = context["params"].get("period", "2026_Q1")
    data = client.export_and_download("company_forecast", period)

    entries = data.get("entries", [])
    context["ti"].xcom_push(key="entry_count", value=len(entries))
    # Load to warehouse here

dag = DAG(
    "clari_daily_export",
    schedule_interval="0 6 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
)

export_task = PythonOperator(
    task_id="export_forecast",
    python_callable=export_clari_forecast,
    dag=dag,
)
```

### AWS Lambda

```python
# lambda_handler.py
import json
import boto3
from clari_client import ClariClient, ClariConfig

def handler(event, context):
    ssm = boto3.client("ssm")
    api_key = ssm.get_parameter(
        Name="/clari/api-key", WithDecryption=True
    )["Parameter"]["Value"]

    client = ClariClient(ClariConfig(api_key=api_key))
    data = client.export_and_download(
        event.get("forecast_name", "company_forecast"),
        event.get("period", "2026_Q1"),
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"entries": len(data.get("entries", []))}),
    }
```

### Google Cloud Function

```python
# main.py
import functions_framework
from google.cloud import secretmanager
from clari_client import ClariClient, ClariConfig

@functions_framework.http
def clari_export(request):
    sm = secretmanager.SecretManagerServiceClient()
    secret = sm.access_secret_version(name="projects/my-proj/secrets/clari-api-key/versions/latest")
    api_key = secret.payload.data.decode()

    client = ClariClient(ClariConfig(api_key=api_key))
    data = client.export_and_download("company_forecast", "2026_Q1")

    return {"entries": len(data.get("entries", []))}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Lambda timeout | Export takes > 15min | Use Step Functions for long jobs |
| Secret not found | Wrong parameter path | Verify SSM/Secret Manager path |
| Airflow task fails | Rate limited | Add retries with backoff |

## Resources

- [Airflow Documentation](https://airflow.apache.org/docs/)
- [AWS Lambda](https://docs.aws.amazon.com/lambda/)

## Next Steps

For webhook setup, see `clari-webhooks-events`.
