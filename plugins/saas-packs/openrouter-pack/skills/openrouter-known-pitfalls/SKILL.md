---
name: openrouter-known-pitfalls
description: |
  Avoid common OpenRouter mistakes. Triggers on "openrouter pitfalls",
  "openrouter mistakes", "openrouter gotchas", "openrouter common issues".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# OpenRouter Known Pitfalls

## Authentication Issues

### Wrong Key Format
```python
# ❌ Wrong: OpenAI key format
api_key = "sk-..."  # OpenAI format

# ✓ Correct: OpenRouter key format
api_key = "sk-or-v1-..."  # OpenRouter format
```

### Missing Bearer Prefix
```python
# ❌ Wrong: No Bearer prefix
headers = {"Authorization": api_key}

# ✓ Correct: With Bearer prefix
headers = {"Authorization": f"Bearer {api_key}"}
```

### Hardcoded Keys
```python
# ❌ Wrong: Hardcoded key
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-or-v1-xxxxx"  # Never do this!
)

# ✓ Correct: Environment variable
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)
```

## Model Name Mistakes

### Missing Provider Prefix
```python
# ❌ Wrong: No provider prefix
model = "gpt-4-turbo"

# ✓ Correct: With provider prefix
model = "openai/gpt-4-turbo"
```

### Typos in Model Names
```python
# Common typos:
# ❌ "anthropic/claude-3-sonnet"   -> ✓ "anthropic/claude-3.5-sonnet"
# ❌ "openai/gpt4-turbo"           -> ✓ "openai/gpt-4-turbo"
# ❌ "meta/llama-3.1-70b"          -> ✓ "meta-llama/llama-3.1-70b-instruct"

# Verify model exists
def verify_model(model: str) -> bool:
    models = get_available_models(api_key)
    return any(m["id"] == model for m in models)
```

### Deprecated Model Names
```python
# Models get deprecated - check current list
# ❌ "anthropic/claude-2"          -> ✓ "anthropic/claude-3-haiku" (or newer)
# ❌ "openai/gpt-4-0314"           -> ✓ "openai/gpt-4-turbo"

# Always use canonical names from the API
response = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {api_key}"}
)
valid_models = [m["id"] for m in response.json()["data"]]
```

## Request Format Errors

### Invalid Message Structure
```python
# ❌ Wrong: Missing role
messages = [{"content": "Hello"}]

# ❌ Wrong: Invalid role
messages = [{"role": "assistant", "content": "Hello"}]  # Can't start with assistant

# ✓ Correct
messages = [{"role": "user", "content": "Hello"}]

# ✓ Correct with system
messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello"}
]
```

### Alternating Roles Violation
```python
# ❌ Wrong: Two user messages in a row
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "user", "content": "How are you?"}  # Must alternate
]

# ✓ Correct
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi!"},
    {"role": "user", "content": "How are you?"}
]
```

## Cost Surprises

### No max_tokens Limit
```python
# ❌ Risky: No response limit
response = client.chat.completions.create(
    model="anthropic/claude-3-opus",  # Expensive model
    messages=[{"role": "user", "content": prompt}]
    # Missing max_tokens - could be very long response
)

# ✓ Better: Set limits
response = client.chat.completions.create(
    model="anthropic/claude-3-opus",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=1000  # Control costs
)
```

### Wrong Model for Task
```python
# ❌ Expensive: Using Opus for simple tasks
response = client.chat.completions.create(
    model="anthropic/claude-3-opus",  # $75/M completion tokens
    messages=[{"role": "user", "content": "What's 2+2?"}]
)

# ✓ Cost-effective: Use Haiku for simple tasks
response = client.chat.completions.create(
    model="anthropic/claude-3-haiku",  # $1.25/M completion tokens
    messages=[{"role": "user", "content": "What's 2+2?"}]
)
```

### Not Tracking Costs
```python
# ❌ Problem: No cost visibility
for prompt in prompts:
    response = client.chat.completions.create(...)

# ✓ Better: Track costs
total_cost = 0
for prompt in prompts:
    response = client.chat.completions.create(...)
    cost = calculate_cost(response.usage)
    total_cost += cost
    if total_cost > budget:
        raise Exception("Budget exceeded")
```

## Error Handling Gaps

### No Error Handling
```python
# ❌ Wrong: No error handling
response = client.chat.completions.create(
    model=model,
    messages=messages
)
content = response.choices[0].message.content

# ✓ Correct: Handle errors
try:
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    content = response.choices[0].message.content
except RateLimitError:
    time.sleep(1)
    # Retry
except APIError as e:
    logging.error(f"API error: {e}")
    raise
```

### Not Handling Empty Responses
```python
# ❌ Problem: Assume content exists
content = response.choices[0].message.content
print(content.lower())  # Crashes if None

# ✓ Better: Handle None
content = response.choices[0].message.content
if content:
    print(content.lower())
else:
    print("No response generated")
```

## Rate Limiting Mistakes

### No Backoff Strategy
```python
# ❌ Wrong: Keep hammering on rate limit
while True:
    try:
        response = client.chat.completions.create(...)
        break
    except RateLimitError:
        continue  # Immediately retry

# ✓ Correct: Exponential backoff
for attempt in range(5):
    try:
        response = client.chat.completions.create(...)
        break
    except RateLimitError:
        wait = 2 ** attempt
        time.sleep(wait)
```

### Ignoring Rate Limit Headers
```python
# ✓ Better: Respect rate limit headers
def make_request_with_headers(prompt: str):
    response = client.chat.completions.create(...)

    # Check remaining requests
    # OpenRouter may include rate limit info in headers

    return response
```

## Streaming Pitfalls

### Not Handling Stream Properly
```python
# ❌ Wrong: Treating stream as single response
stream = client.chat.completions.create(..., stream=True)
print(stream.choices[0].message.content)  # Doesn't work

# ✓ Correct: Iterate through chunks
stream = client.chat.completions.create(..., stream=True)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Not Collecting Full Response
```python
# ❌ Problem: Only printing, not collecting
for chunk in stream:
    print(chunk.choices[0].delta.content)
# Can't access full response later

# ✓ Better: Collect while streaming
full_response = ""
for chunk in stream:
    content = chunk.choices[0].delta.content or ""
    print(content, end="")
    full_response += content
# Now full_response is available
```

## Context Length Errors

### Exceeding Context Limit
```python
# ❌ Problem: Very long prompt
long_prompt = "..." * 100000  # Way too long
response = client.chat.completions.create(
    model="openai/gpt-3.5-turbo",  # Only 16K context
    messages=[{"role": "user", "content": long_prompt}]
)

# ✓ Better: Check and truncate
def safe_chat(prompt: str, model: str):
    max_context = {
        "openai/gpt-3.5-turbo": 16000,
        "openai/gpt-4-turbo": 128000,
        "anthropic/claude-3.5-sonnet": 200000,
    }

    limit = max_context.get(model, 4000)
    tokens = len(prompt) // 4

    if tokens > limit * 0.9:
        prompt = prompt[:int(limit * 0.9 * 4)]

    return client.chat.completions.create(...)
```

## Provider Differences

### Assuming Identical Behavior
```python
# ❌ Problem: Same code, different providers
# Function calling syntax differs slightly

# OpenAI style (works on OpenAI models)
response = client.chat.completions.create(
    model="openai/gpt-4-turbo",
    tools=[...],
    tool_choice="auto"
)

# Claude might have slight differences
# Always test with target provider
```

### Different Response Formats
```python
# Different models may format responses differently
# Always handle variations

def extract_response(response, model: str):
    content = response.choices[0].message.content

    # Some models add extra formatting
    if content.startswith("```"):
        # Strip code blocks if not expected
        content = content.strip("`")

    return content
```

## Debugging Checklist

```
Common Issues Checklist:
[ ] API key is correct format (sk-or-...)
[ ] Authorization header has "Bearer " prefix
[ ] Model name includes provider prefix
[ ] Model name is correctly spelled
[ ] Messages array has valid structure
[ ] max_tokens is set appropriately
[ ] Error handling is implemented
[ ] Rate limiting is handled
[ ] Costs are being tracked
[ ] Context length is within limits
```
