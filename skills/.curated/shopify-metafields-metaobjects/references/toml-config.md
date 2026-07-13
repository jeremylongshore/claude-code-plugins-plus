Shopify app TOML configuration for metafield definitions and metaobject schemas.

## shopify.app.toml Metafield Configuration

App-owned metafield definitions can be declared in `shopify.app.toml` so they deploy automatically with the app. This replaces making `metafieldDefinitionCreate` API calls during installation.

```toml
# shopify.app.toml

[access_scopes]
scopes = "read_products,write_products,read_metaobjects,write_metaobjects"

# Product metafield — deployed with the app
[[metafields]]
namespace = "custom"
key = "care_instructions"
name = "Care Instructions"
description = "Product washing and care details"
type = "multi_line_text_field"
owner_type = "PRODUCT"
pin = true

[[metafields]]
namespace = "custom"
key = "weight_grams"
name = "Weight (grams)"
type = "number_integer"
owner_type = "PRODUCT"
validations = [
  { name = "min", value = "0" },
  { name = "max", value = "100000" },
]

# Variant-level metafield
[[metafields]]
namespace = "custom"
key = "material"
name = "Material"
type = "single_line_text_field"
owner_type = "PRODUCTVARIANT"

# Customer metafield
[[metafields]]
namespace = "custom"
key = "loyalty_tier"
name = "Loyalty Tier"
type = "single_line_text_field"
owner_type = "CUSTOMER"
validations = [
  { name = "choices", value = '["Bronze","Silver","Gold","Platinum"]' },
]
```

## Metaobject Definitions in TOML

```toml
# Custom content type — deploys with app
[[metaobject_definitions]]
type = "$app:designer"
name = "Designer"
description = "Product designer profiles"

[[metaobject_definitions.field_definitions]]
key = "name"
name = "Name"
type = "single_line_text_field"
required = true

[[metaobject_definitions.field_definitions]]
key = "bio"
name = "Bio"
type = "multi_line_text_field"

[[metaobject_definitions.field_definitions]]
key = "photo"
name = "Photo"
type = "file_reference"
validations = [
  { name = "file_type_options", value = '["Image"]' },
]

[[metaobject_definitions.field_definitions]]
key = "portfolio_url"
name = "Portfolio URL"
type = "url"

[metaobject_definitions.access]
storefront = "PUBLIC_READ"
```

## Key Rules

- **Namespace `$app:`**: App-owned definitions use the `$app:` prefix. Shopify auto-scopes these to your app.
- **Deployment**: Run `shopify app deploy` to push definitions. Shopify diffs against existing definitions and applies changes.
- **Pinning**: `pin = true` shows the metafield in the Shopify admin UI for that resource.
- **Deletions**: Removing a definition from TOML does NOT delete it from the store. Use `metafieldDefinitionDelete` mutation for cleanup.
- **Type immutability**: You cannot change a metafield's `type` after creation. Delete and recreate if the type is wrong.
