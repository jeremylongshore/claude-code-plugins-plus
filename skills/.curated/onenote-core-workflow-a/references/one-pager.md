# OneNote Core Workflow A — One-Pager

## The Problem

OneNote's hierarchy (Notebook, Section Group, Section, Page) maps to Graph API endpoints, but the implementation has two major pitfalls: (1) section groups created via API can nest deeper than the desktop app can render, causing invisible content, and (2) page content must be strict XHTML with specific `data-tag` attributes — but the HTML you get back from the API differs from what you sent in, with injected `data-id` attributes and rewritten image URLs.

## The Solution

A complete CRUD lifecycle covering every level of the OneNote hierarchy — create, read, update, and delete for notebooks, section groups, sections, and pages. Includes production-tested XHTML templates, multipart image upload, the JSON-based PATCH update pattern, and explicit warnings about section group nesting limits and input/output HTML differences.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Developers building notebook management, note-taking integrations, or document automation on Microsoft 365 |
| **What** | Full CRUD operations across the entire OneNote hierarchy with XHTML content management |
| **When** | Building any feature that creates, reads, updates, or deletes OneNote content programmatically |
| **Where** | Microsoft Graph API v1.0 `/me/onenote/` endpoints with delegated authentication |
| **Why** | Section group rendering inconsistencies and XHTML schema requirements cause silent failures in production |

## Key Differentiators

- Documents the section group nesting depth limit that desktop apps cannot render beyond two levels
- Explains the critical difference between input HTML and output HTML (Graph-injected `data-id` attributes)
- Provides both TypeScript and Python SDK examples with real authentication setup
- Covers the JSON `target`/`action`/`content` PATCH pattern that most tutorials skip

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated — app-only deprecated March 2025) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity |
