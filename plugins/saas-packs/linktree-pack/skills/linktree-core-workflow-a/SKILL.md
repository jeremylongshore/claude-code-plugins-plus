---
name: linktree-core-workflow-a
description: |
  Execute Linktree primary workflow: Profile & Links Management.
  Trigger: "linktree profile & links management", "primary linktree workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree — Profile & Links Management

## Overview
Primary workflow for Linktree integration.

## Instructions

### Step 1: Get Profile
```typescript
const profile = await client.profiles.get('myprofile');
console.log(`Bio: ${profile.bio}`);
console.log(`Links: ${profile.links.length}`);
```

### Step 2: Create a Link
```typescript
const link = await client.links.create({
  profile_id: profile.id,
  title: 'My Website',
  url: 'https://example.com',
  position: 0,  // Top of list
  thumbnail: 'https://example.com/icon.png'
});
console.log(`Created link: ${link.id}`);
```

### Step 3: Update Link
```typescript
await client.links.update(link.id, {
  title: 'Updated Title',
  archived: false
});
```

### Step 4: List All Links
```typescript
const links = await client.links.list({ profile_id: profile.id });
links.forEach(l => console.log(`${l.position}: ${l.title} → ${l.url}`));
```

## Resources
- [Linktree Docs](https://linktr.ee/marketplace/developer)

## Next Steps
See `linktree-core-workflow-b`.
