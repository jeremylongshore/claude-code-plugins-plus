Complete Storefront Cart API mutations with real field names and response shapes.

## Cart Lifecycle

```
cartCreate → cartLinesAdd/Update/Remove → customer visits checkoutUrl → order created
```

Carts expire after **10 days of inactivity**. Do not persist cart IDs in long-term storage.

## cartCreate

```typescript
const CART_CREATE = `#graphql
  mutation cartCreate($input: CartInput!) {
    cartCreate(input: $input) {
      cart { ...CartFragment }
      userErrors { field message code }
    }
  }

  fragment CartFragment on Cart {
    id
    checkoutUrl
    totalQuantity
    note
    cost {
      totalAmount { amount currencyCode }
      subtotalAmount { amount currencyCode }
      totalTaxAmount { amount currencyCode }
      totalDutyAmount { amount currencyCode }
    }
    lines(first: 100) {
      edges { node {
        id
        quantity
        cost {
          amountPerQuantity { amount currencyCode }
          totalAmount { amount currencyCode }
        }
        merchandise {
          ... on ProductVariant {
            id
            title
            product { title handle }
            image { url altText }
            price { amount currencyCode }
            selectedOptions { name value }
          }
        }
        attributes { key value }
      }}
    }
    buyerIdentity {
      email
      countryCode
    }
    discountCodes { code applicable }
  }
`;
```

## cartLinesAdd

```typescript
const CART_LINES_ADD = `#graphql
  mutation cartLinesAdd($cartId: ID!, $lines: [CartLineInput!]!) {
    cartLinesAdd(cartId: $cartId, lines: $lines) {
      cart { ...CartFragment }
      userErrors { field message code }
    }
  }
`;

await client.request(CART_LINES_ADD, {
  variables: {
    cartId: "gid://shopify/Cart/abc123",
    lines: [
      {
        merchandiseId: "gid://shopify/ProductVariant/456",
        quantity: 1,
        attributes: [{ key: "Gift wrapping", value: "Yes" }],
      },
    ],
  },
});
```

## cartLinesUpdate

```typescript
const CART_LINES_UPDATE = `#graphql
  mutation cartLinesUpdate($cartId: ID!, $lines: [CartLineUpdateInput!]!) {
    cartLinesUpdate(cartId: $cartId, lines: $lines) {
      cart { ...CartFragment }
      userErrors { field message code }
    }
  }
`;

await client.request(CART_LINES_UPDATE, {
  variables: {
    cartId: "gid://shopify/Cart/abc123",
    lines: [
      {
        id: "gid://shopify/CartLine/789",  // Line ID, not variant ID
        quantity: 3,
      },
    ],
  },
});
```

## cartLinesRemove

```typescript
const CART_LINES_REMOVE = `#graphql
  mutation cartLinesRemove($cartId: ID!, $lineIds: [ID!]!) {
    cartLinesRemove(cartId: $cartId, lineIds: $lineIds) {
      cart { ...CartFragment }
      userErrors { field message code }
    }
  }
`;

await client.request(CART_LINES_REMOVE, {
  variables: {
    cartId: "gid://shopify/Cart/abc123",
    lineIds: ["gid://shopify/CartLine/789"],
  },
});
```

## cartDiscountCodesUpdate

```typescript
const CART_DISCOUNT = `#graphql
  mutation cartDiscountCodesUpdate($cartId: ID!, $discountCodes: [String!]!) {
    cartDiscountCodesUpdate(cartId: $cartId, discountCodes: $discountCodes) {
      cart {
        id
        discountCodes { code applicable }
        cost { totalAmount { amount currencyCode } }
      }
      userErrors { field message code }
    }
  }
`;

await client.request(CART_DISCOUNT, {
  variables: {
    cartId: "gid://shopify/Cart/abc123",
    discountCodes: ["SUMMER20"],
  },
});
```

## cartBuyerIdentityUpdate

```typescript
const CART_BUYER = `#graphql
  mutation cartBuyerIdentityUpdate($cartId: ID!, $buyerIdentity: CartBuyerIdentityInput!) {
    cartBuyerIdentityUpdate(cartId: $cartId, buyerIdentity: $buyerIdentity) {
      cart { ...CartFragment }
      userErrors { field message code }
    }
  }
`;

await client.request(CART_BUYER, {
  variables: {
    cartId: "gid://shopify/Cart/abc123",
    buyerIdentity: {
      email: "customer@example.com",
      countryCode: "US",
      customerAccessToken: "token-from-customerAccessTokenCreate",
    },
  },
});
```
