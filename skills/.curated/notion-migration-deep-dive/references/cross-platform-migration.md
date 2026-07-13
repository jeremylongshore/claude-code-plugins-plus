# Cross-Platform Migration and Validation

**Transform Confluence/Google Docs content to Notion blocks:**

```typescript
// Convert HTML-like content to Notion block objects
function htmlToNotionBlocks(html: string): any[] {
  const blocks: any[] = [];
  const lines = html.split('\n').filter(l => l.trim());

  for (const line of lines) {
    const trimmed = line.trim();

    // Headings
    if (trimmed.startsWith('# ')) {
      blocks.push({
        heading_1: { rich_text: [{ text: { content: trimmed.slice(2) } }] },
      });
    } else if (trimmed.startsWith('## ')) {
      blocks.push({
        heading_2: { rich_text: [{ text: { content: trimmed.slice(3) } }] },
      });
    } else if (trimmed.startsWith('### ')) {
      blocks.push({
        heading_3: { rich_text: [{ text: { content: trimmed.slice(4) } }] },
      });
    }
    // Bullet lists
    else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      blocks.push({
        bulleted_list_item: {
          rich_text: [{ text: { content: trimmed.slice(2) } }],
        },
      });
    }
    // Code blocks
    else if (trimmed.startsWith('```')) {
      // Simplified: handle inline code fence
      blocks.push({
        code: {
          rich_text: [{ text: { content: trimmed.replace(/```/g, '') } }],
          language: 'plain text',
        },
      });
    }
    // Regular paragraphs
    else if (trimmed.length > 0) {
      blocks.push({
        paragraph: { rich_text: [{ text: { content: trimmed } }] },
      });
    }
  }

  return blocks;
}

// Create a Notion page with content blocks (max 100 blocks per append)
async function createPageWithContent(
  databaseId: string,
  title: string,
  blocks: any[]
) {
  // Create the page first
  const page = await notion.pages.create({
    parent: { database_id: databaseId },
    properties: {
      Name: { title: [{ text: { content: title } }] },
      Source: { select: { name: 'Migration' } },
      'Migrated At': { date: { start: new Date().toISOString() } },
    },
  });

  // Append blocks in batches of 100 (Notion's limit)
  for (let i = 0; i < blocks.length; i += 100) {
    const batch = blocks.slice(i, i + 100);
    await notion.blocks.children.append({
      block_id: page.id,
      children: batch,
    });

    if (i + 100 < blocks.length) {
      await new Promise(r => setTimeout(r, 350)); // Rate limit
    }
  }

  return page;
}
```

**Post-migration validation:**

```typescript
async function validateMigration(
  sourceData: Record<string, any>[],
  targetDatabaseId: string,
  keyField: string = 'Name'
) {
  console.log('Running migration validation...');

  // Export target database
  const targetData = await exportDatabase(targetDatabaseId);

  const report = {
    sourceCount: sourceData.length,
    targetCount: targetData.length,
    countMatch: sourceData.length === targetData.length,
    missingInTarget: [] as string[],
    duplicatesInTarget: [] as string[],
    fieldIntegrity: { checked: 0, passed: 0, failed: 0 },
  };

  // Build lookup from target
  const targetByKey = new Map<string, Record<string, any>[]>();
  for (const row of targetData) {
    const key = row[keyField];
    const existing = targetByKey.get(key) || [];
    existing.push(row);
    targetByKey.set(key, existing);
  }

  // Check for duplicates
  for (const [key, rows] of targetByKey) {
    if (rows.length > 1) {
      report.duplicatesInTarget.push(`"${key}" (${rows.length} copies)`);
    }
  }

  // Check every source record exists in target
  for (const sourceRow of sourceData) {
    const key = sourceRow[keyField];
    const targetRows = targetByKey.get(key);

    if (!targetRows || targetRows.length === 0) {
      report.missingInTarget.push(key);
    } else {
      report.fieldIntegrity.checked++;
      // Compare specific fields
      const targetRow = targetRows[0];
      const fieldsMatch = Object.keys(sourceRow)
        .filter(k => k !== 'id' && k !== 'url')
        .every(k => String(sourceRow[k] ?? '') === String(targetRow[k] ?? ''));

      if (fieldsMatch) {
        report.fieldIntegrity.passed++;
      } else {
        report.fieldIntegrity.failed++;
      }
    }
  }

  // Print report
  console.log('\n=== Migration Validation Report ===');
  console.log(`Source records: ${report.sourceCount}`);
  console.log(`Target records: ${report.targetCount}`);
  console.log(`Count match: ${report.countMatch ? 'PASS' : 'FAIL'}`);
  console.log(`Missing in target: ${report.missingInTarget.length}`);
  console.log(`Duplicates in target: ${report.duplicatesInTarget.length}`);
  console.log(`Field integrity: ${report.fieldIntegrity.passed}/${report.fieldIntegrity.checked} passed`);
  console.log(`Overall: ${
    report.missingInTarget.length === 0 && report.countMatch ? 'PASS' : 'FAIL'
  }`);

  if (report.missingInTarget.length > 0) {
    console.log('\nMissing records (first 10):');
    report.missingInTarget.slice(0, 10).forEach(m => console.log(`  - ${m}`));
  }

  return report;
}
```
