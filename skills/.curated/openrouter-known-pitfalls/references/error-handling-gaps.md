# Error Handling Gaps

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
