---
name: klingai-ci-integration
description: |
  Integrate Kling AI video generation into CI/CD pipelines. Use when automating video content
  in GitHub Actions or GitLab CI. Trigger with phrases like 'klingai ci', 'kling ai github actions',
  'klingai automation', 'automated video generation'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, ci-cd, automation]

---
# Kling AI CI Integration

## Overview

Automate video generation in CI/CD pipelines. Common use cases: generate product demos on release, create marketing videos from prompts in a YAML file, regression-test video quality across model versions.

## GitHub Actions Workflow

```yaml
# .github/workflows/generate-videos.yml
name: Generate Videos
on:
  workflow_dispatch:
    inputs:
      prompt:
        description: "Video prompt"
        required: true
      model:
        description: "Model version"
        default: "kling-v2-master"

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install PyJWT requests

      - name: Generate video
        env:
          KLING_ACCESS_KEY: ${{ secrets.KLING_ACCESS_KEY }}
          KLING_SECRET_KEY: ${{ secrets.KLING_SECRET_KEY }}
        run: |
          python3 scripts/generate-video.py \
            --prompt "${{ inputs.prompt }}" \
            --model "${{ inputs.model }}" \
            --output output/

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: generated-video
          path: output/*.mp4
          retention-days: 7
```

## CI Generation Script

```python
#!/usr/bin/env python3
"""scripts/generate-video.py -- CI-friendly video generation."""
import argparse
import jwt
import time
import os
import requests
import sys

BASE = "https://api.klingai.com/v1"

def get_headers():
    ak, sk = os.environ["KLING_ACCESS_KEY"], os.environ["KLING_SECRET_KEY"]
    token = jwt.encode(
        {"iss": ak, "exp": int(time.time()) + 1800, "nbf": int(time.time()) - 5},
        sk, algorithm="HS256", headers={"alg": "HS256", "typ": "JWT"}
    )
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--model", default="kling-v2-master")
    parser.add_argument("--duration", default="5")
    parser.add_argument("--mode", default="standard")
    parser.add_argument("--output", default="output/")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    # Submit
    r = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
        "model_name": args.model,
        "prompt": args.prompt,
        "duration": args.duration,
        "mode": args.mode,
    })
    r.raise_for_status()
    task_id = r.json()["data"]["task_id"]
    print(f"Task submitted: {task_id}")

    # Poll
    start = time.monotonic()
    while time.monotonic() - start < args.timeout:
        time.sleep(15)
        result = requests.get(
            f"{BASE}/videos/text2video/{task_id}", headers=get_headers()
        ).json()
        status = result["data"]["task_status"]
        elapsed = int(time.monotonic() - start)
        print(f"[{elapsed}s] Status: {status}")

        if status == "succeed":
            video_url = result["data"]["task_result"]["videos"][0]["url"]
            filepath = os.path.join(args.output, f"{task_id}.mp4")
            with open(filepath, "wb") as f:
                f.write(requests.get(video_url).content)
            print(f"Saved: {filepath}")
            return

        if status == "failed":
            print(f"FAILED: {result['data'].get('task_status_msg')}", file=sys.stderr)
            sys.exit(1)

    print("TIMEOUT: generation did not complete", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
```

## Batch from YAML Config

```yaml
# video-prompts.yml
videos:
  - name: product-hero
    prompt: "Sleek laptop floating in space with particle effects"
    model: kling-v2-6
    mode: professional
  - name: feature-demo
    prompt: "Dashboard interface morphing between screens"
    model: kling-v2-5-turbo
    mode: standard
```

```python
import yaml

with open("video-prompts.yml") as f:
    config = yaml.safe_load(f)

for video in config["videos"]:
    task_id = submit_async(video["prompt"], model=video["model"])
    print(f"{video['name']}: {task_id}")
```

## GitLab CI

```yaml
# .gitlab-ci.yml
generate-video:
  image: python:3.11-slim
  stage: build
  script:
    - pip install PyJWT requests
    - python3 scripts/generate-video.py --prompt "$VIDEO_PROMPT" --output output/
  artifacts:
    paths:
      - output/*.mp4
    expire_in: 7 days
  variables:
    KLING_ACCESS_KEY: $KLING_ACCESS_KEY
    KLING_SECRET_KEY: $KLING_SECRET_KEY
```

## Secret Management

| Platform | Store AK/SK in |
|----------|---------------|
| GitHub Actions | Repository Secrets |
| GitLab CI | CI/CD Variables (masked) |
| AWS CodeBuild | Parameter Store / Secrets Manager |
| GCP Cloud Build | Secret Manager |

**Never** put API keys in the workflow YAML or commit them to the repo.

## Resources

- [API Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
