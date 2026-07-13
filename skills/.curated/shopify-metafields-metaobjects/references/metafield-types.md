Complete list of Shopify metafield types with value format examples.

## Scalar Types

| Type | Value Example | Notes |
|------|--------------|-------|
| `single_line_text_field` | `"Hello world"` | Max 512KB, no newlines |
| `multi_line_text_field` | `"Line 1\nLine 2"` | Max 512KB, newlines allowed |
| `number_integer` | `"42"` | String-encoded integer |
| `number_decimal` | `"19.99"` | String-encoded decimal |
| `boolean` | `"true"` | `"true"` or `"false"` only |
| `color` | `"#FF5733"` | Hex color code |
| `date` | `"2025-06-15"` | ISO 8601 date |
| `date_time` | `"2025-06-15T10:30:00Z"` | ISO 8601 datetime |
| `dimension` | `{"value": 10.5, "unit": "CENTIMETERS"}` | JSON object, units: `INCHES`, `FEET`, `CENTIMETERS`, `METERS` |
| `weight` | `{"value": 250, "unit": "GRAMS"}` | JSON object, units: `GRAMS`, `KILOGRAMS`, `OUNCES`, `POUNDS` |
| `volume` | `{"value": 500, "unit": "MILLILITERS"}` | JSON object |
| `money` | `{"amount": "29.99", "currency_code": "USD"}` | JSON object |
| `rating` | `{"value": "4.5", "scale_min": "1.0", "scale_max": "5.0"}` | JSON object |
| `url` | `"https://example.com"` | Valid URL string |
| `json` | `"{\"key\": \"value\"}"` | Arbitrary JSON, max 512KB |
| `rich_text_field` | `{"type":"root","children":[...]}` | Shopify rich text JSON schema |

## Reference Types

| Type | Value Example | Notes |
|------|--------------|-------|
| `file_reference` | `"gid://shopify/MediaImage/123"` | Reference to uploaded file |
| `product_reference` | `"gid://shopify/Product/123"` | Reference to a product |
| `variant_reference` | `"gid://shopify/ProductVariant/123"` | Reference to a variant |
| `collection_reference` | `"gid://shopify/Collection/123"` | Reference to a collection |
| `page_reference` | `"gid://shopify/Page/123"` | Reference to a page |
| `metaobject_reference` | `"gid://shopify/Metaobject/123"` | Reference to a metaobject |
| `mixed_reference` | `"gid://shopify/Product/123"` | Can reference any resource type |

## List Types

Any scalar or reference type can be a list by prefixing with `list.`:

```
list.single_line_text_field  → ["Red", "Blue", "Green"]
list.product_reference       → ["gid://shopify/Product/1", "gid://shopify/Product/2"]
list.number_integer          → ["1", "2", "3"]
list.url                     → ["https://a.com", "https://b.com"]
list.metaobject_reference    → ["gid://shopify/Metaobject/1", "gid://shopify/Metaobject/2"]
```

**Important:** List values are JSON arrays encoded as strings. The outer value passed to the API is always a string.

## Validation Rules

Metafield definitions support validations per type:

```typescript
// Example: number_integer with min/max
{
  type: "number_integer",
  validations: [
    { name: "min", value: "0" },
    { name: "max", value: "100" },
  ],
}

// Example: single_line_text_field with regex
{
  type: "single_line_text_field",
  validations: [
    { name: "regex", value: "^SKU-[A-Z0-9]+$" },
  ],
}

// Example: file_reference restricted to images
{
  type: "file_reference",
  validations: [
    { name: "file_type_options", value: '["Image"]' },
  ],
}
```
