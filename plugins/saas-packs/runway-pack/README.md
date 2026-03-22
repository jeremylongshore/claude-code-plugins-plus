# Runway Skill Pack

> Claude Code skill pack for Runway — AI video generation, Gen-3 Alpha, image-to-video, text-to-video, and creative AI API (18 skills)

## What This Covers

Runway is an AI creative platform for video generation. This pack covers the **Runway REST API** and **runwayml** Python SDK for text-to-video, image-to-video, and video-to-video generation using Gen-3 Alpha and Gen-4 Turbo models.

**Key APIs:** Text-to-Video, Image-to-Video, Video-to-Video, Task Management (create, poll, retrieve). Auth: `Authorization: Bearer <api_key>`. SDK: `runwayml` (pip) or `@runwayml/sdk` (npm).

## Installation

```bash
/plugin install runway-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `runway-install-auth` | Install `runwayml` SDK, configure API key |
| `runway-hello-world` | Generate first video from text prompt |
| `runway-local-dev-loop` | Local development with task polling and output management |
| `runway-sdk-patterns` | SDK client patterns, async/sync, task polling helpers |
| `runway-core-workflow-a` | Text-to-video: prompts, parameters, model selection |
| `runway-core-workflow-b` | Image-to-video and video-to-video generation |
| `runway-common-errors` | Fix generation failures, prompt issues, quota errors |
| `runway-debug-bundle` | Collect task IDs, generation parameters, error logs |
| `runway-rate-limits` | Handle API rate limits for generation requests |
| `runway-security-basics` | API key management, content policy compliance |
| `runway-prod-checklist` | Production: queue management, output storage, monitoring |
| `runway-upgrade-migration` | SDK version and model upgrades |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `runway-ci-integration` | CI pipeline with generation validation tests |
| `runway-deploy-integration` | Deploy video generation service to cloud |
| `runway-webhooks-events` | Handle task completion callbacks |
| `runway-performance-tuning` | Optimize generation speed and quality |
| `runway-cost-tuning` | Optimize per-generation costs, model selection |
| `runway-reference-architecture` | AI video pipeline architecture |

## Key Documentation

- [Runway API Documentation](https://docs.dev.runwayml.com/)
- [API Reference](https://docs.dev.runwayml.com/api/)
- [Python SDK](https://github.com/runwayml/sdk-python)
- [Input Parameters](https://docs.dev.runwayml.com/assets/inputs/)

## License

MIT
