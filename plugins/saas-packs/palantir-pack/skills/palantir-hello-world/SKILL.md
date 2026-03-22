---
name: palantir-hello-world
description: |
  Create a minimal working Palantir Foundry example querying Ontology objects.
  Use when starting a new Foundry integration, testing your setup,
  or learning basic Foundry API and Ontology patterns.
  Trigger with phrases like "palantir hello world", "palantir example",
  "palantir quick start", "foundry first query".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(npm:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, ontology, getting-started]
compatible-with: claude-code, codex, openclaw
---

# Palantir Hello World

## Overview
Build a minimal working example that connects to Palantir Foundry, queries Ontology objects via the REST API, reads a dataset, and applies an action. Uses real `foundry-platform-sdk` Python API calls.

## Prerequisites
- Completed `palantir-install-auth` setup
- Valid bearer token or OAuth2 credentials
- At least one Ontology with object types configured in your Foundry enrollment

## Instructions

### Step 1: List Available Ontologies
```python
import os
import foundry

client = foundry.FoundryClient(
    auth=foundry.UserTokenAuth(
        hostname=os.environ["FOUNDRY_HOSTNAME"],
        token=os.environ["FOUNDRY_TOKEN"],
    ),
    hostname=os.environ["FOUNDRY_HOSTNAME"],
)

# List all ontologies you have access to
for ont in client.ontologies.Ontology.list():
    print(f"Ontology: {ont.api_name}  RID: {ont.rid}")
```

### Step 2: Query Ontology Objects
```python
# List objects of type "Employee" from the default ontology
# The object type api_name comes from your Ontology configuration
ONTOLOGY = "your-ontology-api-name"
OBJECT_TYPE = "Employee"

objects = client.ontologies.OntologyObject.list(
    ontology=ONTOLOGY,
    object_type=OBJECT_TYPE,
    page_size=5,
)

for obj in objects.data:
    props = obj.properties
    print(f"  {props.get('fullName', 'N/A')} — {props.get('department', 'N/A')}")
```

### Step 3: Get a Single Object by Primary Key
```python
employee = client.ontologies.OntologyObject.get(
    ontology=ONTOLOGY,
    object_type=OBJECT_TYPE,
    primary_key="EMP-001",
)
print(f"Found: {employee.properties}")
```

### Step 4: Read a Dataset
```python
# Read rows from a Foundry dataset (tabular)
DATASET_RID = "ri.foundry.main.dataset.xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Get dataset metadata
dataset = client.datasets.Dataset.get(dataset_rid=DATASET_RID)
print(f"Dataset: {dataset.name}, Path: {dataset.path}")

# Read rows from the dataset (CSV format)
content = client.datasets.Dataset.read(
    dataset_rid=DATASET_RID,
    branch_id="master",
    format="arrow",  # or "csv"
)
print(f"Read {len(content)} bytes of data")
```

### Step 5: Apply an Ontology Action
```python
# Actions modify objects — e.g., updating an employee's department
result = client.ontologies.Action.apply(
    ontology=ONTOLOGY,
    action_type="updateDepartment",
    parameters={
        "employeeId": "EMP-001",
        "newDepartment": "Engineering",
    },
)
print(f"Action result: {result.validation}")
```

### Step 6: Run and Verify
```bash
set -euo pipefail
python hello_foundry.py
# Expected output:
# Ontology: my-company  RID: ri.ontology.main.ontology.xxx
# Employee: Jane Doe — Engineering
# Action result: VALID
```

## Output
- Authenticated connection to Palantir Foundry
- Listed ontologies and object types
- Retrieved objects with property values
- Read dataset content
- Applied an action to modify an object

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `ObjectTypeNotFound` | Wrong `api_name` | Check Ontology Manager for exact object type names |
| `ObjectNotFound` | Invalid primary key | Verify the key exists; keys are case-sensitive |
| `ActionValidationFailed` | Missing required params | Check action definition for required parameters |
| `DatasetNotFound` | Wrong RID or no access | Verify RID in Foundry UI; check project permissions |
| `401 Unauthorized` | Token expired | Regenerate in Developer Console |

## Examples

### Using the REST API Directly (curl)
```bash
# List objects via REST
curl -s -H "Authorization: Bearer $FOUNDRY_TOKEN" \
  "https://$FOUNDRY_HOSTNAME/api/v2/ontologies/my-ontology/objects/Employee?pageSize=5" \
  | python -m json.tool
```

### TypeScript OSDK Equivalent
```typescript
import { createClient } from "@osdk/client";
import { Employee } from "@my-app/sdk";  // generated from OSDK

const employees = await client(Employee)
  .where({ department: "Engineering" })
  .fetchPage({ pageSize: 10 });

employees.data.forEach(emp => console.log(emp.fullName));
```

## Resources
- [Foundry API Introduction](https://www.palantir.com/docs/foundry/api/general/overview/introduction)
- [Get Object API](https://www.palantir.com/docs/foundry/api/ontology-resources/objects/get-object)
- [Python SDK PyPI](https://pypi.org/project/foundry-platform-sdk/)
- [Code Examples](https://www.palantir.com/docs/foundry/code-examples/foundry-apis-local-environment)

## Next Steps
- Set up iterative development: `palantir-local-dev-loop`
- Build data pipelines with transforms: `palantir-core-workflow-a`
- Query and link objects: `palantir-core-workflow-b`
