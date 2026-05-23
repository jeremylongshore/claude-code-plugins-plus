# Gitlab Ci Configuration

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
