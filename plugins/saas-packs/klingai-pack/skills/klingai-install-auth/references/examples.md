# Kling AI Authentication Examples

## Environment Setup

```bash
# .env
KLINGAI_API_KEY=your_api_key_here
```

## cURL Verification

```bash
curl -X GET "https://api.klingai.com/v1/account/info" \
  -H "Authorization: Bearer $KLINGAI_API_KEY" \
  -H "Content-Type: application/json"
# {"code":0,"data":{"account_id":"acc_123","remaining_credits":1000}}
```

## Node.js Client

```typescript
const klingClient = axios.create({
  baseURL: 'https://api.klingai.com/v1',
  headers: { 'Authorization': `Bearer ${process.env.KLINGAI_API_KEY}` },
});
const info = await klingClient.get('/account/info');
console.log('Credits:', info.data.data.remaining_credits);
```

## Python Client

```python
import os, httpx
headers = {"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"}
r = httpx.get("https://api.klingai.com/v1/account/info", headers=headers)
r.raise_for_status()
print(r.json()["data"])
```

## Error Codes

| Status | Meaning | Fix |
|--------|---------|-----|
| 401 | Invalid key | Check KLINGAI_API_KEY |
| 403 | No permissions | Upgrade plan |
| 429 | Rate limited | Add backoff |
