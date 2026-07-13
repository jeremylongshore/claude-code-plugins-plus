# Tips For Effective Rules

## Tips for Effective Rules

### Be Specific

```yaml
# Vague (less effective)
rules:
  - Write good code
  - Handle errors

# Specific (more effective)
rules:
  - Wrap async operations in try/catch
  - Return typed error responses using ApiError class
  - Log errors with context using logger.error()
```

### Include Examples

```yaml
# Examples help AI understand your patterns
error-handling-example: |
  try {
    const result = await someOperation();
    return { success: true, data: result };
  } catch (error) {
    logger.error('Operation failed', { error, context });
    throw new ApiError('OPERATION_FAILED', 500);
  }
```

### Reference Project Files

```yaml
context:
  reference-files:
    - See @lib/api-client.ts for API patterns
    - See @components/Button.tsx for component structure
    - See @hooks/useAuth.ts for hook patterns
```
