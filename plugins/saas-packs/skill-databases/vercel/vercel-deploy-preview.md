# vercel-deploy-preview

## Skill Scaffold

```
vercel-deploy-preview/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Deploy preview environments for pull requests and branches - instant previews for every commit.
**Workflow:** Primary deployment workflow - triggered on every PR to create shareable preview environments.
**Relates to:** Follows vercel-sdk-patterns; complements vercel-edge-functions as secondary workflow

## Summary

This skill implements Vercel's core feature: deploy previews. It enables instant preview deployments for every pull request, allowing teams to test changes in isolated environments before merging. This is the primary workflow for Vercel - every commit generates a unique preview URL that can be shared with stakeholders for testing and feedback before production deployment.
