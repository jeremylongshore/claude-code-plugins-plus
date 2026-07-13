# Step 2: ESLint Rules for Figma

Deep-dive reference for the `figma-policy-guardrails` skill — extracted from the 'Step 2: ESLint Rules for Figma' step of the workflow.

```javascript
// eslint-rules/no-figma-token-literal.js
module.exports = {
  meta: {
    type: 'problem',
    docs: { description: 'Disallow hardcoded Figma PATs' },
  },
  create(context) {
    return {
      Literal(node) {
        if (typeof node.value === 'string' && /^figd_[a-zA-Z0-9_-]{20,}/.test(node.value)) {
          context.report({
            node,
            message: 'Hardcoded Figma PAT detected. Use process.env.FIGMA_PAT instead.',
          });
        }
      },
      TemplateLiteral(node) {
        for (const quasi of node.quasis) {
          if (/figd_[a-zA-Z0-9_-]{20,}/.test(quasi.value.raw)) {
            context.report({
              node,
              message: 'Hardcoded Figma PAT in template literal.',
            });
          }
        }
      },
    };
  },
};
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
