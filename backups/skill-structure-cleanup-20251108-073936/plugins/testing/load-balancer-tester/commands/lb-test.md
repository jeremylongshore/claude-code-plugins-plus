---
description: Test load balancer traffic distribution and failover strategies
shortcut: lbt
---

# Load Balancer Tester

Test load balancing strategies including round-robin, least connections, weighted distribution, sticky sessions, and failover scenarios.

## What You Do

1. **Traffic Distribution Testing**: Verify requests are distributed correctly across backends
2. **Failover Testing**: Test behavior when backends fail
3. **Sticky Session Validation**: Ensure session affinity works
4. **Health Check Testing**: Verify health checks remove unhealthy backends

## Output Example

```javascript
describe('Load Balancer Tests', () => {
  it('distributes traffic evenly with round-robin', async () => {
    const requests = 100;
    const backends = ['backend1', 'backend2', 'backend3'];
    const distribution = await sendRequests(requests);

    backends.forEach(backend => {
      expect(distribution[backend]).toBeCloseTo(requests / backends.length, 10);
    });
  });

  it('handles backend failure gracefully', async () => {
    await stopBackend('backend2');
    const response = await fetch('/api/health');
    expect(response.status).toBe(200);
  });
});
```
