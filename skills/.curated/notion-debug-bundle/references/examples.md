# Notion Debug Bundle — Examples and Redaction Rules

Focused snippets for the recurring gotchas that show up in support tickets:
token format, page ID normalization, and what is safe to include in a bundle.

## Token Format Validation

```bash
# Valid formats (all start with ntn_):
# ntn_abc123...  (internal integration token)
# Old format (secret_xyz...) is deprecated — regenerate in notion.so/my-integrations
echo "Token prefix: ${NOTION_TOKEN:0:4}"
```

## Page ID Normalization

```typescript
// Notion accepts both formats — but URLs use dashless form
const withDashes    = '12345678-1234-1234-1234-123456789abc';
const withoutDashes = '123456781234123412341234567890abc';

// The SDK handles both, but for consistency:
const normalized = rawId.replace(/-/g, '');
```

## Redaction Rules

**ALWAYS REDACT:** Integration tokens (`ntn_*`), OAuth client secrets, user emails, page content

**SAFE TO INCLUDE:** Error codes/messages, HTTP status codes, latencies, SDK versions, platform status, page/database IDs (non-sensitive metadata)
