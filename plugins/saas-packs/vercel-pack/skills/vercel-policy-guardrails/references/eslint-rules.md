# Eslint Rules

## ESLint Rules

### Custom Vercel Plugin

```javascript
// eslint-plugin-vercel/rules/no-hardcoded-keys.js
module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Disallow hardcoded Vercel API keys',
    },
    fixable: 'code',
  },
  create(context) {
    return {
      Literal(node) {
        if (typeof node.value === 'string') {
          if (node.value.match(/^sk_(live|test)_[a-zA-Z0-9]{24,}/)) {
            context.report({
              node,
              message: 'Hardcoded Vercel API key detected',
            });
          }
        }
      },
    };
  },
};
```

### ESLint Configuration

```javascript
// .eslintrc.js
module.exports = {
  plugins: ['vercel'],
  rules: {
    'vercel/no-hardcoded-keys': 'error',
    'vercel/require-error-handling': 'warn',
    'vercel/use-typed-client': 'warn',
  },
};
```
