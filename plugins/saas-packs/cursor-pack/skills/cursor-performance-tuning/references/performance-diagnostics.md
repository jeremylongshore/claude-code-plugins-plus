# Performance Diagnostics

## Performance Diagnostics

### Checking Performance

```
1. Process Explorer
   Help > Process Explorer
   - View CPU/memory per process
   - Identify heavy extensions
   - Monitor extension hosts

2. Developer Tools
   Help > Toggle Developer Tools
   - Performance tab
   - Memory profiling
   - Network requests

3. Startup Performance
   Cmd+Shift+P > "Startup Performance"
   - Extension load times
   - Activation events
```

### Common Performance Issues

```
Symptoms → Likely Cause:

Slow startup → Many extensions, large workspace
Laggy typing → Heavy extensions, large files
High CPU → Runaway extension, indexing
High memory → Many open files, large project
Slow completions → Network latency, model choice
```
