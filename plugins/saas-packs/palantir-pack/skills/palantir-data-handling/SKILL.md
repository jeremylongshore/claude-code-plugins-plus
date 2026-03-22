---
name: palantir-data-handling
description: |
  Implement Palantir Foundry data handling with PII protection, markings, and GDPR compliance.
  Use when handling sensitive data in Foundry, implementing data classifications,
  or ensuring compliance with privacy regulations.
  Trigger with phrases like "palantir data", "foundry PII",
  "palantir GDPR", "foundry data protection", "palantir markings".
allowed-tools: Read, Write, Edit
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, data, privacy, compliance]
compatible-with: claude-code, codex, openclaw
---

# Palantir Data Handling

## Overview
Handle sensitive data in Foundry using markings (data classifications), column-level security, PII redaction in transforms, and GDPR/CCPA deletion workflows.

## Prerequisites
- Foundry enrollment with Markings enabled
- Understanding of your organization's data classification policy
- Familiarity with transforms (`palantir-core-workflow-a`)

## Instructions

### Step 1: Data Classification with Markings
Foundry Markings control who can access data at the dataset, column, or row level.

| Marking | Access | Use Case |
|---------|--------|----------|
| `PUBLIC` | All users | Aggregated reports, reference data |
| `INTERNAL` | Employees only | Business metrics, operational data |
| `CONFIDENTIAL` | Specific groups | Customer PII, financial data |
| `RESTRICTED` | Named individuals | Compensation, legal, M&A |

### Step 2: PII Redaction in Transforms
```python
from transforms.api import transform_df, Input, Output
from pyspark.sql import functions as F

@transform_df(
    Output("/Company/datasets/customers_safe"),
    customers=Input("/Company/datasets/raw_customers"),
)
def redact_pii(customers):
    """Create an analytics-safe view with PII removed."""
    return (
        customers
        .withColumn("email", F.sha2(F.col("email"), 256))           # Hash email
        .withColumn("phone", F.lit("***-***-****"))                   # Mask phone
        .withColumn("ssn", F.lit(None).cast("string"))                # Remove SSN
        .withColumn("name", F.concat(
            F.substring("first_name", 1, 1), F.lit("***")            # First initial only
        ))
        .drop("first_name", "last_name", "address", "date_of_birth")
    )
```

### Step 3: GDPR Right to Erasure
```python
def delete_user_data(client, user_id: str):
    """GDPR Article 17: delete all data for a specific user."""
    datasets_with_pii = [
        "/Company/datasets/raw_customers",
        "/Company/datasets/raw_orders",
        "/Company/datasets/customer_communications",
    ]
    for dataset_path in datasets_with_pii:
        # Trigger a transform that filters out the user
        client.ontologies.Action.apply(
            ontology="my-company",
            action_type="gdprDeleteUser",
            parameters={"userId": user_id, "datasetPath": dataset_path},
        )
    # Log the deletion for compliance
    client.ontologies.Action.apply(
        ontology="my-company",
        action_type="logDeletionRequest",
        parameters={
            "userId": user_id,
            "requestedAt": datetime.utcnow().isoformat(),
            "status": "completed",
        },
    )
```

### Step 4: Column-Level Security in Ontology
```python
# Define object type with restricted properties
# In Ontology Manager:
# - fullName: marking = CONFIDENTIAL
# - email: marking = CONFIDENTIAL  
# - department: marking = INTERNAL
# - employeeId: marking = INTERNAL

# Users without CONFIDENTIAL marking see:
# employeeId, department (but NOT fullName, email)
```

### Step 5: Data Retention Policy
```python
@transform_df(
    Output("/Company/datasets/events_retained"),
    events=Input("/Company/datasets/raw_events"),
)
def apply_retention(events):
    """Keep only last 2 years of data per retention policy."""
    from pyspark.sql import functions as F
    from datetime import datetime, timedelta

    cutoff = (datetime.utcnow() - timedelta(days=730)).strftime("%Y-%m-%d")
    return events.filter(F.col("event_date") >= cutoff)
```

## Output
- PII-redacted datasets safe for analytics
- GDPR deletion workflow with audit trail
- Column-level security via Foundry Markings
- Automated data retention enforcement

## Error Handling
| Compliance Risk | Detection | Mitigation |
|----------------|-----------|------------|
| PII in analytics dataset | Column scan | Apply redaction transform |
| Stale data beyond retention | Date filter | Schedule retention transforms |
| Missing deletion audit | Log review | Always log GDPR actions |
| Over-permissive markings | Access audit | Review marking assignments quarterly |

## Resources
- [Foundry Markings](https://www.palantir.com/docs/foundry)
- [Transforms Guide](https://www.palantir.com/docs/foundry/transforms-python/transforms)

## Next Steps
For access control, see `palantir-enterprise-rbac`.
