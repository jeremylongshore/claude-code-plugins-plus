---
name: techsmith-core-workflow-a
description: |
  TechSmith core workflow a for Snagit COM API and Camtasia automation.
  Use when working with TechSmith screen capture and video editing automation.
  Trigger: "techsmith core workflow a".
allowed-tools: Read, Write, Edit, Bash(powershell:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, screen-capture, video, techsmith]
compatible-with: claude-code
---

# TechSmith Core Workflow A

## Overview

Automated documentation pipeline: capture screenshots, annotate, and organize into guides.

## Instructions

### Step 1: Step Capture for Documentation

```powershell
# Capture a series of screenshots for a step-by-step guide
function Invoke-StepCapture {
    param([string]$GuideDir, [int]$StepCount = 10)

    New-Item -ItemType Directory -Force -Path $GuideDir | Out-Null
    $capture = New-Object -ComObject Snagit.ImageCapture
    $capture.Input = 2  # Region
    $capture.Output = 2
    $capture.OutputImageFile.FileType = 3  # PNG
    $capture.OutputImageFile.Directory = $GuideDir

    for ($i = 1; $i -le $StepCount; $i++) {
        $capture.OutputImageFile.Filename = "step_$($i.ToString('00'))"
        Write-Host "Capture step $i -- select region..."
        $capture.Capture()
        Start-Sleep -Seconds 1
    }
}

Invoke-StepCapture -GuideDir "C:\Guides\setup-tutorial"
```

### Step 2: Batch Annotate with Snagit

```powershell
# Open captures in Snagit Editor for annotation
$editor = New-Object -ComObject Snagit.ImageCapture
$editor.Input = 5  # siiFile
$editor.Output = 2
$editor.EnablePreview = $true  # Opens in Snagit Editor for annotation

$files = Get-ChildItem "C:\Guides\setup-tutorial\*.png"
foreach ($file in $files) {
    $editor.InputRegionOptions.UseFile = $file.FullName
    $editor.Capture()
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Capture area wrong | Region not selected | Use Window capture for consistency |
| Files overwritten | Same filename | Timestamped naming pattern |

## Resources

- [Snagit Step Capture](https://www.techsmith.com/learn/snagit/step-capture/)

## Next Steps

For video workflows, see `techsmith-core-workflow-b`.
