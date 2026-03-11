---
name: windsurf-webhooks-events
description: |
  Implement Windsurf webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Windsurf event notifications securely.
  Trigger with phrases like "windsurf webhook", "windsurf events",
  "windsurf webhook signature", "handle windsurf events", "windsurf notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Windsurf Webhooks & Events

## Overview
Handle Windsurf workspace and editor events for extension development and team workflow integration. Windsurf, built on VS Code architecture, exposes extension events for workspace changes, editor actions, AI interactions (Cascade), and terminal activity.

## Prerequisites
- Windsurf IDE installed with extension development support
- Node.js and VS Code extension API familiarity
- Understanding of VS Code extension model (activationEvents, commands)
- Windsurf workspace with Cascade AI enabled

## Event Types

| Event | Source | Payload |
|-------|--------|---------|
| `workspace.onDidOpenTextDocument` | VS Code API | Document URI, language |
| `workspace.onDidSaveTextDocument` | VS Code API | File path, content |
| `cascade.onSuggestionAccepted` | Windsurf API | Suggestion text, file, line |
| `cascade.onFlowCompleted` | Windsurf API | Flow ID, changes made |
| `terminal.onDidWriteTerminalData` | VS Code API | Terminal output text |
| `debug.onDidStartDebugSession` | VS Code API | Session config, type |

## Instructions

### Step 1: Create Windsurf Extension
```typescript
import * as vscode from "vscode";

export function activate(context: vscode.ExtensionContext) {
  const saveListener = vscode.workspace.onDidSaveTextDocument(
    async (document) => {
      console.log(`File saved: ${document.uri.fsPath}`);
      await handleFileSave(document);
    }
  );

  const editorListener = vscode.window.onDidChangeActiveTextEditor(
    (editor) => {
      if (editor) {
        trackFileOpen(editor.document);
      }
    }
  );

  const folderListener = vscode.workspace.onDidChangeWorkspaceFolders(
    (event) => {
      for (const added of event.added) {
        console.log(`Folder added: ${added.uri.fsPath}`);
      }
    }
  );

  context.subscriptions.push(saveListener, editorListener, folderListener);
}
```

### Step 2: Track AI Interaction Events
```typescript
async function trackCascadeEvents(context: vscode.ExtensionContext) {
  const outputChannel = vscode.window.createOutputChannel("Cascade Tracker");

  const completionListener = vscode.languages.registerInlineCompletionItemProvider(
    { pattern: "**" },
    {
      provideInlineCompletionItems(document, position) {
        outputChannel.appendLine(
          `Completion requested: ${document.fileName}:${position.line}`
        );
        return [];
      },
    }
  );

  context.subscriptions.push(completionListener);
}
```

### Step 3: Send Events to External System
```typescript
async function handleFileSave(document: vscode.TextDocument) {
  const webhookUrl = vscode.workspace
    .getConfiguration("windsurf-events")
    .get<string>("webhookUrl");

  if (!webhookUrl) return;

  await fetch(webhookUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event: "file.saved",
      file: document.uri.fsPath,
      language: document.languageId,
      lineCount: document.lineCount,
      timestamp: new Date().toISOString(),
    }),
  });
}

function trackFileOpen(document: vscode.TextDocument) {
  const diagnostics = vscode.languages.getDiagnostics(document.uri);
  const errorCount = diagnostics.filter(
    d => d.severity === vscode.DiagnosticSeverity.Error
  ).length;
  console.log(`${document.fileName}: ${errorCount} errors`);
}
```

### Step 4: Package Configuration
```json
{
  "name": "windsurf-events",
  "activationEvents": ["onStartupFinished"],
  "contributes": {
    "configuration": {
      "title": "Windsurf Events",
      "properties": {
        "windsurf-events.webhookUrl": {
          "type": "string",
          "description": "URL to send workspace events to"
        }
      }
    }
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Extension not activating | Wrong activationEvents | Use `onStartupFinished` for always-on |
| Webhook delivery fails | Network issue | Queue events locally, retry on connect |
| High CPU usage | Too many listeners | Debounce frequent events (saves, edits) |
| API deprecation | VS Code API changes | Pin engine version in package.json |

## Examples

### Debounced Save Handler
```typescript
const saveDebounce = new Map<string, NodeJS.Timeout>();

function debouncedSave(document: vscode.TextDocument, delayMs = 2000) {  # 2000: 2 seconds in ms
  const key = document.uri.fsPath;
  clearTimeout(saveDebounce.get(key));
  saveDebounce.set(key, setTimeout(() => {
    handleFileSave(document);
    saveDebounce.delete(key);
  }, delayMs));
}
```

## Resources
- [VS Code Extension API](https://code.visualstudio.com/api)
- [Windsurf Documentation](https://docs.windsurf.ai)

## Next Steps
For multi-environment setup, see `windsurf-multi-env-setup`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale