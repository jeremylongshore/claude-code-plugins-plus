---
name: miro-migration-deep-dive
description: |
  Execute major Miro migrations — migrate boards between teams/orgs,
  export board content to external systems, import data into Miro,
  and re-platform from competing whiteboard tools using REST API v2.
  Trigger with phrases like "migrate miro", "miro migration",
  "export miro boards", "import to miro", "miro data migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, migration, data-export]
compatible-with: claude-code
---

# Miro Migration Deep Dive

## Overview

Comprehensive migration strategies for Miro REST API v2: export entire board content, import structured data into boards, migrate between teams/organizations, and re-platform from competing whiteboard tools.

## Migration Types

| Type | Complexity | Duration | Approach |
|------|-----------|----------|----------|
| Export board content | Low | Minutes | Read all items, save as JSON |
| Import data into board | Medium | Minutes | Batch create items via API |
| Move boards between teams | Medium | Hours | Copy + re-share |
| Re-platform (Lucidchart/FigJam) | High | Days–Weeks | Export → transform → import |
| Full org migration | High | Weeks | SCIM + board migration + member mapping |

## Board Content Export

Export every item on a board to a structured JSON file:

```typescript
interface BoardExport {
  exportedAt: string;
  board: {
    id: string;
    name: string;
    description: string;
    owner: { id: string; name: string };
  };
  items: ExportedItem[];
  connectors: ExportedConnector[];
  tags: ExportedTag[];
  members: ExportedMember[];
}

async function exportBoard(boardId: string): Promise<BoardExport> {
  // Get board metadata
  const board = await miroFetch(`/v2/boards/${boardId}`);

  // Get all items (cursor-paginated)
  const items: any[] = [];
  let cursor: string | undefined;
  do {
    const params = new URLSearchParams({ limit: '50' });
    if (cursor) params.set('cursor', cursor);
    const page = await miroFetch(`/v2/boards/${boardId}/items?${params}`);
    items.push(...page.data);
    cursor = page.cursor;
  } while (cursor);

  // Get all connectors
  const connectors: any[] = [];
  cursor = undefined;
  do {
    const params = new URLSearchParams({ limit: '50' });
    if (cursor) params.set('cursor', cursor);
    const page = await miroFetch(`/v2/boards/${boardId}/connectors?${params}`);
    connectors.push(...page.data);
    cursor = page.cursor;
  } while (cursor);

  // Get all tags
  const tags = await miroFetch(`/v2/boards/${boardId}/tags`);

  // Get board members
  const members = await miroFetch(`/v2/boards/${boardId}/members?limit=100`);

  return {
    exportedAt: new Date().toISOString(),
    board: {
      id: board.id,
      name: board.name,
      description: board.description ?? '',
      owner: { id: board.owner?.id, name: board.owner?.name },
    },
    items: items.map(normalizeItem),
    connectors: connectors.map(normalizeConnector),
    tags: tags.data ?? [],
    members: members.data ?? [],
  };
}

function normalizeItem(item: any) {
  return {
    id: item.id,
    type: item.type,
    data: item.data,
    style: item.style,
    position: item.position,
    geometry: item.geometry,
    parentId: item.parent?.id,
    createdAt: item.createdAt,
    createdBy: item.createdBy?.id,
  };
}
```

## Import Data into a Board

Recreate exported items on a new board:

```typescript
import PQueue from 'p-queue';

interface ImportResult {
  created: number;
  failed: number;
  errors: Array<{ item: any; error: string }>;
  idMap: Map<string, string>;  // Old ID → New ID
}

async function importToBoard(
  targetBoardId: string,
  exportData: BoardExport,
  options: { offsetX?: number; offsetY?: number } = {}
): Promise<ImportResult> {
  const queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 8 });
  const result: ImportResult = { created: 0, failed: 0, errors: [], idMap: new Map() };

  // Phase 1: Create items (excluding frames first, then frames)
  const frames = exportData.items.filter(i => i.type === 'frame');
  const nonFrames = exportData.items.filter(i => i.type !== 'frame');

  // Create frames first (they contain other items)
  for (const frame of frames) {
    await queue.add(async () => {
      try {
        const newItem = await createItemByType(targetBoardId, frame, options);
        result.idMap.set(frame.id, newItem.id);
        result.created++;
      } catch (err: any) {
        result.failed++;
        result.errors.push({ item: frame, error: err.message });
      }
    });
  }
  await queue.onIdle();

  // Then create other items
  for (const item of nonFrames) {
    await queue.add(async () => {
      try {
        const newItem = await createItemByType(targetBoardId, item, options);
        result.idMap.set(item.id, newItem.id);
        result.created++;
      } catch (err: any) {
        result.failed++;
        result.errors.push({ item, error: err.message });
      }
    });
  }
  await queue.onIdle();

  // Phase 2: Recreate connectors using new IDs
  for (const connector of exportData.connectors) {
    const newStartId = result.idMap.get(connector.startItem?.id);
    const newEndId = result.idMap.get(connector.endItem?.id);
    if (!newStartId || !newEndId) continue;

    await queue.add(async () => {
      try {
        await miroFetch(`/v2/boards/${targetBoardId}/connectors`, 'POST', {
          startItem: { id: newStartId },
          endItem: { id: newEndId },
          captions: connector.captions,
          style: connector.style,
          shape: connector.shape,
        });
        result.created++;
      } catch (err: any) {
        result.errors.push({ item: connector, error: err.message });
      }
    });
  }
  await queue.onIdle();

  // Phase 3: Recreate tags
  for (const tag of exportData.tags) {
    await queue.add(async () => {
      try {
        await miroFetch(`/v2/boards/${targetBoardId}/tags`, 'POST', {
          title: tag.title,
          fillColor: tag.fillColor,
        });
      } catch (err: any) {
        // Duplicate tag titles return 409 — safe to ignore
        if (!err.message?.includes('409')) {
          result.errors.push({ item: tag, error: err.message });
        }
      }
    });
  }
  await queue.onIdle();

  return result;
}

async function createItemByType(
  boardId: string,
  item: any,
  options: { offsetX?: number; offsetY?: number }
) {
  const position = {
    x: (item.position?.x ?? 0) + (options.offsetX ?? 0),
    y: (item.position?.y ?? 0) + (options.offsetY ?? 0),
  };

  const endpointMap: Record<string, string> = {
    sticky_note: 'sticky_notes',
    shape: 'shapes',
    card: 'cards',
    text: 'texts',
    frame: 'frames',
    image: 'images',
    document: 'documents',
    embed: 'embeds',
    app_card: 'app_cards',
  };

  const endpoint = endpointMap[item.type];
  if (!endpoint) throw new Error(`Unsupported item type: ${item.type}`);

  return miroFetch(`/v2/boards/${boardId}/${endpoint}`, 'POST', {
    data: item.data,
    style: item.style,
    position,
    geometry: item.geometry,
  });
}
```

## Board Duplication Between Teams

```typescript
async function duplicateBoard(
  sourceBoardId: string,
  targetTeamId: string,
  newName: string,
): Promise<{ newBoardId: string; importResult: ImportResult }> {
  // Step 1: Export source board
  console.log('Exporting source board...');
  const exportData = await exportBoard(sourceBoardId);

  // Step 2: Create new board in target team
  console.log('Creating target board...');
  const newBoard = await miroFetch('/v2/boards', 'POST', {
    name: newName,
    description: exportData.board.description,
    teamId: targetTeamId,
  });

  // Step 3: Import all content
  console.log('Importing items...');
  const importResult = await importToBoard(newBoard.id, exportData);

  console.log(`Done! Created ${importResult.created} items, ${importResult.failed} failed`);
  return { newBoardId: newBoard.id, importResult };
}
```

## CSV/Spreadsheet Import

Import structured data (from spreadsheets, Jira, etc.) as Miro items:

```typescript
interface CsvRow {
  title: string;
  description?: string;
  category?: string;
  priority?: string;
}

async function importCsvAsCards(
  boardId: string,
  rows: CsvRow[],
  layout: 'grid' | 'column' = 'grid'
): Promise<ImportResult> {
  const result: ImportResult = { created: 0, failed: 0, errors: [], idMap: new Map() };
  const queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 8 });

  // Color mapping for categories
  const categoryColors: Record<string, string> = {
    bug: '#ff6b6b',
    feature: '#2d9bf0',
    improvement: '#51cf66',
    default: '#868e96',
  };

  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const x = layout === 'grid' ? (i % 5) * 300 : 0;
    const y = layout === 'grid' ? Math.floor(i / 5) * 200 : i * 200;

    await queue.add(async () => {
      try {
        const card = await miroFetch(`/v2/boards/${boardId}/cards`, 'POST', {
          data: {
            title: row.title,
            description: row.description ?? '',
          },
          style: {
            cardTheme: categoryColors[row.category?.toLowerCase() ?? 'default'] ?? categoryColors.default,
          },
          position: { x, y },
        });

        // Add priority as tag
        if (row.priority) {
          try {
            const tag = await miroFetch(`/v2/boards/${boardId}/tags`, 'POST', {
              title: row.priority,
              fillColor: row.priority === 'High' ? 'red' : 'yellow',
            });
            await miroFetch(`/v2/boards/${boardId}/items/${card.id}/tags`, 'POST', {
              tagId: tag.id,
            });
          } catch {
            // Tag might already exist — acceptable
          }
        }

        result.created++;
      } catch (err: any) {
        result.failed++;
        result.errors.push({ item: row, error: err.message });
      }
    });
  }

  await queue.onIdle();
  return result;
}
```

## Migration Validation

```typescript
async function validateMigration(
  sourceBoardId: string,
  targetBoardId: string,
): Promise<ValidationReport> {
  const sourceItems = await fetchAllItems(sourceBoardId);
  const targetItems = await fetchAllItems(targetBoardId);

  const sourceConnectors = await fetchAllConnectors(sourceBoardId);
  const targetConnectors = await fetchAllConnectors(targetBoardId);

  const checks = [
    {
      name: 'Item count match',
      pass: targetItems.length >= sourceItems.length * 0.95,  // 95% threshold
      detail: `Source: ${sourceItems.length}, Target: ${targetItems.length}`,
    },
    {
      name: 'Item types match',
      pass: compareTypeCounts(sourceItems, targetItems),
      detail: getTypeCountDiff(sourceItems, targetItems),
    },
    {
      name: 'Connectors migrated',
      pass: targetConnectors.length >= sourceConnectors.length * 0.9,
      detail: `Source: ${sourceConnectors.length}, Target: ${targetConnectors.length}`,
    },
  ];

  return {
    passed: checks.every(c => c.pass),
    checks,
    summary: `${checks.filter(c => c.pass).length}/${checks.length} checks passed`,
  };
}
```

## Rollback Plan

```typescript
async function rollbackMigration(
  targetBoardId: string,
  importResult: ImportResult,
): Promise<void> {
  console.log(`Rolling back: deleting ${importResult.created} items from ${targetBoardId}`);

  const queue = new PQueue({ concurrency: 5 });
  for (const [, newId] of importResult.idMap) {
    queue.add(async () => {
      await miroFetch(`/v2/boards/${targetBoardId}/items/${newId}`, 'DELETE').catch(() => {});
    });
  }
  await queue.onIdle();

  console.log('Rollback complete');
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limited during import | Too many items | Reduce concurrency, increase interval |
| Connector fails | Referenced item wasn't created | Check idMap for missing mappings |
| Image URL 404 | External image no longer available | Skip or replace with placeholder |
| Position overlap | No offset applied | Use `offsetX`/`offsetY` options |
| Tag duplicate | Tag title already exists | Catch 409, reuse existing tag |

## Resources

- [REST API Reference Guide](https://developers.miro.com/docs/rest-api-reference-guide)
- [Board Items](https://developers.miro.com/docs/board-items)
- [REST API Comparison (v1 vs v2)](https://developers.miro.com/docs/rest-api-comparison-guide)
- [Miro App Examples](https://github.com/miroapp/app-examples)

## Next Steps

This is the final Flagship skill. For starting a new integration from scratch, see `miro-install-auth`.
