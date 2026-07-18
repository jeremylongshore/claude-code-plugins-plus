# Klaviyo Error Catalog

Full reference for each Klaviyo API status code: the actual JSON:API error
payload, root causes, and the fix. Match the status code you pulled in Step 1
against the section below.

---

## 400 -- Bad Request (Validation Error)

**Actual Klaviyo response:**

```json
{
  "errors": [{
    "id": "abc-123",
    "code": "invalid",
    "title": "Invalid input.",
    "detail": "The email field is required.",
    "source": { "pointer": "/data/attributes/email" }
  }]
}
```

**Common causes:**

- Missing required field (email, metric name, list name)
- Invalid phone number format (must be E.164: `+15551234567`)
- Invalid filter syntax in query params
- Wrong `type` value in JSON:API payload
- Sending `snake_case` instead of `camelCase` (SDK uses camelCase)

**Fix:**

```typescript
// Wrong: snake_case
{ first_name: 'Jane', phone_number: '+155...' }

// Right: camelCase (SDK convention)
{ firstName: 'Jane', phoneNumber: '+15551234567' } // E.164 sample number
```

---

## 401 -- Unauthorized

**Actual response:**

```json
{
  "errors": [{
    "code": "not_authenticated",
    "title": "Authentication credentials were not provided.",
    "detail": "Missing or invalid Authorization header."
  }]
}
```

**Root causes:**

1. Missing `KLAVIYO_PRIVATE_KEY` environment variable
2. Using a public key (6 chars) instead of private key (`pk_*`)
3. API key was revoked or rotated

**Fix:**

```bash
# Verify key is set and starts with pk_
echo $KLAVIYO_PRIVATE_KEY | head -c 3
# Should print: pk_

# Test with cURL
curl -s -w "%{http_code}" -o /dev/null \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/accounts/"
```

---

## 403 -- Forbidden (Missing Scope)

**Actual response:**

```json
{
  "errors": [{
    "code": "permission_denied",
    "title": "You do not have permission to perform this action.",
    "detail": "The API key does not have the required scope: profiles:write"
  }]
}
```

**Fix:** Generate a new API key with the required scope at **Settings > API Keys > Create Private API Key**.

| Endpoint | Required Scope |
|----------|---------------|
| `POST /api/profiles/` | `profiles:write` |
| `GET /api/segments/` | `segments:read` |
| `POST /api/events/` | `events:write` |
| `POST /api/campaigns/` | `campaigns:write` |
| `POST /api/data-privacy-deletion-jobs/` | `data-privacy:write` |

---

## 404 -- Not Found

**Typical causes:**

- Wrong resource ID (profile, list, segment, campaign)
- Using v1/v2 URL paths instead of new API (`/api/v2/` is dead, use `/api/`)
- Resource was deleted

**Fix:**

```typescript
// Verify the resource exists first
const lists = await listsApi.getLists();
const targetList = lists.body.data.find(l => l.attributes.name === 'Newsletter');
if (!targetList) throw new Error('List not found');
```

---

## 409 -- Conflict (Duplicate)

**Actual response:**

```json
{
  "errors": [{
    "code": "duplicate",
    "title": "Conflict.",
    "detail": "A profile already exists with the email customer@example.com"
  }]
}
```

**Fix:** Use `createOrUpdateProfile` (upsert) instead of `createProfile`:

```typescript
// This handles both create and update
await profilesApi.createOrUpdateProfile({
  data: {
    type: 'profile' as any,
    attributes: { email: 'customer@example.com', firstName: 'Updated' },
  },
});
```

---

## 429 -- Rate Limited

**Headers on 429 response:**

```
Retry-After: 10
```

**Klaviyo rate limits (per-account, fixed window):**

| Window | Limit |
|--------|-------|
| Burst (1 second) | 75 requests |
| Steady (1 minute) | 700 requests |

**Note:** When rate limited, `RateLimit-Remaining` and `RateLimit-Reset` headers are NOT returned. Only `Retry-After` (integer seconds) is present.

**Fix:** Honor `Retry-After` header:

```typescript
catch (error: any) {
  if (error.status === 429) {
    const retryAfter = parseInt(error.headers?.['retry-after'] || '10');
    console.log(`Rate limited. Waiting ${retryAfter}s...`);
    await new Promise(r => setTimeout(r, retryAfter * 1000));
    // Retry the request
  }
}
```

---

## 500/503 -- Klaviyo Server Error

**Fix:**

1. Check [Klaviyo Status Page](https://status.klaviyo.com)
2. Retry with exponential backoff (see `klaviyo-rate-limits`)
3. If persistent, check Klaviyo's [changelog](https://developers.klaviyo.com/en/docs/changelog_) for known issues
