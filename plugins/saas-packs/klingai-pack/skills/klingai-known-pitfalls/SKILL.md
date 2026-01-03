---
name: klingai-known-pitfalls
description: |
  Avoid common mistakes when using Kling AI. Use when troubleshooting issues or learning
  best practices to prevent problems. Trigger with phrases like 'klingai pitfalls',
  'kling ai mistakes', 'klingai gotchas', 'klingai best practices'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Known Pitfalls

## Overview

This skill documents common mistakes, gotchas, and pitfalls when working with Kling AI, along with solutions and best practices to avoid them.

## Prerequisites

- Basic Kling AI usage experience
- Encountered issues to troubleshoot
- Desire to improve implementation

## Instructions

Follow these steps to avoid pitfalls:

1. **Review Common Issues**: Understand frequent problems
2. **Apply Best Practices**: Implement recommendations
3. **Test Thoroughly**: Validate implementations
4. **Monitor Continuously**: Watch for new issues
5. **Update Regularly**: Keep up with API changes

## Common Pitfalls

### 1. Not Handling Async Jobs

```python
# WRONG: Assuming immediate result
def bad_generate():
    response = requests.post(
        "https://api.klingai.com/v1/videos/text-to-video",
        json={"prompt": "test"}
    )
    # This returns job_id, NOT video_url!
    video_url = response.json()["video_url"]  # KeyError!

# RIGHT: Poll for completion
def good_generate():
    response = requests.post(
        "https://api.klingai.com/v1/videos/text-to-video",
        json={"prompt": "test"}
    )
    job_id = response.json()["job_id"]

    # Poll until complete
    while True:
        status = requests.get(f"https://api.klingai.com/v1/videos/{job_id}")
        data = status.json()

        if data["status"] == "completed":
            return data["video_url"]
        elif data["status"] == "failed":
            raise Exception(data.get("error"))

        time.sleep(5)
```

### 2. Ignoring Rate Limits

```python
# WRONG: Rapid fire requests
def bad_batch():
    for prompt in prompts:
        # Will hit rate limit quickly
        requests.post(url, json={"prompt": prompt})

# RIGHT: Respect rate limits
def good_batch():
    from ratelimit import limits, sleep_and_retry

    @sleep_and_retry
    @limits(calls=60, period=60)  # 60 requests per minute
    def rate_limited_generate(prompt):
        return requests.post(url, json={"prompt": prompt})

    for prompt in prompts:
        rate_limited_generate(prompt)
```

### 3. Not Handling Errors

```python
# WRONG: No error handling
def bad_client():
    response = requests.post(url, json={"prompt": prompt})
    return response.json()  # Will crash on error

# RIGHT: Comprehensive error handling
def good_client():
    try:
        response = requests.post(url, json={"prompt": prompt}, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print("Request timed out - retry later")
        raise
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            retry_after = int(e.response.headers.get("Retry-After", 60))
            print(f"Rate limited - wait {retry_after}s")
        elif e.response.status_code == 401:
            print("Invalid API key")
        elif e.response.status_code == 400:
            print(f"Bad request: {e.response.json()}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        raise
```

### 4. Hardcoding API Keys

```python
# WRONG: Hardcoded secret
API_KEY = "klingai_sk_1234567890"  # Never do this!

# RIGHT: Environment variable
API_KEY = os.environ.get("KLINGAI_API_KEY")
if not API_KEY:
    raise ValueError("KLINGAI_API_KEY environment variable not set")

# BETTER: Secrets manager
from google.cloud import secretmanager

def get_api_key():
    client = secretmanager.SecretManagerServiceClient()
    name = "projects/my-project/secrets/klingai-api-key/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```

### 5. Not Validating Prompts

```python
# WRONG: Pass any prompt directly
def bad_generate(user_prompt):
    return api.generate(prompt=user_prompt)  # Could be anything!

# RIGHT: Validate and sanitize prompts
def good_generate(user_prompt):
    # Length check
    if len(user_prompt) < 10:
        raise ValueError("Prompt too short - needs more detail")
    if len(user_prompt) > 2000:
        raise ValueError("Prompt too long - please shorten")

    # Content check
    prohibited = ["violence", "explicit", "illegal"]
    for word in prohibited:
        if word in user_prompt.lower():
            raise ValueError(f"Prohibited content detected: {word}")

    # Sanitize
    cleaned_prompt = user_prompt.strip()
    cleaned_prompt = " ".join(cleaned_prompt.split())  # Normalize whitespace

    return api.generate(prompt=cleaned_prompt)
```

### 6. Ignoring Video Expiration

```python
# WRONG: Store URL and assume it works forever
def bad_storage():
    result = generate_video(prompt)
    database.save(video_url=result["video_url"])  # URL will expire!

# RIGHT: Download and store video
def good_storage():
    result = generate_video(prompt)
    video_url = result["video_url"]

    # Download immediately
    response = requests.get(video_url)
    video_content = response.content

    # Store in permanent storage
    s3.put_object(
        Bucket="my-bucket",
        Key=f"videos/{result['job_id']}.mp4",
        Body=video_content
    )

    # Save permanent URL
    database.save(
        video_url=f"https://my-bucket.s3.amazonaws.com/videos/{result['job_id']}.mp4",
        original_job_id=result["job_id"]
    )
```

### 7. Blocking Main Thread

```python
# WRONG: Block while waiting
def bad_sync():
    job_id = submit_job(prompt)
    while True:
        status = check_status(job_id)
        if status == "completed":
            break
        time.sleep(5)  # Blocks entire application

# RIGHT: Async or background processing
import asyncio

async def good_async():
    job_id = await submit_job(prompt)

    while True:
        status = await check_status(job_id)
        if status == "completed":
            break
        await asyncio.sleep(5)  # Yields to event loop

# Or use webhooks
def good_webhook():
    job_id = submit_job(prompt, webhook_url="https://myapp.com/webhook")
    # Don't wait - webhook will notify when done
```

### 8. Not Tracking Costs

```python
# WRONG: Unlimited spending
def bad_unlimited():
    for prompt in prompts:  # Could be thousands!
        generate_video(prompt)

# RIGHT: Budget controls
def good_budget_controlled():
    DAILY_BUDGET = 100  # Credits
    used_today = get_usage_today()

    for prompt in prompts:
        cost_estimate = estimate_cost(prompt)

        if used_today + cost_estimate > DAILY_BUDGET:
            print(f"Budget exceeded: {used_today}/{DAILY_BUDGET}")
            break

        generate_video(prompt)
        used_today += cost_estimate
```

### 9. Poor Prompt Engineering

```python
# WRONG: Vague prompt
bad_prompt = "a video"

# WRONG: Too complex
bad_prompt = "a hyper-realistic 8K video of a dragon fighting a robot in a futuristic city with explosions and lens flares and dramatic lighting and cinematic camera movements and..."

# RIGHT: Clear and specific
good_prompt = """
A peaceful forest clearing at dawn.
Sunlight filters through the trees.
Gentle fog drifts across the ground.
Cinematic, warm lighting, calm mood.
"""
```

### 10. Not Testing Before Production

```python
# WRONG: Deploy untested
def bad_deploy():
    # Hope it works in production!
    deploy_to_production(video_service)

# RIGHT: Test thoroughly
def good_deploy():
    # Unit tests
    def test_prompt_validation():
        assert validate_prompt("test") == False
        assert validate_prompt("valid prompt here") == True

    # Integration test with sandbox
    def test_sandbox_generation():
        result = generate_video(
            prompt="Test video",
            environment="sandbox"
        )
        assert result["status"] == "completed"

    # Load test
    def test_rate_limits():
        for i in range(100):
            try:
                generate_video(f"Test {i}")
            except RateLimitError:
                assert i >= 60  # Expected to hit limit

    # Run all tests before deploy
    test_prompt_validation()
    test_sandbox_generation()
    test_rate_limits()

    deploy_to_production(video_service)
```

## Quick Reference Checklist

```
Before Going Live:

[ ] API key stored securely (not in code)
[ ] Error handling for all API calls
[ ] Rate limiting implemented
[ ] Async job handling (polling or webhooks)
[ ] Prompt validation
[ ] Video download/storage (URLs expire)
[ ] Budget controls
[ ] Logging and monitoring
[ ] Test coverage
[ ] Fallback handling

Common Error Codes:
- 400: Bad request (check prompt/params)
- 401: Invalid API key
- 403: Insufficient permissions
- 429: Rate limit exceeded
- 500: Server error (retry)
- 503: Service unavailable (retry later)
```

## Output

Successful execution produces:
- Robust error handling
- Proper async patterns
- Secure credential management
- Cost-controlled generation

## Error Handling

This entire skill is about error handling - apply the patterns shown above.

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Best Practices](https://docs.klingai.com/best-practices)
- [API Error Reference](https://docs.klingai.com/errors)
- [Security Guidelines](https://docs.klingai.com/security)
