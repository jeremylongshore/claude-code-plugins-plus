---
name: clay-policy-guardrails
description: |
  Implement Clay lint rules, policy enforcement, and automated guardrails.
  Use when setting up code quality rules for Clay integrations, implementing
  pre-commit hooks, or configuring CI policy checks for Clay best practices.
  Trigger with phrases like "clay policy", "clay lint",
  "clay guardrails", "clay best practices check", "clay eslint".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clay Policy Guardrails

## Overview
Policy enforcement and guardrails for Clay data enrichment pipelines. Clay processes personal and business data at scale, requiring strict controls around data handling, credit spending, and compliance with data privacy regulations.

## Prerequisites
- Clay API access with admin permissions
- Understanding of data privacy regulations (GDPR, CCPA)
- Credit monitoring infrastructure

## Instructions

### Step 1: Enforce Credit Spending Limits

Prevent runaway enrichment costs with per-user and per-table spending caps.

```python
class CreditPolicy:
    LIMITS = {
        "per_table_max": 10000,  # 10000: 10 seconds in ms
        "per_user_daily": 5000,  # 5000: 5 seconds in ms
        "per_enrichment_column": 2000,  # 2000: 2 seconds in ms
        "alert_threshold_pct": 80
    }

    def check_table_budget(self, table_id: str, rows_to_process: int, credits_per_row: int):
        estimated = rows_to_process * credits_per_row
        used = self.get_table_usage(table_id)
        if used + estimated > self.LIMITS["per_table_max"]:
            raise PolicyViolation(
                f"Table {table_id} would exceed credit limit: "
                f"{used} used + {estimated} requested > {self.LIMITS['per_table_max']}"
            )
        if (used + estimated) / self.LIMITS["per_table_max"] > self.LIMITS["alert_threshold_pct"] / 100:
            self.alert(f"Table {table_id} at {((used + estimated) / self.LIMITS['per_table_max']) * 100:.0f}% of budget")
```

### Step 2: Data Privacy Compliance Filters

Block enrichment of personal data fields that violate privacy policies.

```python
BLOCKED_ENRICHMENT_FIELDS = [
    "ssn", "social_security", "date_of_birth", "dob",
    "home_address", "personal_phone", "personal_email",
    "medical_history", "financial_records"
]

def validate_enrichment_request(columns_to_enrich: list[str]) -> list[str]:
    violations = []
    for col in columns_to_enrich:
        col_lower = col.lower().replace(" ", "_")
        if any(blocked in col_lower for blocked in BLOCKED_ENRICHMENT_FIELDS):
            violations.append(f"Blocked field: {col} (privacy policy)")
    if violations:
        raise PolicyViolation(f"Data privacy violations: {violations}")
    return columns_to_enrich
```

### Step 3: Row-Level Data Validation Before Enrichment

Pre-validate input data to prevent wasting credits on invalid rows.

```python
import re

def validate_rows_for_enrichment(rows: list[dict], enrichment_type: str) -> tuple[list, list]:
    valid, rejected = [], []
    for row in rows:
        if enrichment_type == "email_enrichment":
            email = row.get("email", "")
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                rejected.append({"row": row, "reason": "invalid email format"})
                continue
        elif enrichment_type == "company_enrichment":
            domain = row.get("domain", "")
            if not domain or len(domain) < 4:
                rejected.append({"row": row, "reason": "missing or invalid domain"})
                continue
        valid.append(row)
    return valid, rejected
```

### Step 4: Export and Retention Policies

Control how enriched data can be exported and how long it is retained.

```python
class DataRetentionPolicy:
    RETENTION_DAYS = {
        "enrichment_results": 90,
        "raw_input_data": 30,
        "export_logs": 365  # 365 days = 1 year
    }

    def enforce_retention(self, table_id: str):
        for data_type, max_days in self.RETENTION_DAYS.items():
            cutoff = datetime.now() - timedelta(days=max_days)
            deleted = self.delete_older_than(table_id, data_type, cutoff)
            if deleted > 0:
                self.log_retention_action(table_id, data_type, deleted)

    def validate_export(self, table_id: str, export_format: str, destination: str):
        allowed_formats = ["csv", "json"]
        if export_format not in allowed_formats:
            raise PolicyViolation(f"Export format {export_format} not allowed")
        if "personal" in self.get_table_tags(table_id):
            raise PolicyViolation("Tables tagged 'personal' cannot be exported")
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Credit overrun | No spending limits | Implement per-table and per-user caps |
| Privacy violation | Enriching PII fields | Block sensitive field enrichment |
| Wasted credits | Invalid input rows | Pre-validate before enrichment |
| Data retention breach | No cleanup policy | Automate retention enforcement |

## Examples

### Policy Check Before Enrichment
```python
policy = CreditPolicy()
valid_rows, rejected = validate_rows_for_enrichment(rows, "email_enrichment")
policy.check_table_budget(table_id, len(valid_rows), credits_per_row=2)
# Proceed only after all checks pass
```

## Resources
- [Clay Security](https://docs.clay.com/security)
- [GDPR Compliance](https://gdpr.eu)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale