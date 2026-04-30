---
name: oraclecloud-webhooks-events
description: 'Wire up event-driven workflows with OCI Events, Notifications, and Functions.

  Use when building serverless event processing, subscribing to instance lifecycle
  changes, or routing audit events to alerting systems.

  Trigger with "oraclecloud webhooks events", "oci events rules", "oci notifications",
  "oci ons topics".

  '
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(oci:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# Oracle Cloud Webhooks & Events

## Overview

Build event-driven workflows using the OCI Events service, Oracle Notification Service (ONS), and OCI Functions. OCI Events monitors resource state changes across your tenancy and fires rules that route events to ONS topics, streaming, or Functions. This skill covers event rule creation, ONS topic/subscription setup, event pattern matching syntax, and Functions integration.

**Purpose:** Create reliable event-driven pipelines that react to OCI resource changes in real time.

## Prerequisites

- **OCI Python SDK** — `pip install oci`
- **OCI config file** at `~/.oci/config` with valid credentials (user, fingerprint, tenancy, region, key_file)
- **IAM policies** granting access to Events, ONS, and Functions:
  - `Allow group EventAdmins to manage cloudevents-rules in compartment <name>`
  - `Allow group EventAdmins to manage ons-topics in compartment <name>`
  - `Allow group EventAdmins to use fn-function in compartment <name>`
- **Compartment OCID** for the target compartment
- Python 3.8+

## Instructions

### Step 1: Create an ONS Topic and Subscription

Create a notification topic that will receive events, then subscribe an endpoint (email, HTTPS, PagerDuty, or Slack via HTTPS):

```python
import oci

config = oci.config.from_file("~/.oci/config")
ons_control = oci.ons.NotificationControlPlaneClient(config)
ons_data = oci.ons.NotificationDataPlaneClient(config)

# Create a topic
topic_response = ons_control.create_topic(
    oci.ons.models.CreateTopicDetails(
        name="infra-alerts",
        compartment_id="ocid1.compartment.oc1..example",
        description="Infrastructure lifecycle alerts"
    )
)
topic_id = topic_response.data.topic_id
print(f"Topic created: {topic_id}")

# Subscribe an HTTPS endpoint (e.g., Slack incoming webhook)
subscription = ons_data.create_subscription(
    oci.ons.models.CreateSubscriptionDetails(
        topic_id=topic_id,
        compartment_id="ocid1.compartment.oc1..example",
        protocol="HTTPS",
        endpoint="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    )
)
print(f"Subscription: {subscription.data.id} ({subscription.data.lifecycle_state})")
```

### Step 2: Create an Events Rule

Events rules use a condition block that matches on `eventType`, `compartmentId`, and optional `attribute` filters. The condition syntax is JSON, not HCL:

```python
events_client = oci.events.EventsClient(config)

rule = events_client.create_rule(
    oci.events.models.CreateRuleDetails(
        display_name="instance-state-changes",
        compartment_id="ocid1.compartment.oc1..example",
        description="Fire on compute instance lifecycle changes",
        is_enabled=True,
        condition='{"eventType":["com.oraclecloud.computeapi.launchinstance.end","com.oraclecloud.computeapi.terminateinstance.end","com.oraclecloud.computeapi.instanceaction.end"]}',
        actions=oci.events.models.ActionDetailsList(
            actions=[
                oci.events.models.ActionDetails(
                    action_type="ONS",
                    topic_id=topic_id,
                    is_enabled=True,
                    description="Notify infra-alerts topic"
                )
            ]
        )
    )
)
print(f"Rule created: {rule.data.id}")
```

### Step 3: Common Event Types Reference

Use these exact `eventType` strings in your rule conditions:

| Category | Event Type | Fires When |
|----------|-----------|------------|
| Compute | `com.oraclecloud.computeapi.launchinstance.end` | Instance launch completes |
| Compute | `com.oraclecloud.computeapi.terminateinstance.end` | Instance terminated |
| Compute | `com.oraclecloud.computeapi.instanceaction.end` | Stop/start/reboot finishes |
| Storage | `com.oraclecloud.objectstorage.createbucket` | New bucket created |
| Storage | `com.oraclecloud.objectstorage.deleteobject` | Object deleted |
| Identity | `com.oraclecloud.identitycontrolplane.createuser` | New user created |
| Identity | `com.oraclecloud.identitycontrolplane.updatepolicy` | IAM policy modified |
| Audit | `com.oraclecloud.audit.event` | Any auditable action |

### Step 4: Route Events to a Function

For complex processing, route events to an OCI Function instead of (or in addition to) ONS:

```python
# Create a rule that invokes a Function
fn_rule = events_client.create_rule(
    oci.events.models.CreateRuleDetails(
        display_name="bucket-change-processor",
        compartment_id="ocid1.compartment.oc1..example",
        is_enabled=True,
        condition='{"eventType":["com.oraclecloud.objectstorage.createobject","com.oraclecloud.objectstorage.deleteobject"]}',
        actions=oci.events.models.ActionDetailsList(
            actions=[
                oci.events.models.ActionDetails(
                    action_type="FAAS",
                    function_id="ocid1.fnfunc.oc1.iad.example",
                    is_enabled=True,
                    description="Process bucket changes"
                )
            ]
        )
    )
)
```

### Step 5: Verify the Pipeline

List active rules and test by triggering an event:

```bash
# List event rules via CLI
oci events rule list --compartment-id ocid1.compartment.oc1..example --all

# Check ONS subscription confirmation status
oci ons subscription list --compartment-id ocid1.compartment.oc1..example --topic-id <topic-ocid>
```

## Output

Successful completion produces:
- An ONS topic with at least one confirmed subscription (email, HTTPS, or PagerDuty)
- One or more Events rules with condition filters matching target event types
- Verified event delivery — triggering a matched action (e.g., stopping an instance) delivers a notification to the subscribed endpoint

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| NotAuthenticated | 401 | Bad config or API key | Verify `~/.oci/config` credentials and key_file path |
| NotAuthorizedOrNotFound | 404 | Missing IAM policy or wrong OCID | Add `manage cloudevents-rules` / `manage ons-topics` policies |
| TooManyRequests | 429 | Rate limited (no Retry-After header) | Back off exponentially; see `oraclecloud-rate-limits` |
| InvalidParameter | 400 | Malformed condition JSON in rule | Validate JSON syntax — condition must be valid JSON, not HCL |
| TopicLimitReached | 400 | ONS topic limit (max 100 per compartment) | Delete unused topics or request a limit increase |
| InternalError | 500 | OCI service error | Retry after 30 seconds; check https://ocistatus.oraclecloud.com |
| SubscriptionPending | — | HTTPS endpoint did not confirm | Check endpoint logs — OCI sends a confirmation POST that must return 200 |

## Examples

**Quick event rule via CLI:**

```bash
# Create a rule that fires on all audit events in a compartment
oci events rule create \
  --compartment-id ocid1.compartment.oc1..example \
  --display-name "audit-all" \
  --is-enabled true \
  --condition '{"eventType":["com.oraclecloud.audit.event"]}' \
  --actions '{"actions":[{"actionType":"ONS","topicId":"ocid1.onstopic.oc1.iad.example","isEnabled":true}]}'
```

**List all event types available:**

```python
import oci

config = oci.config.from_file("~/.oci/config")
events_client = oci.events.EventsClient(config)

# Event types are documented — no list API exists.
# Reference: https://docs.oracle.com/en-us/iaas/Content/Events/Reference/eventsproducers.htm
```

## Resources

- [OCI Events Service](https://docs.oracle.com/en-us/iaas/Content/Events/Concepts/eventsoverview.htm) — event rules and conditions
- [OCI Notification Service (ONS)](https://docs.oracle.com/en-us/iaas/Content/Notification/Concepts/notificationoverview.htm) — topics and subscriptions
- [Event Types Reference](https://docs.oracle.com/en-us/iaas/Content/Events/Reference/eventsproducers.htm) — all available event types
- [Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — EventsClient, NotificationDataPlaneClient
- [OCI Status](https://ocistatus.oraclecloud.com) — service health dashboard

## Next Steps

After event pipelines are running, see `oraclecloud-observability` for monitoring event delivery metrics, or `oraclecloud-rate-limits` for handling 429 errors in high-volume event processing.
