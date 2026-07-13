# Step 1: Vercel Deployment (Webhook Receiver)

Deep-dive reference for the `figma-deploy-integration` skill — extracted from the 'Step 1: Vercel Deployment (Webhook Receiver)' step of the workflow.

```bash
# Store Figma secrets
vercel env add FIGMA_PAT production
vercel env add FIGMA_WEBHOOK_PASSCODE production

# Deploy
vercel --prod
```

```typescript
// api/webhooks/figma.ts (Vercel serverless function)
import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';

export async function POST(req: NextRequest) {
  const payload = await req.json();

  // Verify passcode
  const expected = process.env.FIGMA_WEBHOOK_PASSCODE!;
  const received = payload.passcode || '';
  const a = Buffer.from(received);
  const b = Buffer.from(expected);
  // timingSafeEqual throws on length mismatch — guard first
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) {
    return NextResponse.json({ error: 'Invalid passcode' }, { status: 401 });
  }

  // Process webhook event
  switch (payload.event_type) {
    case 'FILE_UPDATE':
      console.log(`File updated: ${payload.file_name} (${payload.file_key})`);
      // Trigger token re-sync, invalidate cache, etc.
      break;
    case 'FILE_COMMENT':
      console.log(`New comment on ${payload.file_name}`);
      break;
    case 'LIBRARY_PUBLISH':
      console.log(`Library published: ${payload.file_name}`);
      break;
  }

  return NextResponse.json({ received: true });
}

export const config = { maxDuration: 10 };
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
