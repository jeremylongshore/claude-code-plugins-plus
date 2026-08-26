---
name: apple-notes-reference-architecture
description: 'Reference architecture for Apple Notes automation systems.

  Trigger: "apple notes architecture".

  '
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- macos
- apple-notes
- automation
compatibility: Designed for Claude Code
---
# Apple Notes Reference Architecture

## Overview

Apple Notes automation systems are fundamentally different from cloud SaaS integrations. There is no REST API, no server-side SDK, and no webhook infrastructure. Everything runs locally on macOS through the Apple Events IPC bridge. This reference architecture defines the standard layered approach: a Node.js application layer that calls JXA scripts via `osascript`, a local SQLite cache for fast queries, a change detection poller for event-driven workflows, and optional Shortcuts integration for cross-app automation.

## Prerequisites

- An owned interactive macOS host, exact client TCC consent, and a declared account/folder scope.
- A reviewed local-only service boundary, encrypted data stores, and an incident/rollback owner.
- Mocked tests for all application logic; device integration tests run only on a protected self-hosted Mac.

## Instructions

1. Place authorization, input validation, idempotency, and audit logging above the JXA adapter; the adapter should receive only validated scoped commands.
2. Bind any local service to loopback by default and require an authenticated, approved transport for remote administration.
3. Treat cache and event data as sensitive replicas: minimize fields, encrypt at rest, restrict access, rotate/delete under policy, and never read NoteStore directly.
4. Separate liveness from readiness; pause mutations when authorization, reconciliation, or sync health is uncertain.

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    macOS Machine                      │
│                                                       │
│  ┌──────────┐   ┌───────────┐   ┌────────────────┐  │
│  │ Your App │──▶│ osascript  │──▶│   Notes.app    │  │
│  │ (Node.js)│   │  (JXA)    │   │  (local DB)    │  │
│  └────┬─────┘   └───────────┘   └───────┬────────┘  │
│       │                                   │           │
│  ┌────▼─────┐   ┌───────────┐   ┌───────▼────────┐  │
│  │ SQLite   │   │ Shortcuts │   │  iCloud Sync   │  │
│  │ Cache    │   │ Automations│   │ (bird/cloudd)  │  │
│  └──────────┘   └───────────┘   └────────────────┘  │
│       │                                   │           │
│  ┌────▼─────┐                    ┌────────▼───────┐  │
│  │ Poller / │                    │  Other Apple   │  │
│  │ FSEvents │                    │  Devices       │  │
│  └──────────┘                    └────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Project Structure

```
apple-notes-automation/
├── src/
│   ├── notes-client.ts        # JXA wrapper class (osascript calls)
│   ├── cache.ts               # SQLite cache layer
│   ├── templates/             # Note templates (HTML fragments)
│   ├── export/                # Export to MD/JSON/SQLite/CSV
│   ├── events/                # Change detection via polling
│   └── server.ts              # Optional: local HTTP API for remote access
├── scripts/
│   ├── notes-cli.sh           # CLI wrapper for common operations
│   ├── health-check.sh        # Monitoring and alerting
│   ├── export-all.sh          # Full backup export
│   └── install.sh             # launchd deployment installer
├── tests/
│   ├── mocks/                 # Mock JXA client for CI (non-macOS)
│   └── unit/                  # Unit tests (vitest)
├── config/
│   ├── environments.json      # Account/folder per environment
│   └── launchd.plist          # Service definition template
└── package.json
```

## Component Design

```typescript
// src/notes-client.ts — Core abstraction over osascript
import { execSync } from "child_process";

export class NotesClient {
  private account: string;

  constructor(account = "iCloud") { this.account = account; }

  private exec(jxa: string): string {
    return execSync(`osascript -l JavaScript -e '${jxa.replace(/'/g, "'\\''")}'`,
      { encoding: "utf8", timeout: 30000 }).trim();
  }

  count(): number {
    return parseInt(this.exec(`Application("Notes").accounts().find(a => a.name() === "${this.account}").notes.length`));
  }

  list(): Array<{ id: string; title: string; modified: string }> {
    return JSON.parse(this.exec(`
      JSON.stringify(Application("Notes").accounts().find(a => a.name() === "${this.account}")
        .notes().map(n => ({id: n.id(), title: n.name(), modified: n.modificationDate().toISOString()})))
    `));
  }

  create(title: string, body: string, folder = "Notes"): string {
    return this.exec(`
      const Notes = Application("Notes");
      const acct = Notes.accounts().find(a => a.name() === "${this.account}");
      const f = acct.folders().find(f => f.name() === "${folder}") || acct.folders[0];
      const n = Notes.Note({name: "${title}", body: "${body}"});
      f.notes.push(n); n.id();
    `);
  }
}
```

## Key Constraints

| Constraint | Impact | Workaround |
|-----------|--------|------------|
| macOS only | No Linux/Windows servers | Run on Mac; export data for cross-platform consumption |
| No REST API | Cannot access remotely | Optional: expose local HTTP server; lock down to localhost |
| iCloud sync lag | Writes may take 5-30s to appear on other devices | Poll with delay; verify on target device |
| No webhooks | Cannot receive push notifications | Poll for changes every 60s; watch FSEvents on Notes DB |
| HTML-only body | No native Markdown support | Convert HTML to/from Markdown in export/import layer |
| No attachment export via JXA | Binary data inaccessible from scripting | Use Shortcuts for attachment extraction |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Architecture requires macOS server | No cloud-native option | Dedicate a Mac mini as automation server; use Tailscale for remote access |
| Local HTTP API exposed to network | Security risk if not locked down | Bind to 127.0.0.1 only; use SSH tunnel for remote access |
| Cache out of sync with Notes | Polling interval too long | Reduce poll interval; use FSEvents on NoteStore.sqlite for faster detection |
| Template HTML rejected by Notes | Invalid HTML tags | Test templates with a canary note before bulk creation |

## Output

The architecture decision record identifies host ownership, scope, authorization layer, protected data stores, event/reconciliation flow, deployment version, and rollback path. It explicitly states which components are mock-tested versus device-tested and excludes hard-coded account identifiers or note data.

## Examples

Run a Node service on the owned Mac with a loopback-only admin endpoint, a configuration-resolved test folder, and an encrypted metadata-only cache. The worker records an idempotency key before a mutation, validates the scoped result, and pauses its queue if readiness fails; it never exposes a general remote API to Notes.app.

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Cookbook](https://github.com/JXA-Cookbook/JXA-Cookbook)
- [macOS Security Architecture](https://support.apple.com/guide/security/welcome/web)

## Next Steps

For deploying this architecture as a service, see `apple-notes-deploy-integration`. For monitoring the running system, see `apple-notes-observability`.
