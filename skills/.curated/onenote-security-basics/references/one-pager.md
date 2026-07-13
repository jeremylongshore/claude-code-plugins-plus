# OneNote Security Basics — One-Pager

## The Problem

Microsoft deprecated app-only authentication for OneNote Graph API endpoints on March 31, 2025. Integrations that relied on ClientSecretCredential stopped working overnight. The migration to delegated auth introduces new complexity: which of the four Notes.* permission scopes do you actually need? Notes.ReadWrite.All requires tenant admin consent that most developers cannot self-approve. Token caches expire silently after 90 days, and MSAL cache serialization patterns differ between Python and TypeScript with no unified guide. Teams ship OneNote integrations with overly broad permissions because the scope matrix is buried across multiple documentation pages.

## The Solution

This skill provides a complete security implementation guide for post-2025 OneNote integrations: a permission scope decision matrix (4 scopes mapped to exact capabilities), working MSAL token cache serialization code for both Python and TypeScript, secure credential storage patterns using environment variables and Azure Key Vault, multi-tenant token isolation, and a 10-point security checklist for production deployment.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Backend developers, DevOps engineers, and security reviewers working on M365 integrations |
| **What** | Delegated auth setup, least-privilege scoping, MSAL cache persistence, credential rotation |
| **When** | During initial integration setup, security audits, or migrating from deprecated app-only auth |
| **Where** | Azure AD app registrations, MSAL token cache, environment/Key Vault credential stores |
| **Why** | App-only auth deprecated March 2025; over-provisioned scopes create audit failures; expired token caches cause silent 401 loops |

## Key Differentiators

- Covers the March 2025 app-only deprecation explicitly with migration path — most guides still show ClientSecretCredential
- Permission scope matrix maps all 4 Notes.* scopes to exact CRUD capabilities with admin consent requirements
- Working MSAL cache serialization code for both Python and TypeScript with file permission hardening
- Security checklist is OneNote-specific, not a generic OAuth checklist

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated only — app-only deprecated) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity |
| Credential Store | Azure Key Vault or environment variables |
| Token Cache | MSAL SerializableTokenCache (file-backed, 0600 permissions) |
