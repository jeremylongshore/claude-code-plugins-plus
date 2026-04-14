Input query examples and FunctionRunResult shapes for each Shopify Function type.

## Product Discount Input/Output

### Input Query
```graphql
query Input {
  cart {
    lines {
      quantity
      cost {
        amountPerQuantity { amount currencyCode }
        totalAmount { amount currencyCode }
      }
      merchandise {
        ... on ProductVariant {
          id
          product {
            id
            hasAnyTag(tags: ["sale"])
            inAnyCollection(ids: ["gid://shopify/Collection/123"])
          }
        }
      }
    }
    buyerIdentity {
      customer { id hasAnyTag(tags: ["VIP"]) }
    }
  }
  discountNode {
    metafield(namespace: "$app:config", key: "settings") { value }
  }
}
```

### FunctionRunResult
```typescript
interface FunctionRunResult {
  discountApplicationStrategy: "FIRST" | "MAXIMUM";
  discounts: Array<{
    targets: Array<{
      productVariant: { id: string };
    }>;
    value:
      | { percentage: { value: string } }       // "10.0" for 10%
      | { fixedAmount: { amount: string } };     // "5.00" for $5 off
    message?: string;                            // Shown to customer
    conditions?: Array<{
      productMinimumQuantity?: { ids: string[]; minimumQuantity: string };
      productMinimumSubtotal?: { ids: string[]; minimumAmount: { amount: string } };
      orderMinimumSubtotal?: { minimumAmount: { amount: string } };
    }>;
  }>;
}
```

## Order Discount Input/Output

### FunctionRunResult
```typescript
interface FunctionRunResult {
  discountApplicationStrategy: "FIRST" | "MAXIMUM";
  discounts: Array<{
    value:
      | { percentage: { value: string } }
      | { fixedAmount: { amount: string } };
    message?: string;
    conditions?: Array<{
      orderMinimumSubtotal?: { minimumAmount: { amount: string } };
    }>;
  }>;
  // Note: no "targets" — applies to whole order
}
```

## Payment Customization Input/Output

### Input Query
```graphql
query Input {
  cart {
    cost { totalAmount { amount currencyCode } }
    buyerIdentity {
      customer { hasAnyTag(tags: ["wholesale"]) }
    }
  }
  paymentMethods {
    id
    name
  }
  paymentCustomization {
    metafield(namespace: "$app:config", key: "rules") { value }
  }
}
```

### FunctionRunResult
```typescript
interface FunctionRunResult {
  operations: Array<
    | { hide: { paymentMethodId: string } }
    | { rename: { paymentMethodId: string; name: string } }
    | { move: { paymentMethodId: string; index: number } }
  >;
}
```

## Delivery Customization Input/Output

### Input Query
```graphql
query Input {
  cart {
    deliveryGroups {
      deliveryOptions {
        handle
        title
        cost { amount }
      }
      deliveryAddress {
        countryCode
        provinceCode
      }
    }
  }
  deliveryCustomization {
    metafield(namespace: "$app:config", key: "rules") { value }
  }
}
```

### FunctionRunResult
```typescript
interface FunctionRunResult {
  operations: Array<
    | { hide: { deliveryOptionHandle: string } }
    | { rename: { deliveryOptionHandle: string; name: string } }
    | { move: { deliveryOptionHandle: string; index: number } }
  >;
}
```

## Cart Transform Input/Output

### FunctionRunResult
```typescript
interface FunctionRunResult {
  operations: Array<
    | { merge: { parentVariantId: string; title: string; cartLines: Array<{ cartLineId: string; quantity: number }> } }
    | { expand: { cartLineId: string; expandedCartItems: Array<{ merchandiseId: string; quantity: number }> } }
    | { update: { cartLineId: string; title?: string; image?: { url: string } } }
  >;
}
```
