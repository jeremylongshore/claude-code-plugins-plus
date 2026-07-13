Strategies for staying under the 64KB Checkout UI Extension bundle limit.

## Measuring Bundle Size

```bash
# Build and check the output size
shopify app build --verbose

# The built extension is at:
# extensions/[name]/dist/[target].js
ls -la extensions/checkout-banner/dist/*.js

# Detailed breakdown (if using esbuild directly)
npx esbuild extensions/checkout-banner/src/Checkout.tsx \
  --bundle --analyze --outfile=/dev/null
```

## Import Strategy

### Import Only What You Use

```tsx
// BAD: Imports the entire library
import * as UI from "@shopify/ui-extensions-react/checkout";

// GOOD: Named imports enable tree-shaking
import {
  reactExtension,
  Banner,
  BlockStack,
  Text,
  useSettings,
} from "@shopify/ui-extensions-react/checkout";
```

### Avoid Heavy Dependencies

| Dependency | Size Impact | Alternative |
|-----------|-------------|-------------|
| `lodash` | ~70KB | Native array/object methods |
| `date-fns` | ~30KB+ | `Intl.DateTimeFormat` or manual formatting |
| `zod` | ~14KB | Manual validation (checkout data is typed) |
| `uuid` | ~3KB | `crypto.randomUUID()` |
| Any React router | N/A | Not applicable (single component, no routing) |

## Code Splitting Between Extensions

If your app has multiple checkout extensions, share code via a local package:

```
extensions/
├── shared/
│   ├── package.json
│   └── src/
│       ├── formatPrice.ts      # Shared utility
│       └── constants.ts        # Shared config
├── checkout-banner/
│   ├── shopify.extension.toml
│   └── src/Checkout.tsx        # Imports from ../shared/
└── delivery-note/
    ├── shopify.extension.toml
    └── src/Checkout.tsx        # Imports from ../shared/
```

Each extension is bundled independently, so shared code is duplicated per bundle. Keep shared modules small.

## Reducing Component Count

```tsx
// BAD: Many small components (each import adds overhead)
import {
  BlockStack, InlineStack, View, Grid,
  Text, Heading, TextBlock,
  Button, Pressable,
  Banner, Divider, Image, Icon,
  TextField, Checkbox, Select, ChoiceList,
} from "@shopify/ui-extensions-react/checkout";

// GOOD: Only what this extension actually renders
import {
  reactExtension,
  BlockStack,
  Banner,
  Text,
  useSettings,
} from "@shopify/ui-extensions-react/checkout";
```

## When Approaching the Limit

1. **Audit imports**: Remove unused components and hooks
2. **Inline small utilities**: Don't import a library for one function
3. **Split into multiple extensions**: Two 30KB extensions beat one 60KB extension
4. **Move logic to metafields**: Pre-compute values in your app backend, store as metafields, read with `useAppMetafields()` — keeps the extension thin
5. **Use `useSettings()`**: Let merchants configure text/values instead of hardcoding strings in the bundle

## Size Budget Planning

| Component | Approximate Cost |
|-----------|-----------------|
| Base extension boilerplate | ~5KB |
| Each UI component import | ~1-3KB |
| Each hook import | ~0.5-2KB |
| Shared utility code | Varies |
| **Target budget** | **< 50KB** (leave headroom) |

Leave at least 14KB of headroom below the 64KB limit for Shopify's runtime overhead and future component updates.
