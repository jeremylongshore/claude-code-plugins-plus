# OneNote Install & Auth — One-Pager

## The Problem

App-only authentication (ClientSecretCredential) was deprecated for OneNote Graph APIs on March 31, 2025, breaking every unattended OneNote integration. The migration path requires Azure AD app registration with delegated auth, correct MSAL credential types, and precise permission scopes. One wrong scope means 403 Forbidden on every call — with an error message that does not mention the deprecation.

## The Solution

A complete setup guide for OneNote Graph API authentication using delegated credentials (DeviceCodeCredential). Covers Azure AD app registration, SDK installation for both Python and TypeScript, permission scope selection, token caching for persistent sessions, and multi-tenant configuration. Includes migration path from deprecated app-only auth.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Developers building OneNote integrations, teams migrating from app-only auth |
| **What** | End-to-end auth setup: Azure AD registration, SDK install, delegated credential configuration, token caching |
| **When** | Starting a new OneNote integration or after receiving 403 errors post-March 2025 deprecation |
| **Where** | Azure Portal for app registration, local dev environment for SDK setup |
| **Why** | App-only auth deprecation broke all existing patterns — delegated auth is now mandatory |

## Key Differentiators

- Explicit deprecation warning with before/after code migration examples
- Both Python and TypeScript working code with correct import paths
- Token caching setup so users do not re-authenticate on every run
- Permission scope decision table (Notes.Read vs Notes.ReadWrite vs Notes.ReadWrite.All)

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated — DeviceCodeCredential) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity + @azure/msal-node |
