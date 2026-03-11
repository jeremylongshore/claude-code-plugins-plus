---
name: documenso-hello-world
description: |
  Create a minimal working Documenso example.
  Use when starting a new Documenso integration, testing your setup,
  or learning basic document signing patterns.
  Trigger with phrases like "documenso hello world", "documenso example",
  "documenso quick start", "simple documenso code", "first document".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Documenso Hello World

## Overview
Minimal working example demonstrating core Documenso document signing functionality.

## Prerequisites
- Completed `documenso-install-auth` setup
- Valid API credentials configured
- A PDF file to upload (or use built-in test)

## Instructions

### Step 1: Create Entry File

Create a new file `documenso-hello.ts` (or `.py` for Python).

### Step 2: Create Your First Document

**TypeScript:**
### Step 3: Upload PDF and Add Recipient

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

**TypeScript (Complete Example):**
### Python Example

## Output
- Working code file with Documenso client initialization
- Created document in Documenso dashboard
- Recipient added with signature field
- Email sent to recipient for signing
- Console output showing:
## Field Types Available

| Type | Description |
|------|-------------|
| `SIGNATURE` | Electronic signature |
| `INITIALS` | Initials field |
| `NAME` | Full name |
| `EMAIL` | Email address |
| `DATE` | Date field |
| `TEXT` | Free text input |
| `NUMBER` | Number input |
| `CHECKBOX` | Checkbox/Boolean |
| `DROPDOWN` | Dropdown selection |
| `RADIO` | Radio button group |

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Import Error | SDK not installed | Verify with `npm list @documenso/sdk-typescript` |
| Auth Error | Invalid credentials | Check environment variable is set |
| File Not Found | PDF path incorrect | Verify PDF file exists |
| Invalid Field Position | Coordinates off page | Check page dimensions |
| Recipient Exists | Duplicate email | Use existing recipient or update |

## Resources
- [Documenso Getting Started](https://docs.documenso.com/developers)
- [API Reference](https://openapi.documenso.com/)
- [Document Operations](https://github.com/documenso/sdk-typescript/blob/main/docs/sdks/documents/README.md)

## Next Steps
Proceed to `documenso-local-dev-loop` for development workflow setup.

## Examples

**Basic usage**: Apply documenso hello world to a standard project setup with default configuration options.

**Advanced scenario**: Customize documenso hello world for production environments with multiple constraints and team-specific requirements.