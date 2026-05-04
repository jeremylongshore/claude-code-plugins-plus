# Fingerprint Specification

Structural state schema for `${CLAUDE_PLUGIN_DATA}/arch-state.json`. Written by generate/diff, read by diff/watch.

## Table of Contents

- [File Location](#file-location)
- [Schema (JSON)](#schema-json)
- [Stable Hash Algorithm](#stable-hash-algorithm)
- [Graph Fingerprint](#graph-fingerprint)
- [Diff Algorithm](#diff-algorithm)
- [Schema Versioning](#schema-versioning)

## File Location

Fallback chain (first writable wins):

1. `${CLAUDE_PLUGIN_DATA}/arch-state.json` (preferred — plugin-managed state dir, survives updates)
2. `${XDG_STATE_HOME}/claude/arch/arch-state.json`
3. `~/.claude-state/arch/arch-state.json` (final fallback — auto-created)

One state file per active workspace, keyed by `repo.root` in the document.

## Schema (JSON)

```json
{
  "schema_version": "1",
  "generated_at": "2026-04-19T14:05:11Z",
  "repo": {
    "root": "/home/jeremy/000-projects/my-app",
    "git_sha": "a1b2c3d4",
    "branch": "main",
    "remote": "git@github.com:org/repo.git"
  },
  "nodes": [
    {
      "id": "api",
      "label": "API Service",
      "role": "backend",
      "source": "docker-compose.yml:services.api",
      "tech": ["node", "express"],
      "ports": [3000],
      "stable_hash": "sha256:7f3a...e2"
    }
  ],
  "edges": [
    {
      "from": "web",
      "to": "api",
      "kind": "http",
      "label": "/v1/*",
      "source": "web/src/lib/api-client.ts:12",
      "stable_hash": "sha256:4c9d...11"
    }
  ],
  "groups": [
    {
      "id": "vpc-prod",
      "label": "Production VPC",
      "kind": "region",
      "members": ["api", "db", "cache"]
    }
  ],
  "annotations": [
    {
      "node_id": "payment-service",
      "kind": "git-blame",
      "text": "added in v4.2 by @alice (2025-11-03)",
      "source": "git log --diff-filter=A --follow"
    }
  ],
  "tech_inventory": {
    "package_managers": ["npm", "pip"],
    "orchestrators": ["docker-compose"],
    "iac": [],
    "cloud_providers_detected": []
  },
  "graph_fingerprint": "sha256:9b8a...cd"
}
```

### Node fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | Unique within graph; kebab-case |
| `label` | string | yes | Display name |
| `role` | enum | yes | One of: `frontend`, `backend`, `database`, `cloud`, `security`, `message-bus`, `external` |
| `source` | string | yes | `file:line` citation for where this node was inferred from |
| `tech` | string[] | no | Tags like `["node", "express"]`, `["python", "fastapi"]` |
| `ports` | number[] | no | Exposed ports |
| `stable_hash` | string | yes | `sha256(role + label + sorted-neighbors)` — identity preserved across position changes |

### Edge fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `from` | string | yes | Source node id |
| `to` | string | yes | Destination node id |
| `kind` | enum | yes | `http`, `grpc`, `queue`, `db`, `import`, `fs`, `auth`, `unknown` |
| `label` | string | no | Edge annotation (route, protocol) |
| `source` | string | yes | `file:line` citation |
| `stable_hash` | string | yes | `sha256(from + to + kind)` |

## Stable Hash Algorithm

Per-element hash preserves identity when a node shifts position or a label is cosmetic-only.

```python
def node_stable_hash(node, neighbor_ids):
    canonical = f"{node['role']}|{node['label']}|{'|'.join(sorted(neighbor_ids))}"
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()

def edge_stable_hash(edge):
    canonical = f"{edge['from']}|{edge['to']}|{edge['kind']}"
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
```

Rename a node label (e.g., "API Service" → "Core API") → hash changes → treated as a change, not add+remove.

Change a node's neighbors → hash changes → surfaces as a `changed` node in diff output.

## Graph Fingerprint

A single rollup hash of the sorted set of all stable_hash values. Lets watch mode answer "did anything change?" in O(1) without a full diff.

```python
def graph_fingerprint(nodes, edges):
    all_hashes = sorted([n["stable_hash"] for n in nodes] + [e["stable_hash"] for e in edges])
    return "sha256:" + hashlib.sha256("".join(all_hashes).encode()).hexdigest()
```

## Diff Algorithm

Given `old_state` and `new_state`:

1. **Added nodes** = `{n in new_state.nodes where n.id not in old_state.nodes}`
2. **Removed nodes** = `{n in old_state.nodes where n.id not in new_state.nodes}`
3. **Changed nodes** = `{n where n.id exists in both but n.stable_hash differs}`
4. **Added edges** = `{e in new_state.edges where e.stable_hash not in old_state.edges.stable_hashes}`
5. **Removed edges** = symmetric
6. **Changed edges** = edges with matching `from|to` but different `kind` or `label`

Return four lists + the new fingerprint.

## Schema Versioning

`schema_version` is a **string** so bumps are non-destructive. Rules:

- `fingerprint.py` **refuses** to diff across schema versions — emits "baseline restart required" instead.
- Migration: when `schema_version` changes, next run writes a fresh state and archives the prior one to `arch-state.json.v<old>.bak`.
- Policy: bump `schema_version` whenever adding a required field or changing a field's semantics.

Current version: **`"1"`**.
