# Secret Detection ESLint Rule

Custom ESLint rule that detects hardcoded Shopify tokens (`shpat_*`, `shpss_*`) and API secrets in source code.

```javascript
// eslint-rules/no-shopify-secrets.js
module.exports = {
  meta: {
    type: "problem",
    docs: { description: "Detect hardcoded Shopify tokens and secrets" },
    messages: {
      adminToken: "Hardcoded Shopify Admin API token detected (shpat_*)",
      apiSecret: "Potential Shopify API secret detected",
      storefrontToken: "Hardcoded Storefront API token detected",
    },
  },
  create(context) {
    return {
      Literal(node) {
        if (typeof node.value !== "string") return;
        const v = node.value;

        // Admin API access token: shpat_ + 32 hex chars
        if (/^shpat_[a-f0-9]{32}$/i.test(v)) {
          context.report({ node, messageId: "adminToken" });
        }
        // Storefront token: shpss_ pattern
        if (/^shpss_[a-f0-9]{32}$/i.test(v)) {
          context.report({ node, messageId: "storefrontToken" });
        }
        // Generic secret pattern (32+ hex that's clearly a token)
        if (/^[a-f0-9]{32,}$/i.test(v) && v.length === 32) {
          context.report({ node, messageId: "apiSecret" });
        }
      },
      TemplateLiteral(node) {
        for (const quasi of node.quasis) {
          if (/shpat_[a-f0-9]/i.test(quasi.value.raw)) {
            context.report({ node, messageId: "adminToken" });
          }
        }
      },
    };
  },
};
```
