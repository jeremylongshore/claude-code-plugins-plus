# Eslint Rules

## ESLint Rules

### Custom Supabase Plugin

```javascript
// eslint-plugin-supabase/rules/no-hardcoded-keys.js
module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Disallow hardcoded Supabase API keys',
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
              message: 'Hardcoded Supabase API key detected',
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
  plugins: ['supabase'],
  rules: {
    'supabase/no-hardcoded-keys': 'error',
    'supabase/require-error-handling': 'warn',
    'supabase/use-typed-client': 'warn',
  },
};
```
