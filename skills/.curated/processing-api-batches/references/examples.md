# API Batch Processing Examples

## Synchronous Batch Endpoint (Express)

```javascript
// routes/batch.js
app.post('/batch', authenticateToken, async (req, res) => {
  const { operations } = req.body;

  if (!Array.isArray(operations) || operations.length > 1000) {
    return res.status(413).json({
      detail: `Batch size ${operations?.length} exceeds maximum of 1000`
    });
  }

  if (operations.length <= 100) {
    const results = await processBatchSync(operations);
    return res.status(207).json(results);
  }

  const batchId = crypto.randomUUID();
  await redis.set(`batch:${batchId}`, JSON.stringify({
    status: 'processing', total: operations.length, completed: 0, failed: 0
  }));
  batchQueue.add({ batchId, operations });

  res.status(202).json({
    batchId,
    statusUrl: `/batch/${batchId}/status`,
    total: operations.length
  });
});

async function processBatchSync(operations) {
  const results = [];
  for (const op of operations) {
    try {
      const result = await executeOperation(op);
      results.push({ id: op.id, status: 'success', result });
    } catch (err) {
      results.push({ id: op.id, status: 'error', error: err.message });
    }
  }
  return {
    total: operations.length,
    succeeded: results.filter(r => r.status === 'success').length,
    failed: results.filter(r => r.status === 'error').length,
    results
  };
}
```

## Batch Request / Response Format

```json
// Request
{
  "operations": [
    { "id": "op1", "method": "POST", "path": "/users", "body": { "name": "Alice" } },
    { "id": "op2", "method": "PUT", "path": "/users/42", "body": { "name": "Bob" } },
    { "id": "op3", "method": "DELETE", "path": "/products/99" }
  ]
}

// 207 Multi-Status Response
{
  "total": 3,
  "succeeded": 2,
  "failed": 1,
  "results": [
    { "id": "op1", "status": "success", "result": { "userId": 101 } },
    { "id": "op2", "status": "success", "result": { "updated": true } },
    { "id": "op3", "status": "error", "error": "Product 99 not found" }
  ]
}
```

## Async Batch Worker with Concurrency Control

```javascript
// batch/worker.js
const { Worker } = require('bullmq');
const pLimit = require('p-limit');
const limit = pLimit(10);

const worker = new Worker('batch', async (job) => {
  const { batchId, operations } = job.data;
  const results = [];

  const tasks = operations.map((op) =>
    limit(async () => {
      try {
        const result = await executeOperation(op);
        results.push({ id: op.id, status: 'success', result });
      } catch (err) {
        results.push({ id: op.id, status: 'error', error: err.message });
      }
      const completed = results.filter(r => r.status === 'success').length;
      const failed = results.filter(r => r.status === 'error').length;
      await redis.set(`batch:${batchId}`, JSON.stringify({
        status: 'processing', total: operations.length,
        completed, failed, progress: (completed + failed) / operations.length
      }));
    })
  );

  await Promise.all(tasks);
  await redis.set(`batch:${batchId}`, JSON.stringify({
    status: 'completed',
    total: operations.length,
    completed: results.filter(r => r.status === 'success').length,
    failed: results.filter(r => r.status === 'error').length,
    progress: 1.0,
    results
  }), 'EX', 86400);
});
```

## Progress Polling

```bash
# Submit large batch -> 202 Accepted
curl -X POST http://localhost:3000/batch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"operations": [... 500 items ...]}'
# {"batchId":"abc-123","statusUrl":"/batch/abc-123/status","total":500}

# Poll progress
curl http://localhost:3000/batch/abc-123/status -H "Authorization: Bearer $TOKEN"
# {"status":"processing","total":500,"completed":327,"failed":2,"progress":0.658}
```

## Idempotent Batch Retry (Python)

```python
import httpx, time

def submit_batch_with_retry(operations, token, max_retries=3):
    for op in operations:
        if 'idempotencyKey' not in op:
            op['idempotencyKey'] = f"idem_{op['id']}_{int(time.time())}"

    result = None
    for attempt in range(max_retries):
        resp = httpx.post(
            'http://localhost:3000/batch',
            json={'operations': operations},
            headers={'Authorization': f'Bearer {token}'}
        )
        if resp.status_code == 207:
            result = resp.json()
            failed_ops = [
                op for op, r in zip(operations, result['results'])
                if r['status'] == 'error' and r.get('retryable', True)
            ]
            if not failed_ops:
                return result
            operations = failed_ops
            continue
        resp.raise_for_status()
    return result
```

## Bulk CSV Import

```javascript
app.post('/batch/users/import', upload.single('file'), async (req, res) => {
  const records = [];
  const parser = csvParser.parse(req.file.buffer.toString(), {
    columns: true, skip_empty_lines: true
  });
  for await (const record of parser) {
    records.push({
      id: `row-${records.length}`,
      method: 'POST',
      path: '/users',
      body: { name: record.name, email: record.email, role: record.role }
    });
  }
  if (records.length > 5000) {
    return res.status(413).json({ detail: 'CSV exceeds 5000 row limit' });
  }
  const batchId = crypto.randomUUID();
  batchQueue.add({ batchId, operations: records });
  res.status(202).json({ batchId, total: records.length });
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
