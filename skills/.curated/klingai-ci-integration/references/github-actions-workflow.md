# Github Actions Workflow

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
