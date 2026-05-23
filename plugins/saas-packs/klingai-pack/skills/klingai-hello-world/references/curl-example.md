# Curl Example

## cURL Example

```bash
# Step 1: Submit request
JOB_ID=$(curl -s -X POST https://api.klingai.com/v1/videos/text2video \
  -H "Authorization: Bearer $KLINGAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A golden retriever running through a sunny meadow",
    "duration": 5,
    "aspect_ratio": "16:9"
  }' | jq -r '.job_id')

echo "Job ID: $JOB_ID"

# Step 2: Poll for status
while true; do
  STATUS=$(curl -s https://api.klingai.com/v1/videos/$JOB_ID \
    -H "Authorization: Bearer $KLINGAI_API_KEY" | jq -r '.status')

  echo "Status: $STATUS"

  if [ "$STATUS" = "completed" ]; then
    curl -s https://api.klingai.com/v1/videos/$JOB_ID \
      -H "Authorization: Bearer $KLINGAI_API_KEY" | jq '.video_url'
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Generation failed!"
    break
  fi

  sleep 5
done
```
