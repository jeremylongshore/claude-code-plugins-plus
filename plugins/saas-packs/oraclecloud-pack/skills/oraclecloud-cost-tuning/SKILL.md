---
name: oraclecloud-cost-tuning
description: 'Track OCI spend with the Usage API and set up budget alerts.

  Use when monitoring Oracle Cloud costs, creating budgets, analyzing spend by compartment
  or service, or optimizing Universal Credits consumption.

  Trigger with "oraclecloud cost", "oci budget", "oci usage api", "oci spending",
  "oracle cloud cost tuning".

  '
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# Oracle Cloud Cost Tuning

## Overview

Track OCI spending programmatically using the Usage API and set up budget alerts before Universal Credits run out unexpectedly. OCI pricing varies by shape, region, and commitment level, and the Cost Analysis tool in the Console is buried and confusing. This skill uses the Usage API to query spend by compartment, service, and shape, creates budgets with alert rules, and covers optimization strategies including Always Free tier resources, preemptible instances, and reserved capacity.

**Purpose:** Get visibility into OCI spending through code, set proactive budget alerts, and identify cost optimization opportunities.

## Prerequisites

- **OCI tenancy** with an API signing key in `~/.oci/config`
- **Python 3.8+** with `pip install oci`
- **Tenancy OCID** (root compartment) for tenancy-wide cost queries
- **IAM policy** granting `read usage-reports` in the tenancy
- **Notification topic OCID** for budget alert delivery (see `oraclecloud-observability`)

## Instructions

### Step 1: Query Usage with the Usage API

The Usage API returns cost and usage data broken down by configurable dimensions:

```python
import oci
from datetime import datetime, timedelta

config = oci.config.from_file("~/.oci/config")
usage_api = oci.usage_api.UsageapiClient(config)

# Query last 30 days of spend by service
response = usage_api.request_summarized_usages(
    oci.usage_api.models.RequestSummarizedUsagesDetails(
        tenant_id=config["tenancy"],
        time_usage_started=(datetime.utcnow() - timedelta(days=30)).isoformat() + "Z",
        time_usage_ended=datetime.utcnow().isoformat() + "Z",
        granularity="DAILY",
        query_type="COST",
        group_by=["service"]
    )
)

total_cost = 0.0
for item in response.data.items:
    cost = item.computed_amount or 0
    total_cost += cost
    if cost > 0:
        print(f"{item.service}: ${cost:.2f} ({item.currency})")

print(f"\nTotal 30-day spend: ${total_cost:.2f}")
```

### Step 2: Break Down Cost by Compartment and Shape

Identify which compartments and shapes are driving your bill:

```python
# Cost by compartment
response = usage_api.request_summarized_usages(
    oci.usage_api.models.RequestSummarizedUsagesDetails(
        tenant_id=config["tenancy"],
        time_usage_started=(datetime.utcnow() - timedelta(days=30)).isoformat() + "Z",
        time_usage_ended=datetime.utcnow().isoformat() + "Z",
        granularity="MONTHLY",
        query_type="COST",
        group_by=["compartmentName", "skuName"]
    )
)

for item in response.data.items:
    cost = item.computed_amount or 0
    if cost > 1.0:  # Filter noise
        print(f"{item.compartment_name} | {item.sku_name}: ${cost:.2f}")
```

### Step 3: Create a Budget with Alert Rules

Budgets warn you before spend exceeds a threshold. Create them via SDK instead of hunting through the Console:

```python
budget_client = oci.budget.BudgetClient(config)

# Create a monthly budget for a specific compartment
budget = budget_client.create_budget(
    oci.budget.models.CreateBudgetDetails(
        compartment_id=config["tenancy"],
        target_type="COMPARTMENT",
        targets=["ocid1.compartment.oc1..example"],
        amount=500.0,
        reset_period="MONTHLY",
        display_name="Dev Environment Budget",
        description="Monthly budget for dev compartment"
    )
).data

print(f"Budget created: {budget.id}")

# Add alert rule at 80% threshold
budget_client.create_alert_rule(
    budget_id=budget.id,
    create_alert_rule_details=oci.budget.models.CreateAlertRuleDetails(
        type="ACTUAL",
        threshold=80.0,
        threshold_type="PERCENTAGE",
        display_name="80% Warning",
        recipients="oncall@example.com",
        message="Dev budget has reached 80% of $500 monthly limit."
    )
)

# Add critical alert at 95%
budget_client.create_alert_rule(
    budget_id=budget.id,
    create_alert_rule_details=oci.budget.models.CreateAlertRuleDetails(
        type="ACTUAL",
        threshold=95.0,
        threshold_type="PERCENTAGE",
        display_name="95% Critical",
        recipients="oncall@example.com",
        message="CRITICAL: Dev budget at 95%. Review immediately."
    )
)
print("Alert rules created: 80% warning + 95% critical")
```

### Step 4: Forecast Budget with Projected Spend

Set a forecast-based alert that warns you if your current burn rate will exceed the budget:

```python
budget_client.create_alert_rule(
    budget_id=budget.id,
    create_alert_rule_details=oci.budget.models.CreateAlertRuleDetails(
        type="FORECAST",
        threshold=100.0,
        threshold_type="PERCENTAGE",
        display_name="Forecast Overspend",
        recipients="oncall@example.com",
        message="Projected spend will exceed monthly budget based on current usage."
    )
)
print("Forecast alert created: warns if burn rate exceeds budget")
```

### Step 5: Cost Optimization Strategies

Apply these strategies to reduce OCI spending:

**Always Free tier resources** — run dev/test workloads for free:
- 2 AMD Compute VMs (1/8 OCPU, 1 GB each) or 4 Arm A1 VMs (24 GB total)
- 200 GB total block storage, 10 GB object storage
- 1 Autonomous Database (20 GB), 10 Mbps load balancer
- Monitoring: 500 million ingestion datapoints, 1 billion retrieval datapoints

**Preemptible instances** — up to 50% cheaper for fault-tolerant batch jobs:

```python
compute = oci.core.ComputeClient(config)

compute.launch_instance(
    oci.core.models.LaunchInstanceDetails(
        compartment_id="ocid1.compartment.oc1..example",
        availability_domain="Uocm:US-ASHBURN-AD-1",
        shape="VM.Standard.E4.Flex",
        shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
            ocpus=4.0,
            memory_in_gbs=16.0
        ),
        preemptible_instance_config=oci.core.models.PreemptibleInstanceConfigDetails(
            preemption_action=oci.core.models.TerminatePreemptionAction(
                type="TERMINATE",
                preserve_boot_volume=False
            )
        ),
        source_details=oci.core.models.InstanceSourceViaImageDetails(
            image_id="ocid1.image.oc1..example",
            source_type="image"
        ),
        create_vnic_details=oci.core.models.CreateVnicDetails(
            subnet_id="ocid1.subnet.oc1..example"
        ),
        display_name="batch-worker-preemptible"
    )
)
print("Preemptible instance launched — up to 50% cost savings")
```

**Reserved capacity** — commit for 1 or 3 years for predictable discounts. Savings vary by shape and term length, typically 30–60% off on-demand pricing.

## Output

Successful completion produces:
- Usage API queries showing cost breakdown by service, compartment, and SKU
- A monthly budget with alert rules at 80% and 95% thresholds
- A forecast-based alert for projected overspend
- Cost optimization patterns: Always Free resources, preemptible instances, and reserved capacity guidance

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| NotAuthenticated | 401 | Bad API key or wrong tenancy | Verify `~/.oci/config` fields match your tenancy |
| NotAuthorizedOrNotFound | 404 | Missing `read usage-reports` policy | Add: `Allow group X to read usage-reports in tenancy` |
| TooManyRequests | 429 | Rate limited on Usage API | Reduce query frequency; cache daily results |
| InvalidParameter | 400 | Invalid date range or granularity | Ensure dates are ISO format with Z suffix; use DAILY or MONTHLY |
| InternalError | 500 | OCI Usage API service issue | Check [OCI Status](https://ocistatus.oraclecloud.com) and retry |
| ServiceError status -1 | N/A | Timeout on large cost queries | Narrow date range or reduce `group_by` dimensions |

## Examples

**Quick cost check with OCI CLI:**

```bash
# List all budgets in your tenancy
oci budgets budget list --compartment-id $OCI_TENANCY_OCID

# Get current month spend summary
oci usage-api usage-summary request-summarized-usages \
  --tenant-id $OCI_TENANCY_OCID \
  --time-usage-started "$(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --time-usage-ended "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --granularity MONTHLY \
  --query-type COST
```

**Daily cost tracker script:**

```python
import oci
from datetime import datetime, timedelta

config = oci.config.from_file("~/.oci/config")
usage_api = oci.usage_api.UsageapiClient(config)

# Yesterday's spend
yesterday = datetime.utcnow() - timedelta(days=1)
response = usage_api.request_summarized_usages(
    oci.usage_api.models.RequestSummarizedUsagesDetails(
        tenant_id=config["tenancy"],
        time_usage_started=yesterday.replace(hour=0, minute=0).isoformat() + "Z",
        time_usage_ended=yesterday.replace(hour=23, minute=59).isoformat() + "Z",
        granularity="DAILY",
        query_type="COST",
        group_by=["service"]
    )
)

daily_total = sum(i.computed_amount or 0 for i in response.data.items)
print(f"Yesterday's spend: ${daily_total:.2f}")
for item in sorted(response.data.items, key=lambda x: x.computed_amount or 0, reverse=True)[:5]:
    print(f"  {item.service}: ${item.computed_amount or 0:.2f}")
```

## Resources

- [OCI Cost Analysis](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/costanalysisoverview.htm) — Console cost tool documentation
- [OCI Budgets](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/budgetsoverview.htm) — budget creation and alert rules
- [OCI Pricing](https://www.oracle.com/cloud/pricing/) — current pricing by service and shape
- [OCI Always Free](https://www.oracle.com/cloud/free/) — permanent free tier resources
- [OCI Python SDK](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — SDK reference

## Next Steps

After cost monitoring is in place, review `oraclecloud-performance-tuning` to right-size instances based on actual metrics, or see `oraclecloud-observability` to route budget alerts through the same notification topics as your infrastructure alarms.
