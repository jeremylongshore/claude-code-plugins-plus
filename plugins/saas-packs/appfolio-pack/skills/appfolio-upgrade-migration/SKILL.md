---
name: appfolio-upgrade-migration
description: |
  Migrate between AppFolio API versions and handle endpoint changes.
  Trigger: "appfolio upgrade".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# appfolio upgrade migration | sed 's/\b\(.\)/\u\1/g'

## API Version Migration
```typescript
// Adapter pattern for API version changes
class AppFolioVersionAdapter {
  private version: "v1" | "v2";
  private client: any;

  constructor(version: "v1" | "v2" = "v1") {
    this.version = version;
  }

  async getProperties(): Promise<any[]> {
    if (this.version === "v2") {
      // v2 may return paginated results
      return this.paginatedGet("/properties");
    }
    return (await this.client.get("/properties")).data;
  }

  private async paginatedGet(path: string): Promise<any[]> {
    const results: any[] = [];
    let cursor: string | null = null;
    do {
      const { data } = await this.client.get(path, { params: { cursor } });
      results.push(...data.results);
      cursor = data.next_cursor;
    } while (cursor);
    return results;
  }
}
```

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)
