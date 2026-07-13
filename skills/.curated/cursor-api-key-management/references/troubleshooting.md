# Troubleshooting

## Troubleshooting

### "Invalid API Key"

```
Checklist:
[ ] Key is correctly copied (no extra spaces)
[ ] Key hasn't expired
[ ] Key has required permissions
[ ] Correct provider selected
[ ] Account is active

Test key:
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-..."
```

### "Rate Limited"

```
Solutions:
1. Check rate limits for your tier
2. Upgrade API plan if needed
3. Reduce request frequency
4. Use caching/debouncing
```

### "Model Not Available"

```
Causes:
- Model requires waitlist access
- Model not available in your region
- Wrong model name

Verify:
1. Check provider documentation
2. Confirm model access in dashboard
3. Try different model
```

### "Insufficient Quota"

```
Solutions:
1. Add billing to API account
2. Increase spending limit
3. Check for free tier exhaustion
4. Upgrade to paid plan
```
