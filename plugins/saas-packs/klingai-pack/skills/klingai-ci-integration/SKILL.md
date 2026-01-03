---
name: klingai-ci-integration
description: |
  Integrate Kling AI video generation into CI/CD pipelines. Use when automating video
  content generation in build pipelines. Trigger with phrases like 'klingai ci',
  'kling ai github actions', 'klingai automation', 'automated video generation'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI CI/CD Integration

## Overview

This skill shows how to integrate Kling AI video generation into CI/CD pipelines using GitHub Actions, GitLab CI, and other automation platforms.

## Prerequisites

- Kling AI API key stored as CI secret
- CI/CD platform (GitHub Actions, GitLab CI, etc.)
- Python 3.8+ available in CI environment

## Instructions

Follow these steps for CI/CD integration:

1. **Store Secrets**: Add API key to CI secrets
2. **Create Workflow**: Define pipeline configuration
3. **Build Script**: Create video generation script
4. **Handle Output**: Store or deploy generated videos
5. **Add Notifications**: Alert on success/failure

## GitHub Actions Workflow

```yaml
# .github/workflows/generate-videos.yml
name: Generate Marketing Videos

on:
  workflow_dispatch:
    inputs:
      prompt:
        description: 'Video prompt'
        required: true
        default: 'Professional product showcase with modern lighting'
      duration:
        description: 'Video duration (5 or 10)'
        required: true
        default: '5'
        type: choice
        options:
          - '5'
          - '10'
      model:
        description: 'Model to use'
        required: true
        default: 'kling-v1.5'
        type: choice
        options:
          - 'kling-v1'
          - 'kling-v1.5'
          - 'kling-pro'

  schedule:
    # Generate weekly content every Monday at 9am UTC
    - cron: '0 9 * * 1'

jobs:
  generate:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install requests boto3

      - name: Generate video
        id: generate
        env:
          KLINGAI_API_KEY: ${{ secrets.KLINGAI_API_KEY }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          python scripts/generate_video.py \
            --prompt "${{ github.event.inputs.prompt || 'Weekly promotional video' }}" \
            --duration ${{ github.event.inputs.duration || '5' }} \
            --model "${{ github.event.inputs.model || 'kling-v1.5' }}" \
            --output-json video_result.json

          # Export result to job output
          echo "video_url=$(jq -r '.video_url' video_result.json)" >> $GITHUB_OUTPUT
          echo "job_id=$(jq -r '.job_id' video_result.json)" >> $GITHUB_OUTPUT

      - name: Upload to S3
        if: success()
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          python scripts/upload_to_s3.py \
            --video-url "${{ steps.generate.outputs.video_url }}" \
            --bucket "marketing-videos" \
            --key "generated/${{ steps.generate.outputs.job_id }}.mp4"

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: video-result
          path: video_result.json
          retention-days: 30

      - name: Notify Slack
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          fields: repo,message,commit,author
          text: |
            Video generation ${{ job.status }}
            Job ID: ${{ steps.generate.outputs.job_id }}
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

  # Run tests on generated videos
  validate:
    needs: generate
    runs-on: ubuntu-latest

    steps:
      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: video-result

      - name: Validate video
        run: |
          VIDEO_URL=$(jq -r '.video_url' video_result.json)

          # Check video is accessible
          HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$VIDEO_URL")
          if [ "$HTTP_STATUS" != "200" ]; then
            echo "Video not accessible: $HTTP_STATUS"
            exit 1
          fi

          echo "Video validation passed"
```

## Video Generation Script

```python
#!/usr/bin/env python3
# scripts/generate_video.py

import argparse
import json
import os
import sys
import time
import requests

def generate_video(prompt: str, duration: int, model: str) -> dict:
    """Generate video using Kling AI API."""
    api_key = os.environ["KLINGAI_API_KEY"]
    base_url = "https://api.klingai.com/v1"

    # Submit generation request
    print(f"Submitting video generation request...")
    print(f"  Prompt: {prompt[:50]}...")
    print(f"  Duration: {duration}s")
    print(f"  Model: {model}")

    response = requests.post(
        f"{base_url}/videos/text-to-video",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "prompt": prompt,
            "duration": duration,
            "model": model,
            "aspect_ratio": "16:9"
        }
    )

    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        sys.exit(1)

    job_id = response.json()["job_id"]
    print(f"Job submitted: {job_id}")

    # Poll for completion
    max_wait = 600  # 10 minutes
    poll_interval = 10
    elapsed = 0

    while elapsed < max_wait:
        response = requests.get(
            f"{base_url}/videos/{job_id}",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        data = response.json()
        status = data["status"]

        print(f"Status: {status} ({elapsed}s elapsed)")

        if status == "completed":
            return {
                "job_id": job_id,
                "status": "completed",
                "video_url": data["video_url"],
                "thumbnail_url": data.get("thumbnail_url"),
                "duration": duration,
                "model": model,
                "prompt": prompt
            }
        elif status == "failed":
            print(f"Error: Generation failed - {data.get('error')}")
            sys.exit(1)

        time.sleep(poll_interval)
        elapsed += poll_interval

    print("Error: Timeout waiting for video generation")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Generate video with Kling AI")
    parser.add_argument("--prompt", required=True, help="Video prompt")
    parser.add_argument("--duration", type=int, default=5, choices=[5, 10])
    parser.add_argument("--model", default="kling-v1.5")
    parser.add_argument("--output-json", help="Output JSON file path")

    args = parser.parse_args()

    result = generate_video(args.prompt, args.duration, args.model)

    if args.output_json:
        with open(args.output_json, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Result written to {args.output_json}")
    else:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```

## GitLab CI Configuration

```yaml
# .gitlab-ci.yml
stages:
  - generate
  - validate
  - deploy

variables:
  PYTHON_VERSION: "3.11"

generate_video:
  stage: generate
  image: python:${PYTHON_VERSION}

  before_script:
    - pip install requests

  script:
    - python scripts/generate_video.py
        --prompt "${VIDEO_PROMPT:-Default promotional video}"
        --duration ${VIDEO_DURATION:-5}
        --model "${VIDEO_MODEL:-kling-v1.5}"
        --output-json video_result.json

  artifacts:
    paths:
      - video_result.json
    expire_in: 1 week

  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
    - if: $CI_PIPELINE_SOURCE == "web"
    - if: $CI_PIPELINE_SOURCE == "trigger"

validate_video:
  stage: validate
  image: alpine:latest

  before_script:
    - apk add --no-cache curl jq

  script:
    - VIDEO_URL=$(jq -r '.video_url' video_result.json)
    - |
      HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$VIDEO_URL")
      if [ "$HTTP_STATUS" != "200" ]; then
        echo "Video validation failed: $HTTP_STATUS"
        exit 1
      fi
    - echo "Video validation passed"

  dependencies:
    - generate_video

deploy_video:
  stage: deploy
  image: amazon/aws-cli:latest

  script:
    - VIDEO_URL=$(jq -r '.video_url' video_result.json)
    - JOB_ID=$(jq -r '.job_id' video_result.json)
    - curl -o video.mp4 "$VIDEO_URL"
    - aws s3 cp video.mp4 s3://${S3_BUCKET}/videos/${JOB_ID}.mp4

  dependencies:
    - generate_video

  only:
    - main
```

## Batch Generation from File

```yaml
# .github/workflows/batch-generate.yml
name: Batch Video Generation

on:
  workflow_dispatch:
    inputs:
      prompts_file:
        description: 'Path to prompts JSON file'
        required: true
        default: 'prompts/weekly-content.json'

jobs:
  generate:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include: ${{ fromJson(needs.load-prompts.outputs.prompts) }}
      max-parallel: 5

    steps:
      - uses: actions/checkout@v4

      - name: Generate video
        env:
          KLINGAI_API_KEY: ${{ secrets.KLINGAI_API_KEY }}
        run: |
          python scripts/generate_video.py \
            --prompt "${{ matrix.prompt }}" \
            --duration ${{ matrix.duration }} \
            --model "${{ matrix.model }}" \
            --output-json "results/${{ matrix.id }}.json"

      - uses: actions/upload-artifact@v4
        with:
          name: video-${{ matrix.id }}
          path: results/${{ matrix.id }}.json

  load-prompts:
    runs-on: ubuntu-latest
    outputs:
      prompts: ${{ steps.load.outputs.prompts }}
    steps:
      - uses: actions/checkout@v4
      - id: load
        run: |
          echo "prompts=$(cat ${{ inputs.prompts_file }})" >> $GITHUB_OUTPUT
```

## Output

Successful execution produces:
- Automated video generation in CI pipeline
- Generated videos stored in cloud storage
- Notifications on completion/failure
- Artifacts for downstream processing

## Error Handling

Common errors and solutions:
1. **Secret Not Found**: Verify KLINGAI_API_KEY in repository secrets
2. **Timeout**: Increase max_wait in generation script
3. **Rate Limit**: Add delays between batch jobs

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [GitHub Actions](https://docs.github.com/en/actions)
- [GitLab CI](https://docs.gitlab.com/ee/ci/)
- [Kling AI API](https://docs.klingai.com/api)
