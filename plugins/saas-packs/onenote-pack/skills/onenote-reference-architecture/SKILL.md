---
name: onenote-reference-architecture
description: 'Reference architecture for OneNote integrations covering all notebook
  locations and API path patterns.

  Use when designing multi-tenant OneNote integrations or choosing between personal,
  SharePoint, and group notebook APIs.

  Trigger with "onenote architecture", "onenote api paths", "onenote sharepoint vs
  personal".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- onenote
- microsoft
compatibility: Designed for Claude Code
---
# OneNote Reference Architecture

## Overview

OneNote notebooks live in three completely different storage backends — personal OneDrive, SharePoint team sites, and Microsoft 365 Groups — each with its own Graph API path, permission model, and behavioral quirks. Building an integration that "just works with OneNote" means handling all three locations, because users do not know (or care) where their notebook is stored. The API path `/me/onenote/notebooks` only returns personal notebooks; SharePoint and Group notebooks require different endpoints entirely. This skill maps the full architecture: storage locations, API paths, the object hierarchy (and its gotchas), and a service abstraction layer that normalizes all three locations into a single interface.

## Prerequisites

- Azure AD app registration with delegated permissions (`Notes.ReadWrite` minimum)
- Familiarity with Microsoft Graph API URL structure (`https://graph.microsoft.com/v1.0`)
- For SharePoint notebooks: `Sites.Read.All` or `Sites.ReadWrite.All` permission
- For Group notebooks: `Group.Read.All` or `Group.ReadWrite.All` permission
- Python: `pip install msgraph-sdk azure-identity` or Node: `npm install @microsoft/microsoft-graph-client @azure/identity`

## Instructions

### System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Your App   │────>│  MSAL Auth   │────>│  Azure AD       │
│  (Client)   │     │  (Delegated) │     │  Token Service  │
└──────┬──────┘     └──────────────┘     └─────────────────┘
       │
       │ Bearer Token
       v
┌──────────────────────────────────────────────────────────┐
│              Microsoft Graph API (v1.0)                   │
│              https://graph.microsoft.com/v1.0             │
├──────────────┬──────────────────┬────────────────────────┤
│ /me/onenote  │ /sites/{id}/     │ /groups/{id}/          │
│              │  onenote          │  onenote               │
├──────────────┼──────────────────┼────────────────────────┤
│  Personal    │   SharePoint     │   Group                │
│  OneDrive    │   Document Lib   │   Notebook             │
│  Storage     │   Storage        │   Storage              │
└──────────────┴──────────────────┴────────────────────────┘
```

### Three Notebook Locations

**1. Personal Notebooks (OneDrive)**

```
GET https://graph.microsoft.com/v1.0/me/onenote/notebooks
GET https://graph.microsoft.com/v1.0/me/onenote/notebooks/{notebook-id}/sections
GET https://graph.microsoft.com/v1.0/me/onenote/sections/{section-id}/pages
```

- Owned by the signed-in user
- Stored in user's OneDrive root `/Documents/` or `/Notebooks/`
- Permission: `Notes.ReadWrite` (user consent, no admin needed)
- Cannot be shared with external tenants via API

**2. SharePoint Site Notebooks**

```
GET https://graph.microsoft.com/v1.0/sites/{site-id}/onenote/notebooks
GET https://graph.microsoft.com/v1.0/sites/{site-id}/onenote/notebooks/{notebook-id}/sections
GET https://graph.microsoft.com/v1.0/sites/{site-id}/onenote/sections/{section-id}/pages
```

- Owned by the SharePoint site, accessible to site members
- Stored in the site's document library
- Permission: `Notes.ReadWrite` + `Sites.Read.All` (Sites scope often requires admin consent)
- **Gotcha:** You need the site ID, not the site URL. Resolve it first:
  ```
  GET https://graph.microsoft.com/v1.0/sites/{hostname}:/{server-relative-path}
  ```

**3. Group Notebooks (Microsoft 365 Groups / Teams)**

```
GET https://graph.microsoft.com/v1.0/groups/{group-id}/onenote/notebooks
GET https://graph.microsoft.com/v1.0/groups/{group-id}/onenote/notebooks/{notebook-id}/sections
GET https://graph.microsoft.com/v1.0/groups/{group-id}/onenote/sections/{section-id}/pages
```

- Owned by the M365 Group (every Teams team has one)
- Stored in the group's SharePoint site document library
- Permission: `Notes.ReadWrite` + `Group.Read.All`
- Each group has exactly one default notebook (created automatically)

### Object Hierarchy

```
Notebook
├── Section Group (optional nesting)
│   └── Section
│       ├── Page
│       │   └── Content (HTML)
│       └── Page
└── Section
    ├── Page
    │   └── Content (HTML)
    └── Page
```

**Critical gotcha — Section Groups:** The API supports creating nested section groups, but the OneNote desktop and mobile apps cannot render section groups deeper than two levels. If your API creates `Notebook > Group A > Group B > Group C > Section`, desktop users will see a broken hierarchy. Limit nesting to one level of section groups.

**Page content is HTML:** Every page body is returned as XHTML. You must POST valid XHTML when creating pages (all tags self-closed, UTF-8 encoded). The Graph API silently strips invalid HTML rather than rejecting it, so malformed content appears to succeed but renders incorrectly.

### API Path Construction

Build paths dynamically based on notebook location:

```typescript
type NotebookLocation = "personal" | "sharepoint" | "group";

function buildOneNotePath(
  location: NotebookLocation,
  resourceId?: string
): string {
  const base = "https://graph.microsoft.com/v1.0";
  switch (location) {
    case "personal":
      return `${base}/me/onenote`;
    case "sharepoint":
      if (!resourceId) throw new Error("SharePoint requires site-id");
      return `${base}/sites/${resourceId}/onenote`;
    case "group":
      if (!resourceId) throw new Error("Group requires group-id");
      return `${base}/groups/${resourceId}/onenote`;
  }
}

// Usage
const path = buildOneNotePath("sharepoint", "contoso.sharepoint.com,guid1,guid2");
// => https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,guid1,guid2/onenote
```

### Service Layer Abstraction

Normalize all three locations behind a single interface so callers never deal with path differences:

```typescript
import { Client } from "@microsoft/microsoft-graph-client";
import { TokenCredentialAuthenticationProvider }
  from "@microsoft/microsoft-graph-client/authProviders/azureTokenCredentials";
import { DeviceCodeCredential } from "@azure/identity";

interface NotebookTarget {
  location: "personal" | "sharepoint" | "group";
  resourceId?: string;  // site-id or group-id
}

class OneNoteService {
  private client: Client;

  constructor(clientId: string, tenantId: string) {
    const credential = new DeviceCodeCredential({ clientId, tenantId });
    const authProvider = new TokenCredentialAuthenticationProvider(credential, {
      scopes: ["Notes.ReadWrite"],
    });
    this.client = Client.initWithMiddleware({ authProvider });
  }

  private basePath(target: NotebookTarget): string {
    switch (target.location) {
      case "personal": return "/me/onenote";
      case "sharepoint": return `/sites/${target.resourceId}/onenote`;
      case "group": return `/groups/${target.resourceId}/onenote`;
    }
  }

  async listNotebooks(target: NotebookTarget) {
    return this.client.api(`${this.basePath(target)}/notebooks`).get();
  }

  async listSections(target: NotebookTarget, notebookId: string) {
    return this.client
      .api(`${this.basePath(target)}/notebooks/${notebookId}/sections`)
      .get();
  }

  async listPages(target: NotebookTarget, sectionId: string) {
    return this.client
      .api(`${this.basePath(target)}/sections/${sectionId}/pages`)
      .select("id,title,createdDateTime,lastModifiedDateTime")
      .orderby("lastModifiedDateTime desc")
      .top(50)
      .get();
  }

  async createPage(target: NotebookTarget, sectionId: string, htmlBody: string) {
    return this.client
      .api(`${this.basePath(target)}/sections/${sectionId}/pages`)
      .header("Content-Type", "text/html")
      .post(htmlBody);
  }
}
```

### Decision Matrix: When to Use Which API Path

| Scenario | Path | Why |
|----------|------|-----|
| Personal note-taking app | `/me/onenote` | Simplest auth, user consent only |
| Team knowledge base | `/groups/{id}/onenote` | Shared with all team members automatically |
| Department wiki | `/sites/{id}/onenote` | SharePoint permissions control access granularly |
| Multi-user reporting tool | `/users/{id}/onenote` | Admin consent required; reads other users' notes |
| Cross-org integration | `/sites/{id}/onenote` | SharePoint external sharing supports guest access |

### Multi-Tenant Architecture

For SaaS apps serving multiple M365 tenants:

1. **Register as multi-tenant** in Azure AD (supported account types: "Accounts in any organizational directory")
2. **Store per-tenant metadata**: each tenant needs its own site-ids, group-ids, and token cache
3. **Validate `tid` claim** in every token to prevent cross-tenant data leakage
4. **Discover notebooks across all three locations** since different tenants organize differently:

```python
async def discover_all_notebooks(client, site_ids: list[str], group_ids: list[str]):
    """Find notebooks across all three locations for comprehensive discovery."""
    notebooks = []

    # Personal notebooks
    personal = await client.me.onenote.notebooks.get()
    for nb in (personal.value or []):
        notebooks.append({"location": "personal", "name": nb.display_name, "id": nb.id})

    # SharePoint notebooks
    for site_id in site_ids:
        try:
            site_nbs = await client.sites.by_site_id(site_id).onenote.notebooks.get()
            for nb in (site_nbs.value or []):
                notebooks.append({"location": "sharepoint", "resource": site_id,
                                  "name": nb.display_name, "id": nb.id})
        except Exception:
            pass  # User may not have access to all sites

    # Group notebooks
    for group_id in group_ids:
        try:
            group_nbs = await client.groups.by_group_id(group_id).onenote.notebooks.get()
            for nb in (group_nbs.value or []):
                notebooks.append({"location": "group", "resource": group_id,
                                  "name": nb.display_name, "id": nb.id})
        except Exception:
            pass  # User may not be a group member

    return notebooks
```

## Output

After applying this skill, you will have: a clear mental model of the three notebook storage locations and their API paths, a reusable service abstraction that normalizes all locations into a single interface, correct permission requirements per location, and a decision matrix for choosing the right API path for your use case.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `404 Not Found` on `/sites/{id}/onenote` | Wrong site-id format (must be `hostname,siteGuid,webGuid`) | Resolve site-id with `GET /sites/{hostname}:/{path}` first |
| `403 Forbidden` on group notebooks | Missing `Group.Read.All` permission | Add Group.Read.All scope; may require admin consent |
| `403 Forbidden` on SharePoint notebooks | Missing `Sites.Read.All` permission | Add Sites.Read.All scope; usually requires admin consent |
| Nested section groups invisible in desktop | API allows deep nesting, desktop does not | Limit section groups to one level of nesting |
| `400 Bad Request` creating pages | Invalid XHTML in POST body | Validate HTML: close all tags, encode as UTF-8, wrap in `<html><head><title>T</title></head><body>...</body></html>` |

## Examples

**Resolve a SharePoint site ID from URL:**

```python
# Convert "https://contoso.sharepoint.com/sites/engineering" to a site-id
response = await client.sites.by_site_id(
    "contoso.sharepoint.com:/sites/engineering"
).get()
site_id = response.id  # "contoso.sharepoint.com,guid1,guid2"
```

**List all notebooks a user can access (all locations):**

```bash
# Personal notebooks
curl -H "Authorization: Bearer $TOKEN" \
  "https://graph.microsoft.com/v1.0/me/onenote/notebooks?\$select=id,displayName"

# Group notebooks (replace GROUP_ID)
curl -H "Authorization: Bearer $TOKEN" \
  "https://graph.microsoft.com/v1.0/groups/GROUP_ID/onenote/notebooks?\$select=id,displayName"
```

## Resources

- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [Integration Guide](https://learn.microsoft.com/en-us/graph/integrate-with-onenote)
- [Input/Output HTML](https://learn.microsoft.com/en-us/graph/onenote-input-output-html)
- [Best Practices](https://learn.microsoft.com/en-us/graph/onenote-best-practices)
- [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)
- [Graph API Reference](https://learn.microsoft.com/en-us/graph/api/overview)

## Next Steps

- Apply `onenote-security-basics` for permission scoping and token management
- Use `onenote-cost-tuning` to optimize API call volume across multiple locations
- See `onenote-sdk-patterns` for advanced query patterns with OData filters
