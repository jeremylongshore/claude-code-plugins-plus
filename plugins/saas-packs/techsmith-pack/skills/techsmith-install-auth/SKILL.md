---
name: techsmith-install-auth
description: |
  Install TechSmith Snagit COM API and register the COM server for automation.
  Use when setting up Snagit automation, configuring COM interop,
  or initializing Camtasia batch processing.
  Trigger: "install techsmith, setup snagit, techsmith COM API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, screen-capture, video, techsmith]
compatible-with: claude-code
---

# TechSmith Install & Auth

## Overview

TechSmith products (Snagit, Camtasia) offer automation through the Snagit COM Server API (Windows) and Camtasia's command-line batch processing. No traditional API keys -- COM registration is the auth mechanism.

## Prerequisites

- Windows OS (COM API is Windows-only)
- Snagit 2023+ or Camtasia 2023+ installed
- PowerShell 5.1+ or .NET SDK for COM interop

## Instructions

### Step 1: Verify Snagit COM Server Registration

```powershell
# Check if Snagit COM server is registered
$snagit = New-Object -ComObject Snagit.ImageCapture
if ($snagit) { Write-Host "Snagit COM server registered successfully" }
```

### Step 2: Re-register COM Server (if needed)

```powershell
# Run as Administrator
$snagitPath = "C:\Program Files\TechSmith\Snagit 2025\Snagit32.exe"
& $snagitPath /register
```

### Step 3: Python COM Interop

```python
# pip install pywin32
import win32com.client

snagit = win32com.client.Dispatch("Snagit.ImageCapture")
print(f"Snagit version: Connected via COM")
```

### Step 4: C# COM Interop

```csharp
using SNAGITLib;

var capture = new ImageCaptureClass();
Console.WriteLine("Snagit COM initialized");
```

### Step 5: Verify Camtasia CLI

```powershell
# Camtasia batch producer
$camtasia = "C:\Program Files\TechSmith\Camtasia 2025\CamtasiaProducer.exe"
& $camtasia --help
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `REGDB_E_CLASSNOTREG` | COM not registered | Run Snagit32.exe /register as admin |
| `Class not registered` | Wrong bitness | Use 32-bit PowerShell for 32-bit Snagit |
| `pywin32 not found` | Missing package | `pip install pywin32` |
| Camtasia CLI not found | Not in PATH | Use full path to CamtasiaProducer.exe |

## Resources

- [Snagit COM Samples](https://github.com/TechSmith/Snagit-COM-Samples)
- [Snagit COM Server Guide (PDF)](https://assets.techsmith.com/Docs/Snagit-2022-COM-Server-Guide.pdf)
- [TechSmith GitHub](https://github.com/TechSmith)

## Next Steps

Proceed to `techsmith-hello-world` for your first capture.
