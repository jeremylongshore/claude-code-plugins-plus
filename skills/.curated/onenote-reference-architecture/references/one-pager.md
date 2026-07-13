# OneNote Reference Architecture — One-Pager

## The Problem

OneNote notebooks exist in three completely separate storage backends — personal OneDrive, SharePoint document libraries, and Microsoft 365 Group sites — each accessed through different Graph API paths (`/me/onenote`, `/sites/{id}/onenote`, `/groups/{id}/onenote`). A call to `/me/onenote/notebooks` silently returns zero results for SharePoint or Group notebooks, leading developers to conclude the API is broken when notebooks simply live elsewhere. Each location also requires different permission scopes: personal needs only `Notes.ReadWrite`, SharePoint adds `Sites.Read.All`, and Groups add `Group.Read.All`. The object hierarchy has its own trap: the API supports deeply nested section groups that the desktop client cannot render, creating invisible data.

## The Solution

This skill provides a complete architectural map of all three notebook locations with their API paths, required permissions, and behavioral differences. It includes a reusable TypeScript service abstraction that normalizes all three locations behind a single interface, a notebook discovery function that searches across all locations, a decision matrix for choosing the right API path per use case, and explicit warnings about section group nesting limits and XHTML content requirements.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Integration architects, full-stack developers, and M365 platform engineers |
| **What** | Unified API path mapping across personal, SharePoint, and Group OneNote notebooks |
| **When** | During initial architecture design, when notebooks "disappear" in API calls, or when expanding from personal to organizational notebooks |
| **Where** | Graph API paths, Azure AD permission configuration, client-side service layer |
| **Why** | Three different API paths with different permissions cause silent empty results; section group nesting creates invisible data in desktop apps |

## Key Differentiators

- Maps all three notebook locations side-by-side with exact API paths, permissions, and storage backends
- Provides a copy-paste TypeScript service abstraction that normalizes location differences
- Documents the section group nesting trap that creates data invisible to desktop users
- Includes a multi-tenant discovery function that searches all three locations in parallel

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity |
| Personal Path | `/me/onenote` |
| SharePoint Path | `/sites/{site-id}/onenote` |
| Group Path | `/groups/{group-id}/onenote` |
