---
name: shipwright-build
description: Build a new app from a plain-English description
category: deployment
---

# /shipwright-build

Build a complete application from a natural-language description using the Shipwright 9-phase pipeline.

## Steps

1. Prompt the user for an app description if not provided as an argument.
2. Confirm the target stack (Next.js + Supabase, Next.js + Prisma, SvelteKit, or Astro).
3. Use the `shipwright-pipeline` skill to orchestrate the full build.
4. Report the final output directory, test results, and next steps.
