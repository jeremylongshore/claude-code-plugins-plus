---
name: techsmith-sdk-patterns
description: |
  TechSmith sdk patterns for Snagit COM API and Camtasia automation.
  Use when working with TechSmith screen capture and video editing automation.
  Trigger: "techsmith sdk patterns".
allowed-tools: Read, Write, Edit, Bash(powershell:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, screen-capture, video, techsmith]
compatible-with: claude-code
---

# TechSmith Sdk Patterns

## Overview

Production patterns for TechSmith COM API: capture factories, output configuration, and batch processing.

## Instructions

### Step 1: Capture Factory Pattern

```powershell
function New-SnagitCapture {
    param(
        [ValidateSet('Desktop', 'Window', 'Region')]
        [string]$InputType = 'Window',
        [ValidateSet('PNG', 'JPEG', 'BMP', 'GIF')]
        [string]$Format = 'PNG',
        [string]$OutputDir = "C:\Screenshots",
        [bool]$Preview = $false
    )

    $inputMap = @{ Desktop = 0; Window = 4; Region = 2 }
    $formatMap = @{ PNG = 3; JPEG = 4; BMP = 0; GIF = 2 }

    $capture = New-Object -ComObject Snagit.ImageCapture
    $capture.Input = $inputMap[$InputType]
    $capture.Output = 2  # File
    $capture.OutputImageFile.FileType = $formatMap[$Format]
    $capture.OutputImageFile.Directory = $OutputDir
    $capture.OutputImageFile.Filename = "capture_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    $capture.EnablePreview = $Preview

    return $capture
}

# Usage
$cap = New-SnagitCapture -InputType Window -Format PNG
$cap.Capture()
```

### Step 2: Batch Camtasia Rendering

```powershell
function Invoke-CamtasiaBatchRender {
    param(
        [string[]]$ProjectFiles,
        [string]$OutputDir,
        [string]$Preset = "MP4 - Smart Player (up to 1080p)"
    )

    $producer = "C:\Program Files\TechSmith\Camtasia 2025\CamtasiaProducer.exe"
    $results = @()

    foreach ($project in $ProjectFiles) {
        $name = [System.IO.Path]::GetFileNameWithoutExtension($project)
        $output = Join-Path $OutputDir "$name.mp4"

        $proc = Start-Process -FilePath $producer -ArgumentList @(
            "/i", "`"$project`"",
            "/o", "`"$output`"",
            "/preset", "`"$Preset`""
        ) -Wait -PassThru

        $results += @{ File = $name; ExitCode = $proc.ExitCode }
    }
    return $results
}
```

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Factory function | Different capture types | Consistent configuration |
| Batch rendering | Multiple projects | Automated pipeline |
| Timestamped names | Avoid overwrites | Unique filenames |

## Resources

- [Snagit COM Server Guide](https://assets.techsmith.com/Docs/Snagit-2022-COM-Server-Guide.pdf)

## Next Steps

Apply patterns in `techsmith-core-workflow-a`.
