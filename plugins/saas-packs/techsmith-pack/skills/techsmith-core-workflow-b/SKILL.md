---
name: techsmith-core-workflow-b
description: |
  TechSmith core workflow b for Snagit COM API and Camtasia automation.
  Use when working with TechSmith screen capture and video editing automation.
  Trigger: "techsmith core workflow b".
allowed-tools: Read, Write, Edit, Bash(powershell:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, screen-capture, video, techsmith]
compatible-with: claude-code
---

# TechSmith Core Workflow B

## Overview

Camtasia video editing automation: batch rendering, preset management, and template-based production.

## Instructions

### Step 1: List Available Presets

```powershell
$producer = "C:\Program Files\TechSmith\Camtasia 2025\CamtasiaProducer.exe"
& $producer /listpresets
# Common presets:
# - "MP4 - Smart Player (up to 1080p)"
# - "MP4 only (up to 1080p)"
# - "Audio Only (M4A)"
# - "Custom Production Settings"
```

### Step 2: Multi-Format Export

```powershell
$project = "C:\Projects\tutorial.tscproj"
$formats = @(
    @{ Preset = "MP4 only (up to 1080p)"; Ext = "mp4" },
    @{ Preset = "Audio Only (M4A)"; Ext = "m4a" }
)

foreach ($fmt in $formats) {
    $output = "C:\Output\tutorial.$($fmt.Ext)"
    & $producer /i "$project" /o "$output" /preset "$($fmt.Preset)"
    Write-Host "Rendered: $output"
}
```

### Step 3: Watermark and Branding

```powershell
& $producer `
    /i "C:\Projects\tutorial.tscproj" `
    /o "C:\Output\branded.mp4" `
    /preset "MP4 only (up to 1080p)" `
    /watermark "C:\Assets\logo.png"
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Invalid preset | Typo in preset name | Use /listpresets to verify |
| Render timeout | Long video | Increase timeout or use async |
| Missing media | Moved source files | Keep project and media together |

## Resources

- [Camtasia Batch Production](https://support.techsmith.com/)

## Next Steps

For common errors, see `techsmith-common-errors`.
