Price list strategies for Shopify B2B: percentage adjustments, fixed prices, and volume pricing.

## Percentage-Based Price List

Apply a blanket discount to all products in a catalog:

```typescript
const PRICE_LIST_CREATE = `
  mutation priceListCreate($input: PriceListCreateInput!) {
    priceListCreate(input: $input) {
      priceList {
        id
        name
        currency
        parent {
          adjustment { type value }
        }
      }
      userErrors { field message code }
    }
  }
`;

// 25% off all products for this catalog
await client.request(PRICE_LIST_CREATE, {
  variables: {
    input: {
      name: "Silver Tier - 25% Off",
      currency: "USD",
      parent: {
        adjustment: {
          type: "PERCENTAGE_DECREASE", // PERCENTAGE_DECREASE or PERCENTAGE_INCREASE
          value: 25,
        },
      },
      catalogId: "gid://shopify/Catalog/123",
    },
  },
});
```

## Fixed Price Overrides

Set specific prices for individual variants, overriding the percentage adjustment:

```typescript
const FIXED_PRICES_ADD = `
  mutation priceListFixedPricesAdd(
    $priceListId: ID!,
    $prices: [PriceListPriceInput!]!
  ) {
    priceListFixedPricesAdd(priceListId: $priceListId, prices: $prices) {
      prices {
        variant { id title }
        price { amount currencyCode }
        compareAtPrice { amount currencyCode }
      }
      userErrors { field message code }
    }
  }
`;

await client.request(FIXED_PRICES_ADD, {
  variables: {
    priceListId: "gid://shopify/PriceList/456",
    prices: [
      {
        variantId: "gid://shopify/ProductVariant/111",
        price: {
          amount: "15.00",
          currencyCode: "USD",
        },
        compareAtPrice: {
          amount: "29.99", // Shows original price crossed out
          currencyCode: "USD",
        },
      },
      {
        variantId: "gid://shopify/ProductVariant/222",
        price: {
          amount: "42.50",
          currencyCode: "USD",
        },
      },
    ],
  },
});
```

## Query Price List Prices

```typescript
const PRICE_LIST_PRICES = `
  query priceList($id: ID!, $first: Int!, $after: String) {
    priceList(id: $id) {
      id
      name
      currency
      parent {
        adjustment { type value }
      }
      prices(first: $first, after: $after) {
        edges {
          node {
            variant {
              id
              title
              product { title }
            }
            price { amount currencyCode }
            compareAtPrice { amount currencyCode }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
`;

await client.request(PRICE_LIST_PRICES, {
  variables: { id: "gid://shopify/PriceList/456", first: 50 },
});
```

## Remove Fixed Prices

Revert specific variants back to the percentage-based price:

```typescript
const FIXED_PRICES_DELETE = `
  mutation priceListFixedPricesDelete(
    $priceListId: ID!,
    $variantIds: [ID!]!
  ) {
    priceListFixedPricesDelete(
      priceListId: $priceListId,
      variantIds: $variantIds
    ) {
      deletedFixedPriceVariantIds
      userErrors { field message code }
    }
  }
`;

await client.request(FIXED_PRICES_DELETE, {
  variables: {
    priceListId: "gid://shopify/PriceList/456",
    variantIds: ["gid://shopify/ProductVariant/111"],
  },
});
```

## Volume Pricing (Quantity Rules)

Set minimum, maximum, and increment quantities per variant for B2B:

```typescript
const QUANTITY_RULES_ADD = `
  mutation quantityRulesAdd(
    $priceListId: ID!,
    $quantityRules: [QuantityRuleInput!]!
  ) {
    quantityRulesAdd(
      priceListId: $priceListId,
      quantityRules: $quantityRules
    ) {
      quantityRules {
        variant { id title }
        minimum
        maximum
        increment
      }
      userErrors { field message code }
    }
  }
`;

await client.request(QUANTITY_RULES_ADD, {
  variables: {
    priceListId: "gid://shopify/PriceList/456",
    quantityRules: [
      {
        variantId: "gid://shopify/ProductVariant/111",
        minimum: 12,      // Must order at least 12
        maximum: 1000,     // Cap at 1000 per order
        increment: 12,     // Must order in multiples of 12 (case packs)
      },
      {
        variantId: "gid://shopify/ProductVariant/222",
        minimum: 6,
        increment: 6,
        // No maximum = unlimited
      },
    ],
  },
});
```

## Multi-Currency Pricing

Create separate price lists per currency for international wholesale:

```typescript
// EUR price list for European distributors
await client.request(PRICE_LIST_CREATE, {
  variables: {
    input: {
      name: "EU Wholesale",
      currency: "EUR",
      parent: {
        adjustment: {
          type: "PERCENTAGE_DECREASE",
          value: 30,
        },
      },
      catalogId: "gid://shopify/Catalog/123",
    },
  },
});

// Then add EUR-specific fixed prices
await client.request(FIXED_PRICES_ADD, {
  variables: {
    priceListId: "gid://shopify/PriceList/789",
    prices: [
      {
        variantId: "gid://shopify/ProductVariant/111",
        price: { amount: "13.50", currencyCode: "EUR" },
      },
    ],
  },
});
```
