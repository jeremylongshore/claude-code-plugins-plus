---
name: techsmith-hello-world
description: |
  Capture a screenshot with Snagit COM API and produce a Camtasia video.
  Use when automating screen captures, batch-processing recordings,
  or building documentation pipelines with TechSmith tools.
  Trigger: "techsmith hello world, snagit capture, camtasia render".
allowed-tools: Read, Write, Edit, Bash(powershell:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, screen-capture, video, techsmith]
compatible-with: claude-code
---

# TechSmith Hello World

## Overview

Capture a screenshot with Snagit's COM API and render a Camtasia project to MP4 -- the two fundamental TechSmith automation operations.

## Instructions

### Step 1: Snagit Image Capture (PowerShell)

```powershell
# Create a Snagit image capture object
$capture = New-Object -ComObject Snagit.ImageCapture

# Configure capture settings
$capture.Input = 4          # siiWindow = 4 (capture active window)
$capture.Output = 2         # sioFile = 2 (save to file)
$capture.OutputImageFile.FileType = 4  # sitJPEG = 4
$capture.OutputImageFile.Directory = "C:\Screenshots"
$capture.OutputImageFile.Filename = "capture"

# Enable preview in Snagit Editor
$capture.EnablePreview = $false  # Set $true to open in editor

# Capture!
$capture.Capture()
Write-Host "Screenshot saved to C:\Screenshots\capture.jpg"
```

### Step 2: Snagit Video Capture (PowerShell)

```powershell
$videoCapture = New-Object -ComObject Snagit.VideoCapture

$videoCapture.Input = 2       # siiRegion = 2
$videoCapture.Output = 2      # sioFile = 2
$videoCapture.OutputImageFile.Directory = "C:\Recordings"

# Start recording
$videoCapture.Capture()
# Recording starts -- manually stop via Snagit UI or timer
```

### Step 3: Camtasia Batch Production

```powershell
# Render a .tscproj to MP4 using CamtasiaProducer
$producer = "C:\Program Files\TechSmith\Camtasia 2025\CamtasiaProducer.exe"

& $producer `
  /i "C:\Projects\tutorial.tscproj" `
  /o "C:\Output\tutorial.mp4" `
  /preset "MP4 - Smart Player (up to 1080p)" `
  /watermark "none"

Write-Host "Camtasia render complete: tutorial.mp4"
```

### Step 4: Python Automation

```python
import win32com.client

# Snagit image capture
capture = win32com.client.Dispatch("Snagit.ImageCapture")
capture.Input = 0       # siiDesktop = 0 (full screen)
capture.Output = 2      # sioFile
capture.OutputImageFile.FileType = 3  # sitPNG
capture.OutputImageFile.Directory = "C:\\Screenshots"
capture.OutputImageFile.Filename = "auto_capture"
capture.EnablePreview = False
capture.Capture()
print("Screenshot captured via Python")
```

## Output

```
Screenshot saved to C:\Screenshots\capture.jpg
Camtasia render complete: tutorial.mp4
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Snagit not running` | COM requires Snagit open | Launch Snagit first |
| `Access denied` on capture | Screen lock or UAC | Run as administrator |
| Camtasia render fails | Missing codec | Install required codec pack |
| Output file exists | Overwrite conflict | Add timestamp to filename |

## Resources

- [Snagit COM Samples](https://github.com/TechSmith/Snagit-COM-Samples)
- [PowerShell Image Capture Sample](https://github.com/TechSmith/Snagit-COM-Samples/blob/main/PowerShell/ImageCapture-Interactive.ps1)

## Next Steps

Proceed to `techsmith-local-dev-loop` for development workflow.
