---
name: juicebox-reference-architecture
description: |
  Implement Juicebox reference architecture.
  Trigger: "juicebox architecture", "recruiting platform design".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Reference Architecture

## Architecture
```
Recruiter UI → Search Service → Juicebox API
                    ↓
              Candidate Store → ATS (Greenhouse/Lever)
                    ↓
             Outreach Service → Juicebox Outreach
                    ↓
              Webhook Handler ← Juicebox Events
```

## Components
```typescript
class SearchService {
  async findCandidates(criteria) {
    const results = await juicebox.search(criteria);
    return results.profiles.map(p => this.score(p, criteria));
  }
}

class ATSSync {
  async push(candidates, jobId: string) {
    await juicebox.export({ profiles: candidates.map(c => c.id), destination: 'greenhouse', job_id: jobId });
  }
}
```

## Resources
- [Integrations](https://juicebox.ai/integrations)

## Next Steps
See `juicebox-multi-env-setup`.
