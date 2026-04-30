---
name: miro-migration-deep-dive
description: "Execute major Miro migrations \u2014 migrate boards between teams/orgs,\n\
  export board content to external systems, import data into Miro,\nand re-platform\
  \ from competing whiteboard tools using REST API v2.\nTrigger with phrases like\
  \ \"migrate miro\", \"miro migration\",\n\"export miro boards\", \"import to miro\"\
  , \"miro data migration\".\n"
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- miro
- migration
- data-export
compatibility: Designed for Claude Code
---
# Miro Migration Deep Dive

## Overview

Comprehensive guide for migrating Miro boards between teams and organizations, updating
from REST API v1 to v2, and re-platforming from competing whiteboard tools (Lucidchart,
FigJam). Covers board content export with cursor pagination, bulk import with rate-limit
aware queuing, widget API changes between v1 and v2, and the new app framework patterns.
Typical migration scope: dozens to thousands of boards with connectors, tags, and members.

## Migration Assessment

```typescript
// Scan current integration for deprecated v1 patterns and board inventory
async function assessMigration(teamId: string) {
  const boards = await miroFetch(`/v2/boards?team_id=${teamId}&limit=50`);
  let totalItems = 0;
  for (const board of boards.data) {
    const items = await miroFetch(`/v2/boards/${board.id}/items?limit=1`);
    totalItems += items.total ?? 0;
  }
  console.log(`Team ${teamId}: ${boards.data.length} boards, ~${totalItems} items`);
  console.log('API version: v2 (v1 deprecated 2024-01)');
  console.log('Widget types to migrate: sticky_note, shape, card, text, frame, image, connector');
  return { boardCount: boards.data.length, totalItems };
}
```

## Step-by-Step Migration

### Phase 1: Prepare — Export Source Boards

Export every item on a board to a structured JSON file with cursor-paginated reads:

```typescript
interface BoardExport {
  exportedAt: string;
  board: { id: string; name: string; description: string; owner: { id: string; name: string } };
  items: any[]; connectors: any[]; tags: any[]; members: any[];
}

async function exportBoard(boardId: string): Promise<BoardExport> {
  const board = await miroFetch(`/v2/boards/${boardId}`);
  const items = await paginateAll(`/v2/boards/${boardId}/items`);
  const connectors = await paginateAll(`/v2/boards/${boardId}/connectors`);
  const tags = await miroFetch(`/v2/boards/${boardId}/tags`);
  const members = await miroFetch(`/v2/boards/${boardId}/members?limit=100`);
  return {
    exportedAt: new Date().toISOString(),
    board: { id: board.id, name: board.name, description: board.description ?? '',
      owner: { id: board.owner?.id, name: board.owner?.name } },
    items: items.map(i => ({ id: i.id, type: i.type, data: i.data, style: i.style,
      position: i.position, geometry: i.geometry, parentId: i.parent?.id })),
    connectors, tags: tags.data ?? [], members: members.data ?? [],
  };
}

async function paginateAll(baseUrl: string): Promise<any[]> {
  const all: any[] = [];
  let cursor: string | undefined;
  do {
    const params = new URLSearchParams({ limit: '50' });
    if (cursor) params.set('cursor', cursor);
    const page = await miroFetch(`${baseUrl}?${params}`);
    all.push(...page.data);
    cursor = page.cursor;
  } while (cursor);
  return all;
}
```

### Phase 2: Migrate — Import to Target Board

Recreate exported items on a new board with rate-limit aware queuing (frames first,
then other items, then connectors, then tags):

```typescript
import PQueue from 'p-queue';

async function importToBoard(targetBoardId: string, exportData: BoardExport): Promise<{
  created: number; failed: number; idMap: Map<string, string>;
}> {
  const queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 8 });
  const idMap = new Map<string, string>();
  let created = 0, failed = 0;

  const endpointMap: Record<string, string> = {
    sticky_note: 'sticky_notes', shape: 'shapes', card: 'cards', text: 'texts',
    frame: 'frames', image: 'images', document: 'documents', app_card: 'app_cards',
  };

  // Frames first (containers), then everything else
  const sorted = [...exportData.items].sort((a, b) =>
    (a.type === 'frame' ? 0 : 1) - (b.type === 'frame' ? 0 : 1));

  for (const item of sorted) {
    await queue.add(async () => {
      try {
        const ep = endpointMap[item.type];
        if (!ep) throw new Error(`Unsupported: ${item.type}`);
        const newItem = await miroFetch(`/v2/boards/${targetBoardId}/${ep}`, 'POST', {
          data: item.data, style: item.style, position: item.position, geometry: item.geometry,
        });
        idMap.set(item.id, newItem.id);
        created++;
      } catch { failed++; }
    });
  }
  await queue.onIdle();

  // Reconnect connectors using new IDs
  for (const conn of exportData.connectors) {
    const startId = idMap.get(conn.startItem?.id), endId = idMap.get(conn.endItem?.id);
    if (!startId || !endId) continue;
    await queue.add(async () => {
      await miroFetch(`/v2/boards/${targetBoardId}/connectors`, 'POST', {
        startItem: { id: startId }, endItem: { id: endId },
        style: conn.style, shape: conn.shape,
      }).catch(() => { failed++; });
      created++;
    });
  }
  await queue.onIdle();
  return { created, failed, idMap };
}
```

### Phase 3: Validate — Compare Source and Target

```typescript
async function validateMigration(sourceBoardId: string, targetBoardId: string) {
  const srcItems = await paginateAll(`/v2/boards/${sourceBoardId}/items`);
  const tgtItems = await paginateAll(`/v2/boards/${targetBoardId}/items`);
  const srcConn = await paginateAll(`/v2/boards/${sourceBoardId}/connectors`);
  const tgtConn = await paginateAll(`/v2/boards/${targetBoardId}/connectors`);

  const checks = [
    { name: 'Item count', pass: tgtItems.length >= srcItems.length * 0.95,
      detail: `${tgtItems.length}/${srcItems.length}` },
    { name: 'Connectors', pass: tgtConn.length >= srcConn.length * 0.9,
      detail: `${tgtConn.length}/${srcConn.length}` },
  ];
  console.log(checks.map(c => `${c.pass ? 'PASS' : 'FAIL'} ${c.name}: ${c.detail}`).join('\n'));
  return checks.every(c => c.pass);
}
```

## Rollback Plan

```bash
# Delete the target board entirely (preserves source untouched)
curl -X DELETE "https://api.miro.com/v2/boards/${TARGET_BOARD_ID}" \
  -H "Authorization: Bearer $MIRO_TOKEN"

# Or delete only imported items by ID list (saved during import)
cat imported-ids.txt | while read id; do
  curl -X DELETE "https://api.miro.com/v2/boards/${TARGET_BOARD_ID}/items/${id}" \
    -H "Authorization: Bearer $MIRO_TOKEN"
done

echo "Rollback complete — source board unchanged"
```

## Migration Checklist

- [ ] Audit source boards: count items, connectors, tags, members
- [ ] Export all source boards to JSON backup files
- [ ] Create target boards in destination team/org
- [ ] Run import with rate-limit aware queuing
- [ ] Validate item counts (95%+ threshold)
- [ ] Validate connector integrity (90%+ threshold)
- [ ] Re-share boards with correct member permissions
- [ ] Update any external links pointing to old board URLs
- [ ] Run user acceptance testing with board owners
- [ ] Decommission source boards after 30-day grace period

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `429 Too Many Requests` | Rate limit exceeded | Reduce PQueue concurrency to 2 |
| Connector creation fails | Referenced item missing | Verify idMap has both start/end IDs |
| Image items 404 | External URL expired | Re-upload image or use placeholder |
| Position overlap on target | No offset applied | Pass `offsetX`/`offsetY` to import |
| Tag 409 Conflict | Duplicate tag title | Catch 409, query existing tag by title |

## Resources

- [REST API Reference](https://developers.miro.com/docs/rest-api-reference-guide)
- [Board Items API](https://developers.miro.com/docs/board-items)
- [v1 to v2 Migration Guide](https://developers.miro.com/docs/rest-api-comparison-guide)
- [Miro App Examples](https://github.com/miroapp/app-examples)

## Next Steps

For starting a new Miro integration from scratch, see `miro-install-auth`. For
board sharing and collaboration workflows, see `miro-core-workflow-b`.
