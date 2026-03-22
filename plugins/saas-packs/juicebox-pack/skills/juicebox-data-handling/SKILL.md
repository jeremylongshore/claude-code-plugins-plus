---
name: juicebox-data-handling
description: |
  Juicebox data privacy and GDPR.
  Trigger: "juicebox data privacy", "juicebox gdpr".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Data Handling

## Data Classification
| Type | Retention |
|------|----------|
| Search results | Session only |
| Enriched profiles | Per policy |
| Contact data | Until candidate objects |

## GDPR Compliance
```typescript
async function deleteCandidate(id: string) {
  await candidateStore.delete(id);
  await outreachLog.purge(id);
}

async function exportData(id: string) {
  return { profile: await candidateStore.get(id), outreach: await outreachLog.get(id) };
}
```

## Checklist
- [ ] Data encrypted at rest
- [ ] Retention periods documented
- [ ] GDPR consent for EU candidates
- [ ] Right to deletion implemented

## Resources
- [Privacy](https://juicebox.ai/privacy)

## Next Steps
See `juicebox-enterprise-rbac`.
