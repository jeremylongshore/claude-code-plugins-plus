---
name: shopify-checkout-extensions
description: |
  Build Checkout UI Extensions to customize Shopify checkout with sandboxed React-like components.
  Use when replacing checkout.liquid (deprecated Aug 2025), adding custom fields to checkout,
  displaying banners, or reading checkout state with hooks.
  Trigger with phrases like "shopify checkout extension", "shopify checkout ui",
  "checkout customization shopify", "checkout.liquid migration", "shopify checkout components".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Checkout UI Extensions

## Overview

Checkout UI Extensions replace checkout.liquid (deprecated August 2025) with sandboxed, React-like components at specific checkout targets. They run in isolation with no DOM access and a strict 64KB bundle limit, using Shopify's component library for consistent, accessible UIs.

## Prerequisites

- Shopify CLI 3.x+ and a Shopify Partners app
- Node.js 18+, `@shopify/ui-extensions-react` package
- Development store with checkout extensibility enabled

## Instructions

### Step 1: Configure the Extension

```toml
# extensions/checkout-banner/shopify.extension.toml
api_version = "2025-01"
type = "ui_extension"

[[extensions.targeting]]
module = "./src/Checkout.tsx"
target = "purchase.checkout.block.render"

[extensions.capabilities]
api_access = true
network_access = false
```

### Step 2: Build with UI Components

```tsx
import {
  reactExtension, Banner, BlockStack, Text, useSettings,
} from "@shopify/ui-extensions-react/checkout";

export default reactExtension("purchase.checkout.block.render", () => <CheckoutBanner />);

function CheckoutBanner() {
  const { banner_text } = useSettings();
  return (
    <BlockStack spacing="tight">
      <Banner status="info">{banner_text || "Free shipping over $50!"}</Banner>
    </BlockStack>
  );
}
```

### Step 3: Read Checkout Data with Hooks

```tsx
import {
  useApplyMetafieldsChange, useTotalAmount, useShippingAddress, TextField,
} from "@shopify/ui-extensions-react/checkout";

function DeliveryNote() {
  const applyMetafieldsChange = useApplyMetafieldsChange();
  return (
    <TextField
      label="Delivery instructions"
      onChange={(value) => applyMetafieldsChange({
        type: "updateMetafield",
        namespace: "custom", key: "delivery_note",
        valueType: "string", value,
      })}
    />
  );
}
```

### Step 4: Bundle Size Strategies

```bash
shopify app build --verbose  # Check output size
# Import only what you use — each component adds ~1-3KB
# Avoid lodash, date-fns, zod — use native JS
# Split into multiple extensions if approaching 64KB
```

See [extension-targets.md](references/extension-targets.md) for all targets, [ui-components.md](references/ui-components.md) for components, and [bundle-optimization.md](references/bundle-optimization.md) for size strategies.

## Output

- Checkout UI extension rendering at the configured target point
- Custom data collection via metafield writes from checkout
- Merchant-configurable settings via the extension editor
- Sandboxed execution with no impact on checkout performance

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `EXTENSION_LOAD_FAILED` | Bundle exceeds 64KB or invalid code | Tree-shake deps; check size with `--verbose` |
| Sandbox violation | DOM access, `fetch`, or `window` usage | Use only Shopify components and hooks |
| `CHECKOUT_COMPLETION_BLOCKED` | Extension error with `block_progress` | Add try/catch; test all edge cases |
| Target not rendering | Wrong target or not enabled | Verify target in TOML; check admin placement |

## Examples

### Adding a Custom Field to Checkout

Collect delivery instructions or gift messages by rendering a text input at a specific checkout target and saving the value as a cart metafield.

See [Extension Targets](references/extension-targets.md) for all available targets and placement options.

### Building a Reusable Checkout Banner

Create a merchant-configurable promotional banner using Shopify's UI component library with proper accessibility.

See [UI Components](references/ui-components.md) for available components and their key props.

### Optimizing Extension Bundle Size

Your checkout extension is approaching the 64KB limit. Apply tree-shaking, dependency auditing, and extension splitting strategies.

See [Bundle Optimization](references/bundle-optimization.md) for size measurement and reduction techniques.

## Resources

- [Checkout UI Extensions Overview](https://shopify.dev/docs/apps/build/checkout)
- [Extension Targets Reference](https://shopify.dev/docs/api/checkout-ui-extensions/latest/extension-targets-overview)
- [UI Component Library](https://shopify.dev/docs/api/checkout-ui-extensions/latest/components)
- [checkout.liquid Migration Guide](https://shopify.dev/docs/apps/build/checkout/migrate-checkout-liquid)
