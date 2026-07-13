# OneNote Hello World — One-Pager

## The Problem

Your first OneNote page creation fails because the Graph API requires strict UTF-8 XHTML, not regular HTML. Missing closing tags (`<br>` instead of `<br />`), unsupported attributes (`rowspan`, `colspan`), or non-UTF-8 encoding cause silent content corruption — the API returns 200 OK but the page renders with missing or garbled content. The output HTML from `GET /pages/{id}/content` also differs from input HTML, confusing developers who expect round-trip fidelity.

## The Solution

A step-by-step first integration that creates a notebook, section, and page with correct XHTML. Includes a side-by-side comparison of valid vs invalid HTML, a `data-tag` reference for checklists, and demonstrates input vs output HTML differences. Both TypeScript and Python examples provided.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Developers starting their first OneNote Graph API integration |
| **What** | Create notebook + section + page with valid XHTML, read back content |
| **When** | First integration attempt, or when pages render incorrectly |
| **Where** | Graph API v1.0 — `/me/onenote/notebooks`, `/sections`, `/pages` endpoints |
| **Why** | XHTML requirements are undocumented in most tutorials, causing silent failures |

## Key Differentiators

- Side-by-side valid vs invalid XHTML with specific failure modes for each mistake
- Demonstrates that output HTML differs from input HTML (prevents confusion)
- Complete data-tag reference table for checkboxes, stars, highlights
- Working code in both TypeScript and Python — not pseudocode

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity |
