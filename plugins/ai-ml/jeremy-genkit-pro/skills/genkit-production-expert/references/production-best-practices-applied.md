# Production Best Practices Applied

## Production Best Practices Applied

### 1. Schema Validation

- All inputs/outputs use Zod (TS), Pydantic (Python), or structs (Go)
- Prevents runtime errors from malformed data

### 2. Error Handling

```typescript
try {
  const result = await ai.generate({...});
  return result;
} catch (error) {
  if (error.code === 'SAFETY_BLOCK') {
    // Handle safety filters
  } else if (error.code === 'QUOTA_EXCEEDED') {
    // Handle rate limits
  }
  throw error;
}
```

### 3. Cost Optimization

- Context caching for repeated prompts
- Token usage monitoring
- Temperature tuning for use case
- Model selection (Flash vs Pro)

### 4. Monitoring

- OpenTelemetry tracing enabled
- Custom span attributes
- Firebase Console integration
- Alert configuration

### 5. Security

- Environment variable management
- API key rotation support
- Input sanitization
- Output filtering
