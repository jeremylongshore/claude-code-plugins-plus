# Production Error Monitoring for Notion Integrations

Structured error logging so you can track Notion-specific failures in your
monitoring tool (Sentry, Datadog, or platform logs). The classifier maps every
`@notionhq/client` error to a retryability flag and a concrete operator action.

## Error Classifier Module

```typescript
// src/notion-error-handler.ts — structured error reporting
import { isNotionClientError, APIErrorCode, ClientErrorCode } from '@notionhq/client';

interface NotionErrorReport {
  source: 'notion_api';
  code: string;
  status: number;
  message: string;
  retryable: boolean;
  action: string;
}

export function classifyNotionError(error: unknown): NotionErrorReport {
  if (!isNotionClientError(error)) {
    return {
      source: 'notion_api',
      code: 'unknown',
      status: 500,
      message: error instanceof Error ? error.message : String(error),
      retryable: false,
      action: 'investigate — non-Notion error in API path',
    };
  }

  const report: NotionErrorReport = {
    source: 'notion_api',
    code: error.code,
    status: error.status,
    message: error.message,
    retryable: false,
    action: '',
  };

  switch (error.code) {
    case APIErrorCode.RateLimited:
      report.retryable = true;
      report.action = 'back off — increase cache TTL or reduce polling frequency';
      break;
    case APIErrorCode.Unauthorized:
      report.retryable = false;
      report.action = 'rotate NOTION_TOKEN — token expired or was revoked';
      break;
    case APIErrorCode.ObjectNotFound:
      report.retryable = false;
      report.action = 'check integration permissions — page/database not shared with integration';
      break;
    case APIErrorCode.InternalServerError:
    case APIErrorCode.ServiceUnavailable:
      report.retryable = true;
      report.action = 'retry with exponential backoff — Notion is having issues';
      break;
    case APIErrorCode.ValidationError:
      report.retryable = false;
      report.action = 'fix request payload — check filter syntax and property names';
      break;
    default:
      report.action = 'check Notion API status page and SDK changelog';
  }

  return report;
}

export function logNotionError(error: unknown, context: Record<string, string> = {}): void {
  const report = classifyNotionError(error);
  console.error(JSON.stringify({ ...report, ...context, timestamp: new Date().toISOString() }));
}
```

## Wiring Into API Routes

```typescript
} catch (error) {
  logNotionError(error, { route: '/api/notion/query', databaseId });
  // ... return error response
}
```
