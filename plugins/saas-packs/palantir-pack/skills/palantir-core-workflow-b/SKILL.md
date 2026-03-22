---
name: palantir-core-workflow-b
description: |
  Work with Palantir Foundry Ontology objects, actions, and queries via SDK.
  Use when querying objects, applying actions, linking objects,
  or building Ontology-driven applications.
  Trigger with phrases like "palantir ontology", "foundry objects",
  "palantir actions", "ontology query", "OSDK objects".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(npm:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, ontology, osdk, actions]
compatible-with: claude-code, codex, openclaw
---

# Palantir Core Workflow B — Ontology Objects & Actions

## Overview
Query, filter, and mutate Ontology objects using the Foundry Platform SDK and OSDK. Covers listing objects with property filters, following links between object types, applying actions, and aggregating object data. This is the primary workflow for Ontology-driven applications.

## Prerequisites
- Completed `palantir-install-auth` setup
- An Ontology with configured object types, link types, and actions
- Familiarity with `palantir-core-workflow-a` (data pipelines feed the Ontology)

## Instructions

### Step 1: List and Filter Objects (REST API)
```python
import os, foundry

client = foundry.FoundryClient(
    auth=foundry.UserTokenAuth(
        hostname=os.environ["FOUNDRY_HOSTNAME"],
        token=os.environ["FOUNDRY_TOKEN"],
    ),
    hostname=os.environ["FOUNDRY_HOSTNAME"],
)

ONTOLOGY = "my-company"

# List employees in Engineering, sorted by hire date
result = client.ontologies.OntologyObject.list(
    ontology=ONTOLOGY,
    object_type="Employee",
    page_size=20,
    order_by="hireDate:asc",
    properties={"department": "Engineering"},
)

for obj in result.data:
    p = obj.properties
    print(f"{p['fullName']} | {p['department']} | hired {p['hireDate']}")
```

### Step 2: Search Objects with Filters
```python
# Search with complex filters using the search endpoint
search_result = client.ontologies.OntologyObject.search(
    ontology=ONTOLOGY,
    object_type="Employee",
    where={
        "type": "and",
        "value": [
            {"type": "eq", "field": "department", "value": "Engineering"},
            {"type": "gte", "field": "salary", "value": 100000},
        ],
    },
    page_size=50,
)
print(f"Found {len(search_result.data)} matching employees")
```

### Step 3: Follow Links Between Objects
```python
# Get all projects linked to an employee
employee_rid = "ri.ontology.main.object.employee-001"

linked_projects = client.ontologies.OntologyObject.list_linked_objects(
    ontology=ONTOLOGY,
    object_type="Employee",
    primary_key="EMP-001",
    link_type="assignedProjects",
)

for project in linked_projects.data:
    print(f"  Project: {project.properties['name']} — {project.properties['status']}")
```

### Step 4: Apply Actions to Modify Objects
```python
# Promote an employee — triggers validation rules defined in Ontology
result = client.ontologies.Action.apply(
    ontology=ONTOLOGY,
    action_type="promoteEmployee",
    parameters={
        "employeeId": "EMP-001",
        "newTitle": "Senior Engineer",
        "newSalary": 150000,
        "effectiveDate": "2026-04-01",
    },
)
print(f"Validation: {result.validation}")  # VALID or INVALID with reasons
```

### Step 5: Aggregate Object Data
```python
# Aggregate salary by department
aggregation = client.ontologies.OntologyObject.aggregate(
    ontology=ONTOLOGY,
    object_type="Employee",
    aggregation=[
        {"type": "avg", "name": "avgSalary", "field": "salary"},
        {"type": "count", "name": "headcount"},
    ],
    group_by=[{"field": "department", "type": "exact"}],
)

for bucket in aggregation.data:
    grp = bucket.group
    vals = bucket.metrics
    print(f"{grp['department']}: {vals['headcount']} people, avg ${vals['avgSalary']:,.0f}")
```

### Step 6: TypeScript OSDK (Generated SDK)
```typescript
import { createClient } from "@osdk/client";
import { Employee } from "@my-app/sdk";  // generated types

// Type-safe queries with auto-completion
const engineers = await client(Employee)
  .where({ department: { $eq: "Engineering" } })
  .orderBy(e => e.hireDate.asc())
  .fetchPage({ pageSize: 20 });

for (const emp of engineers.data) {
  console.log(`${emp.fullName} — ${emp.title}`);
}

// Apply action with type-safe parameters
await client(Employee).applyAction("promoteEmployee", {
  employeeId: "EMP-001",
  newTitle: "Senior Engineer",
});
```

## Output
- Filtered and sorted Ontology object queries
- Cross-object navigation via link types
- Action application with validation feedback
- Server-side aggregations grouped by properties

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `ObjectTypeNotFound` | Wrong api_name | Check Ontology Manager for exact type names |
| `PropertyNotFound` | Wrong property name | Properties are camelCase in API, may differ from UI |
| `ActionValidationFailed` | Business rule violation | Read `result.validation.messages` for details |
| `LinkTypeNotFound` | Invalid link type name | Verify link type in Ontology Manager |
| `PermissionDenied` | Missing Ontology scope | Add `api:ontology-read` scope to your app |

## Examples

### Batch Action Application
```python
employee_ids = ["EMP-001", "EMP-002", "EMP-003"]
for eid in employee_ids:
    result = client.ontologies.Action.apply(
        ontology=ONTOLOGY,
        action_type="markReviewed",
        parameters={"employeeId": eid, "reviewDate": "2026-03-22"},
    )
    status = "OK" if result.validation == "VALID" else "FAILED"
    print(f"  {eid}: {status}")
```

## Resources
- [Ontology SDK Overview](https://www.palantir.com/docs/foundry/ontology-sdk/overview)
- [Get Object API](https://www.palantir.com/docs/foundry/api/ontology-resources/objects/get-object)
- [Python OSDK Guide](https://www.palantir.com/docs/foundry/ontology-sdk/python-osdk)
- [Actions API](https://www.palantir.com/docs/foundry/api/ontology-resources/actions/)

## Next Steps
- Handle errors systematically: `palantir-common-errors`
- Optimize query performance: `palantir-performance-tuning`
- Secure object access with RBAC: `palantir-enterprise-rbac`
