---
name: techsmith-local-dev-loop
description: |
  TechSmith local dev loop for Snagit COM API and Camtasia automation.
  Use when working with TechSmith screen capture and video editing automation.
  Trigger: "techsmith local dev loop".
allowed-tools: Read, Write, Edit, Bash(powershell:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, screen-capture, video, techsmith]
compatible-with: claude-code
---

# TechSmith Local Dev Loop

## Overview

Set up a development workflow for TechSmith automation scripts with PowerShell testing.

## Instructions

### Step 1: Project Structure

```
techsmith-automation/
├── scripts/
│   ├── capture-screenshot.ps1
│   ├── batch-render.ps1
│   └── capture-video.ps1
├── tests/
│   └── test-com-connection.ps1
├── output/
└── templates/
    └── camtasia-presets/
```

### Step 2: Test COM Connection

```powershell
# tests/test-com-connection.ps1
Describe "Snagit COM Server" {
    It "Should create ImageCapture object" {
        $capture = New-Object -ComObject Snagit.ImageCapture
        $capture | Should -Not -BeNullOrEmpty
    }

    It "Should create VideoCapture object" {
        $video = New-Object -ComObject Snagit.VideoCapture
        $video | Should -Not -BeNullOrEmpty
    }
}
```

### Step 3: Run Tests with Pester

```powershell
Install-Module -Name Pester -Force -SkipPublisherCheck
Invoke-Pester ./tests/ -Output Detailed
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| COM not available | Snagit not installed | Install Snagit on dev machine |
| Pester not found | Module missing | `Install-Module Pester` |

## Resources

- [Pester Testing Framework](https://pester.dev/)
- [Snagit COM Samples](https://github.com/TechSmith/Snagit-COM-Samples)

## Next Steps

Proceed to `techsmith-sdk-patterns`.
