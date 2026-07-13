# Error Handling with Shopify Error Types

Custom error class that distinguishes retryable from permanent errors, plus a safe wrapper returning `{data, error}` tuples.

```typescript
// src/shopify/errors.ts
import { HttpResponseError, GraphqlQueryError } from "@shopify/shopify-api";

export class ShopifyServiceError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly retryable: boolean,
    public readonly shopifyRequestId?: string,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = "ShopifyServiceError";
  }
}

export function handleShopifyError(error: unknown): never {
  if (error instanceof HttpResponseError) {
    const retryable = [429, 500, 502, 503, 504].includes(error.response.code);
    throw new ShopifyServiceError(
      `Shopify API ${error.response.code}: ${error.message}`,
      error.response.code,
      retryable,
      error.response.headers?.["x-request-id"] as string,
      error
    );
  }

  if (error instanceof GraphqlQueryError) {
    // GraphQL errors in the response body
    const msg = error.body?.errors
      ?.map((e: any) => e.message)
      .join("; ") || error.message;
    throw new ShopifyServiceError(msg, 200, false, undefined, error);
  }

  throw error;
}

// Safe wrapper
export async function safeShopifyCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: ShopifyServiceError | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    try {
      handleShopifyError(err);
    } catch (shopifyErr) {
      return { data: null, error: shopifyErr as ShopifyServiceError };
    }
    return { data: null, error: err as ShopifyServiceError };
  }
}
```
