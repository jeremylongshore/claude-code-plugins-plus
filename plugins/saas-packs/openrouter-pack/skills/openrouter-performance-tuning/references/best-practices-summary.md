# Best Practices Summary

## Best Practices Summary

```python
PERFORMANCE_TIPS = """
1. Connection Pooling
   - Use persistent HTTP client
   - Enable keepalive connections
   - Set appropriate connection limits

2. Model Selection
   - Use claude-3-haiku for speed
   - Use gpt-3.5-turbo for balance
   - Reserve larger models for complex tasks

3. Request Optimization
   - Minimize prompt length
   - Set appropriate max_tokens
   - Use streaming for perceived speed

4. Caching
   - Cache identical requests
   - Consider semantic caching
   - Implement TTL-based expiration

5. Async Processing
   - Use async for concurrent requests
   - Batch similar requests
   - Implement rate limiting

6. Monitoring
   - Track latency by model
   - Monitor token usage
   - Set up alerting for degradation
"""
```
