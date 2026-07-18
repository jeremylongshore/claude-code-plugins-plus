# PII Detection in Notion Content

Notion pages can contain PII in any property type — dedicated `email`/`phone_number`
properties, `people` references, and free-text embedded inside `rich_text` / `title`
values. Scan systematically across both structured property types and text content.

## TypeScript — full PII scanner

```typescript
import { Client } from '@notionhq/client';
import type { PageObjectResponse } from '@notionhq/client/build/src/api-endpoints';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// PII pattern matchers
const PII_PATTERNS = [
  { type: 'email',      pattern: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
  { type: 'phone_us',   pattern: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g },
  { type: 'phone_intl', pattern: /\+\d{1,3}[-.\s]?\d{4,14}/g },
  { type: 'ssn',        pattern: /\b\d{3}-\d{2}-\d{4}\b/g },
  { type: 'credit_card', pattern: /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/g },
  { type: 'ip_address', pattern: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g },
];

interface PIIFinding {
  propertyName: string;
  piiType: string;
  location: 'property' | 'content';
}

function scanPageForPII(page: PageObjectResponse): PIIFinding[] {
  const findings: PIIFinding[] = [];

  for (const [name, prop] of Object.entries(page.properties)) {
    // Direct PII property types
    if (prop.type === 'email' && prop.email) {
      findings.push({ propertyName: name, piiType: 'email', location: 'property' });
    }
    if (prop.type === 'phone_number' && prop.phone_number) {
      findings.push({ propertyName: name, piiType: 'phone', location: 'property' });
    }
    if (prop.type === 'people' && prop.people.length > 0) {
      findings.push({ propertyName: name, piiType: 'user_reference', location: 'property' });
    }

    // Text properties may contain embedded PII
    if (prop.type === 'rich_text' || prop.type === 'title') {
      const textParts = prop.type === 'title' ? prop.title : prop.rich_text;
      const text = textParts.map(t => t.plain_text).join('');

      for (const { type, pattern } of PII_PATTERNS) {
        // Reset regex lastIndex for each check
        pattern.lastIndex = 0;
        if (pattern.test(text)) {
          findings.push({ propertyName: name, piiType: type, location: 'property' });
        }
      }
    }
  }

  return findings;
}

// Scan an entire database for PII
async function auditDatabaseForPII(dbId: string) {
  const findings: { pageId: string; pageTitle: string; pii: PIIFinding[] }[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.databases.query({
      database_id: dbId,
      page_size: 100,
      start_cursor: cursor,
    });

    for (const page of response.results) {
      if (!('properties' in page)) continue;
      const pii = scanPageForPII(page as PageObjectResponse);
      if (pii.length > 0) {
        const titleProp = Object.values(page.properties)
          .find(p => p.type === 'title');
        const title = titleProp?.type === 'title'
          ? titleProp.title.map(t => t.plain_text).join('')
          : 'Untitled';
        findings.push({ pageId: page.id, pageTitle: title, pii });
      }
    }

    cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
  } while (cursor);

  return findings;
}
```

## Python — PII scanner

```python
import re
from notion_client import Client

client = Client(auth=os.environ["NOTION_TOKEN"])

PII_PATTERNS = [
    ("email", re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")),
    ("phone", re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
]

def scan_page_for_pii(page: dict) -> list[dict]:
    findings = []
    for name, prop in page["properties"].items():
        if prop["type"] == "email" and prop.get("email"):
            findings.append({"property": name, "type": "email"})
        if prop["type"] == "phone_number" and prop.get("phone_number"):
            findings.append({"property": name, "type": "phone"})
        if prop["type"] in ("rich_text", "title"):
            parts = prop.get("title" if prop["type"] == "title" else "rich_text", [])
            text = "".join(t["plain_text"] for t in parts)
            for pii_type, pattern in PII_PATTERNS:
                if pattern.search(text):
                    findings.append({"property": name, "type": pii_type})
    return findings
```

## Tuning notes

- The `g` flag makes the TypeScript patterns stateful — reset `pattern.lastIndex = 0`
  before each `.test()` (done above) or reuse fresh regex instances.
- Broad patterns produce false positives (e.g. any 9-digit run resembling an SSN). Tune
  patterns for your actual data and consider allowlists for known-safe fields.
- The database audit loops over pagination — always continue until `has_more` is false.
