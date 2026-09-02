/**
 * Single source of truth for the marketplace response-security policy.
 *
 * The site is static, so production headers come from Caddy while local Astro
 * preview uses Vite. Keeping the values here prevents those two enforcement
 * layers from silently drifting apart.
 */

export const CSP_INLINE_JUSTIFICATIONS = Object.freeze({
  "script-src":
    'Astro emits page-scoped inline modules and JSON-LD; legacy legal embeds and one inline DOM handler remain.',
  "style-src":
    'Astro component styles and a small number of generated style attributes are inline in the static output.',
});

export const CSP_DIRECTIVES = Object.freeze({
  'default-src': ["'self'"],
  'base-uri': ["'self'"],
  'object-src': ["'none'"],
  'frame-ancestors': ["'self'"],
  'form-action': ["'self'"],
  'script-src': [
    "'self'",
    "'unsafe-inline'",
    'https://analytics.intentsolutions.io',
    'https://www.googletagmanager.com',
    'https://cdn.jsdelivr.net',
    'https://gettermscdn.com',
  ],
  'style-src': ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],
  'font-src': ["'self'", 'data:', 'https://fonts.gstatic.com'],
  'img-src': [
    "'self'",
    'data:',
    'https://github.com',
    'https://avatars.githubusercontent.com',
    'https://www.google-analytics.com',
    'https://www.googletagmanager.com',
  ],
  'connect-src': [
    "'self'",
    'https://analytics.intentsolutions.io',
    'https://www.google-analytics.com',
    'https://analytics.google.com',
    'https://region1.google-analytics.com',
    'https://stats.g.doubleclick.net',
    'https://gettermscdn.com',
    // Deliberate scheme-wide exception: /chats accepts user-supplied WebSocket
    // endpoints, so a static global CSP cannot enumerate hosts. `ws:` supports
    // local HTTP preview; browsers still block mixed-content ws:// in production.
    'wss:',
    'ws:',
  ],
  'frame-src': ["'self'", 'https://gettermscdn.com'],
  'media-src': ["'self'"],
  'manifest-src': ["'self'"],
  'worker-src': ["'self'", 'blob:'],
});

export function serializeCsp(directives = CSP_DIRECTIVES) {
  return Object.entries(directives)
    .map(([name, values]) => [name, ...values].join(' '))
    .join('; ');
}

export function validateSecurityPolicy(
  directives = CSP_DIRECTIVES,
  inlineJustifications = CSP_INLINE_JUSTIFICATIONS,
) {
  const required = {
    'default-src': "'self'",
    'base-uri': "'self'",
    'object-src': "'none'",
    'frame-ancestors': "'self'",
    'form-action': "'self'",
  };
  for (const [name, requiredValue] of Object.entries(required)) {
    if (directives[name]?.length !== 1 || directives[name][0] !== requiredValue) {
      throw new Error(`${name} must be the reviewed singleton ${requiredValue}`);
    }
  }

  const reviewedNames = Object.keys(CSP_DIRECTIVES);
  if (
    Object.keys(directives).length !== reviewedNames.length ||
    reviewedNames.some((name) => !Object.hasOwn(directives, name))
  ) {
    throw new Error('CSP directives must match the reviewed directive allowlist');
  }

  for (const [name, values] of Object.entries(directives)) {
    if (values.includes('*')) throw new Error(`${name} may not contain a wildcard source`);
    if (values.includes("'unsafe-eval'")) throw new Error(`${name} may not allow unsafe-eval`);
    if (values.includes("'unsafe-inline'") && !inlineJustifications[name]) {
      throw new Error(`${name} unsafe-inline requires an explicit justification`);
    }
    const reviewedValues = CSP_DIRECTIVES[name];
    if (
      values.length !== reviewedValues.length ||
      values.some((value, index) => value !== reviewedValues[index])
    ) {
      throw new Error(`${name} must match the reviewed source allowlist`);
    }
  }
  return true;
}

validateSecurityPolicy();

export const MARKETPLACE_SECURITY_HEADERS = Object.freeze({
  'Content-Security-Policy': serializeCsp(),
  'Permissions-Policy': 'camera=(), geolocation=(), microphone=()',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'SAMEORIGIN',
});
