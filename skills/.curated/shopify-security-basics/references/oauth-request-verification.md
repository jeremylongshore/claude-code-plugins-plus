# OAuth Request Verification

Manual HMAC verification for incoming OAuth requests from Shopify (the library handles this automatically, but this shows the underlying approach).

```typescript
import { shopifyApi } from "@shopify/shopify-api";

// The library handles this automatically, but here's the manual approach:
function verifyShopifyRequest(query: Record<string, string>, secret: string): boolean {
  const { hmac, ...params } = query;
  if (!hmac) return false;

  // Sort parameters and create query string
  const message = Object.keys(params)
    .sort()
    .map((key) => `${key}=${params[key]}`)
    .join("&");

  const computed = crypto
    .createHmac("sha256", secret)
    .update(message)
    .digest("hex");

  return crypto.timingSafeEqual(
    Buffer.from(computed),
    Buffer.from(hmac)
  );
}
```
