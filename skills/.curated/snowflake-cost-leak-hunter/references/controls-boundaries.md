# Cost-control boundaries

Use this reference only when the user asks what control might address an observed cost
condition. The skill remains advisory and read-only.

Primary sources:

- [Working with resource monitors](https://docs.snowflake.com/en/user-guide/resource-monitors)
- [Controlling cost](https://docs.snowflake.com/en/user-guide/cost-controlling)

## Resource monitors

Resource monitors govern user-managed virtual warehouses. They can notify and can be
configured to suspend standard warehouses or disable Adaptive Warehouses when a quota
threshold is reached.

Important boundaries:

- They do not track or control serverless-feature or AI-service spend.
- Warehouse-level monitors cannot suspend cloud-services usage.
- Cloud-services credits used for monitor thresholds are not the same as the daily
  billing adjustment.
- Threshold enforcement is not a precise hard cap; consumption can continue while a
  suspension action takes effect or a running query completes.
- `SUSPEND_IMMEDIATE` can cancel executing work.
- Notifications require explicit setup.
- A monitor without an account or warehouse assignment is dormant.
- Each warehouse can be assigned to only one warehouse monitor.
- Creating an account-level monitor and some management operations require elevated
  administrative authority.

Because of these effects, this skill never creates, alters, assigns, suspends, enables,
or disables a monitor.

## Budgets

Snowflake budgets cover supported compute categories including supported serverless
features and provide projected-spend notifications. They are the relevant control
family when the evidence includes serverless usage that a resource monitor cannot
cover.

Do not assume every object or service is supported. Verify current budget coverage,
privileges, notification integration, and account/edition behavior before proposing a
specific configuration.

## Review-packet shape

For a proposed control, record:

```text
observed condition
evidence window and freshness
covered usage categories
explicitly uncovered categories
notification recipients/integration owner
effect of threshold action on running work
approval owner
staging or observation-only period
verification query
rollback command, written but not executed
```

Do not select a quota or threshold from a generic percentage. Derive it from the
customer's approved budget, workload history, and service objective. If those inputs are
absent, request them.

## Safe recommendations

Allowed output:

- “Observe this warehouse with notifications only for an approved period.”
- “Evaluate a budget because this category is serverless and outside resource-monitor
  coverage.”
- “Ask the workload owner whether the measured unattributed compute is intentional warm
  capacity.”
- “Prepare an `ALTER` statement for review after the owner supplies a quota and impact
  tolerance.”

Disallowed action:

- running the `ALTER` statement;
- inventing a threshold, price, or savings figure;
- using `ACCOUNTADMIN` merely for convenience;
- suspending a warehouse during the audit;
- claiming the monitor will enforce an exact invoice cap.
