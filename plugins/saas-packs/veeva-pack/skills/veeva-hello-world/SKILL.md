---
name: veeva-hello-world
description: |
  Veeva Vault hello world with REST API and VQL.
  Use when integrating with Veeva Vault for life sciences document management.
  Trigger: "veeva hello world".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, life-sciences, crm, veeva]
compatible-with: claude-code
---

# Veeva Vault Hello World

## Overview

Create, retrieve, and query documents in Veeva Vault -- the fundamental CRUD operations. Uses the Vault REST API with VQL (Vault Query Language) for data retrieval.

## Instructions

### Step 1: Query Documents with VQL

```python
import requests, os

vault_url = "https://myvault.veevavault.com/api/v24.1"
headers = {"Authorization": session_id}

# VQL is SQL-like but Vault-specific
query = "SELECT id, name__v, type__v, status__v, created_date__v FROM documents LIMIT 10"
response = requests.post(f"{vault_url}/query", headers=headers, data={"q": query})
result = response.json()

for doc in result.get("data", []):
    print(f"{doc['name__v']} | Type: {doc['type__v']} | Status: {doc['status__v']}")
```

### Step 2: Retrieve a Document

```python
doc_id = 123
response = requests.get(f"{vault_url}/objects/documents/{doc_id}", headers=headers)
doc = response.json()
print(f"Document: {doc['document']['name__v']}")
print(f"Version: {doc['document']['major_version_number__v']}.{doc['document']['minor_version_number__v']}")
```

### Step 3: Create a Document

```python
# Create document metadata
doc_data = {
    "name__v": "Protocol Amendment 001",
    "type__v": "Trial Document",
    "subtype__v": "Protocol",
    "lifecycle__v": "General Lifecycle",
}
response = requests.post(f"{vault_url}/objects/documents", headers=headers, data=doc_data)
new_id = response.json()["id"]
print(f"Created document: {new_id}")
```

### Step 4: Upload Document File

```python
with open("protocol.pdf", "rb") as f:
    response = requests.post(
        f"{vault_url}/objects/documents/{new_id}/file",
        headers={**headers, "Content-Type": "application/octet-stream"},
        data=f,
    )
print(f"File uploaded: {response.json()['responseStatus']}")
```

## Output

```
Protocol Amendment 001 | Type: Trial Document | Status: Draft
Document: Protocol Amendment 001
Version: 0.1
Created document: 456
File uploaded: SUCCESS
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `INVALID_DATA` in VQL | Wrong field name | Check object metadata |
| `PARAMETER_REQUIRED` | Missing required field | Add type__v, lifecycle__v |
| `OPERATION_NOT_ALLOWED` | Wrong document state | Check lifecycle state |

## Resources

- [Document API](https://developer.veevavault.com/api/24.1/#documents)
- [VQL Reference](https://developer.veevavault.com/vql/)

## Next Steps

Proceed to `veeva-local-dev-loop` for development workflow.
