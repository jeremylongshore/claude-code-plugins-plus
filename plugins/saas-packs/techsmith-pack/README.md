# TechSmith Skill Pack

> 18 production-ready Claude Code skills for TechSmith -- real Snagit COM API and Camtasia batch production code.

## What This Is

A complete skill pack for automating TechSmith Snagit and Camtasia. Every skill contains real COM API code: `Snagit.ImageCapture`, `Snagit.VideoCapture`, `CamtasiaProducer.exe` batch rendering, PowerShell automation, and Python interop via pywin32. No placeholder imports.

## Installation

```bash
/plugin install techsmith-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `techsmith-install-auth` | Register Snagit COM server, verify COM interop, Camtasia CLI |
| S02 | `techsmith-hello-world` | Capture screenshot with COM API, render Camtasia project to MP4 |
| S03 | `techsmith-local-dev-loop` | PowerShell project structure, Pester tests for COM connection |
| S04 | `techsmith-sdk-patterns` | Capture factory, batch rendering, timestamped output naming |
| S05 | `techsmith-core-workflow-a` | Step capture pipeline, batch annotation, documentation guides |
| S06 | `techsmith-core-workflow-b` | Camtasia multi-format export, presets, watermarking |
| S07 | `techsmith-common-errors` | COM registration, permission, file lock, codec issues |
| S08 | `techsmith-debug-bundle` | COM diagnostics, Snagit version check, capture test |
| S09 | `techsmith-rate-limits` | Capture timing, rendering queue, concurrent limits |
| S10 | `techsmith-security-basics` | Output directory permissions, watermark protection |
| S11 | `techsmith-prod-checklist` | Automation deployment, COM server verification, preset validation |
| S12 | `techsmith-upgrade-migration` | Snagit version migration, COM API changes between versions |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `techsmith-ci-integration` | GitHub Actions with Windows runners, PowerShell test automation |
| P14 | `techsmith-deploy-integration` | Deploy capture scripts, shared preset distribution |
| P15 | `techsmith-webhooks-events` | File system watchers for capture events, auto-processing |
| P16 | `techsmith-performance-tuning` | Parallel rendering, capture optimization, memory management |
| P17 | `techsmith-cost-tuning` | License management, per-seat vs site licensing |
| P18 | `techsmith-reference-architecture` | Documentation pipeline: capture, annotate, render, publish |

## Key Concepts

- **Snagit COM API**: `Snagit.ImageCapture` and `Snagit.VideoCapture` COM objects
- **Input types**: Desktop (0), Region (2), Window (4), File (5)
- **Output types**: Clipboard (1), File (2), Printer (4)
- **Camtasia Producer**: CLI batch rendering with `/i`, `/o`, `/preset` flags
- **Platforms**: Windows-only (COM interop), PowerShell, C#, Python (pywin32)

## License

MIT
