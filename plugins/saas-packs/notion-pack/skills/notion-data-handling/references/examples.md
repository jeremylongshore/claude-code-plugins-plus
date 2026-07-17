# Examples

End-to-end snippets that compose the building blocks from the other reference files.

## Quick PII audit for a database

Runs the full-database scanner from `pii-detection.md` and prints a per-page summary of
what PII types were found:

```typescript
const findings = await auditDatabaseForPII(process.env.NOTION_DB_ID!);
console.log(`PII audit: ${findings.length} pages with PII detected`);
for (const f of findings) {
  console.log(`  Page "${f.pageTitle}": ${f.pii.map(p => p.piiType).join(', ')}`);
}
```

## Python data export

A compact Python equivalent of the Article 15 export in `compliance-patterns.md` —
queries each database for pages assigned to the user and collects their properties:

```python
def export_user_data(user_id: str, db_ids: list[str]) -> dict:
    export = {"exported_at": datetime.utcnow().isoformat(), "databases": {}}
    for db_id in db_ids:
        results = client.databases.query(
            database_id=db_id,
            filter={"property": "Assignee", "people": {"contains": user_id}},
        )
        export["databases"][db_id] = [
            {"id": p["id"], "properties": p["properties"]}
            for p in results["results"]
        ]
    return export
```
