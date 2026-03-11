# Evernote Debug Bundle - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Debug Logger

```javascript
// utils/debug-logger.js
const fs = require('fs');
const path = require('path');

class EvernoteDebugLogger {
  constructor(options = {}) {
    this.enabled = options.enabled ?? process.env.EVERNOTE_DEBUG === 'true';
    this.logFile = options.logFile || 'evernote-debug.log';
    this.logDir = options.logDir || './logs';
    this.maxLogSize = options.maxLogSize || 10 * 1024 * 1024; // 10MB

    if (this.enabled) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }
  }

  log(operation, data) {
    if (!this.enabled) return;

    const entry = {
      timestamp: new Date().toISOString(),
      operation,
      ...data
    };

    // Console output
    console.log(`[EVERNOTE DEBUG] ${operation}`, JSON.stringify(data, null, 2));

    // File output
    this.writeToFile(entry);
  }

  logRequest(operation, params) {
    this.log(operation, {
      type: 'REQUEST',
      params: this.sanitizeParams(params)
    });
  }

  logResponse(operation, response) {
    this.log(operation, {
      type: 'RESPONSE',
      response: this.summarizeResponse(response)
    });
  }

  logError(operation, error) {
    this.log(operation, {
      type: 'ERROR',
      errorCode: error.errorCode,
      parameter: error.parameter,
      identifier: error.identifier,
      key: error.key,
      rateLimitDuration: error.rateLimitDuration,
      message: error.message,
      stack: error.stack
    });
  }

  sanitizeParams(params) {
    // Remove sensitive data from logs
    const sanitized = { ...params };
    if (sanitized.token) sanitized.token = '[REDACTED]';
    if (sanitized.password) sanitized.password = '[REDACTED]';
    if (sanitized.content && sanitized.content.length > 500) {
      sanitized.content = sanitized.content.substring(0, 500) + '...[truncated]';
    }
    return sanitized;
  }

  summarizeResponse(response) {
    if (!response) return null;

    // Summarize common response types
    if (response.guid) {
      return {
        guid: response.guid,
        title: response.title,
        created: response.created,
        updated: response.updated,
        contentLength: response.content?.length
      };
    }

    if (Array.isArray(response)) {
      return {
        count: response.length,
        items: response.slice(0, 3).map(item => ({
          guid: item.guid,
          title: item.title || item.name
        }))
      };
    }

    return response;
  }

  writeToFile(entry) {
    const filePath = path.join(this.logDir, this.logFile);
    const line = JSON.stringify(entry) + '\n';

    try {
      fs.appendFileSync(filePath, line);
      this.rotateIfNeeded(filePath);
    } catch (error) {
      console.error('Failed to write debug log:', error.message);
    }
  }

  rotateIfNeeded(filePath) {
    try {
      const stats = fs.statSync(filePath);
      if (stats.size > this.maxLogSize) {
        const rotated = `${filePath}.${Date.now()}`;
        fs.renameSync(filePath, rotated);
      }
    } catch (error) {
      // Ignore rotation errors
    }
  }
}

module.exports = EvernoteDebugLogger;
```

### Step 2: Instrumented Client Wrapper

```javascript
// utils/instrumented-client.js
const Evernote = require('evernote');
const EvernoteDebugLogger = require('./debug-logger');

class InstrumentedEvernoteClient {
  constructor(client, logger = null) {
    this.client = client;
    this.logger = logger || new EvernoteDebugLogger();
    this._noteStore = null;
    this._userStore = null;
  }

  get noteStore() {
    if (!this._noteStore) {
      this._noteStore = this.wrapStore(
        this.client.getNoteStore(),
        'NoteStore'
      );
    }
    return this._noteStore;
  }

  get userStore() {
    if (!this._userStore) {
      this._userStore = this.wrapStore(
        this.client.getUserStore(),
        'UserStore'
      );
    }
    return this._userStore;
  }

  wrapStore(store, storeName) {
    const logger = this.logger;

    return new Proxy(store, {
      get(target, prop) {
        const original = target[prop];

        if (typeof original !== 'function') {
          return original;
        }

        return async (...args) => {
          const operation = `${storeName}.${prop}`;
          const startTime = Date.now();

          logger.logRequest(operation, {
            args: args.map((arg, i) => ({
              index: i,
              type: typeof arg,
              value: typeof arg === 'object' ? arg : String(arg).substring(0, 100)
            }))
          });

          try {
            const result = await original.apply(target, args);
            const duration = Date.now() - startTime;

            logger.logResponse(operation, {
              duration,
              result
            });

            return result;
          } catch (error) {
            const duration = Date.now() - startTime;

            logger.logError(operation, {
              duration,
              error
            });

            throw error;
          }
        };
      }
    });
  }
}

module.exports = InstrumentedEvernoteClient;
```

### Step 3: ENML Validator

```javascript
// utils/enml-validator.js

class ENMLValidator {
  static validate(content) {
    const errors = [];
    const warnings = [];

    // Required structure
    if (!content.includes('<?xml version="1.0"')) {
      errors.push({
        type: 'MISSING_XML_DECLARATION',
        message: 'Missing XML declaration',
        fix: 'Add: <?xml version="1.0" encoding="UTF-8"?>'
      });
    }

    if (!content.includes('<!DOCTYPE en-note')) {
      errors.push({
        type: 'MISSING_DOCTYPE',
        message: 'Missing DOCTYPE declaration',
        fix: 'Add: <!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
      });
    }

    if (!/<en-note[^>]*>/.test(content)) {
      errors.push({
        type: 'MISSING_ROOT',
        message: 'Missing <en-note> root element',
        fix: 'Wrap content in <en-note>...</en-note>'
      });
    }

    if (!content.includes('</en-note>')) {
      errors.push({
        type: 'UNCLOSED_ROOT',
        message: 'Missing closing </en-note> tag',
        fix: 'Add closing </en-note> tag'
      });
    }

    // Forbidden elements
    const forbidden = [
      { pattern: /<script/i, element: 'script' },
      { pattern: /<form/i, element: 'form' },
      { pattern: /<input/i, element: 'input' },
      { pattern: /<button/i, element: 'button' },
      { pattern: /<iframe/i, element: 'iframe' },
      { pattern: /<object/i, element: 'object' },
      { pattern: /<embed/i, element: 'embed' },
      { pattern: /<applet/i, element: 'applet' },
      { pattern: /<meta/i, element: 'meta' },
      { pattern: /<link/i, element: 'link' },
      { pattern: /<style/i, element: 'style' }
    ];

    forbidden.forEach(({ pattern, element }) => {
      if (pattern.test(content)) {
        errors.push({
          type: 'FORBIDDEN_ELEMENT',
          message: `Forbidden element: <${element}>`,
          fix: `Remove all <${element}> elements`
        });
      }
    });

    // Forbidden attributes
    const forbiddenAttrs = [
      { pattern: /\sclass\s*=/i, attr: 'class' },
      { pattern: /\sid\s*=/i, attr: 'id' },
      { pattern: /\sonclick\s*=/i, attr: 'onclick' },
      { pattern: /\sonload\s*=/i, attr: 'onload' },
      { pattern: /\sonerror\s*=/i, attr: 'onerror' },
      { pattern: /\sonmouseover\s*=/i, attr: 'onmouseover' }
    ];

    forbiddenAttrs.forEach(({ pattern, attr }) => {
      if (pattern.test(content)) {
        errors.push({
          type: 'FORBIDDEN_ATTRIBUTE',
          message: `Forbidden attribute: ${attr}`,
          fix: `Remove all ${attr}="..." attributes`
        });
      }
    });

    // Unclosed tags (basic check)
    const voidElements = ['br', 'hr', 'img', 'en-media', 'en-todo', 'en-crypt'];
    const unclosedPattern = /<(br|hr|img|en-media|en-todo)(?![^>]*\/>)[^>]*>/gi;
    const unclosed = content.match(unclosedPattern);
    if (unclosed) {
      unclosed.forEach(tag => {
        warnings.push({
          type: 'UNCLOSED_VOID_ELEMENT',
          message: `Void element should be self-closing: ${tag}`,
          fix: 'Use self-closing syntax: <br/>, <hr/>, etc.'
        });
      });
    }

    // Check en-media hash format
    const mediaPattern = /<en-media[^>]*hash="([^"]*)"[^>]*>/gi;
    let match;
    while ((match = mediaPattern.exec(content)) !== null) {
      const hash = match[1];
      if (!/^[a-f0-9]{32}$/i.test(hash)) {
        errors.push({
          type: 'INVALID_MEDIA_HASH',
          message: `Invalid MD5 hash in en-media: ${hash}`,
          fix: 'Use valid 32-character MD5 hex hash'
        });
      }
    }

    // Size warning
    const sizeBytes = Buffer.byteLength(content, 'utf8');
    const sizeMB = sizeBytes / (1024 * 1024);
    if (sizeMB > 25) {
      warnings.push({
        type: 'LARGE_CONTENT',
        message: `Note content is large: ${sizeMB.toFixed(2)} MB`,
        fix: 'Consider splitting into multiple notes'
      });
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      stats: {
        sizeBytes,
        sizeMB: sizeMB.toFixed(2),
        hasTodos: /<en-todo/.test(content),
        hasMedia: /<en-media/.test(content),
        hasEncryption: /<en-crypt/.test(content)
      }
    };
  }

  static fix(content) {
    let fixed = content;

    // Add missing XML declaration
    if (!fixed.includes('<?xml version="1.0"')) {
      fixed = '<?xml version="1.0" encoding="UTF-8"?>\n' + fixed;
    }

    // Add missing DOCTYPE
    if (!fixed.includes('<!DOCTYPE en-note')) {
      fixed = fixed.replace(
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
      );
    }

    // Remove forbidden elements
    fixed = fixed.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
    fixed = fixed.replace(/<form[^>]*>[\s\S]*?<\/form>/gi, '');
    fixed = fixed.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
    fixed = fixed.replace(/<iframe[^>]*>[\s\S]*?<\/iframe>/gi, '');

    // Remove forbidden attributes
    fixed = fixed.replace(/\s(class|id|onclick|onload|onerror)="[^"]*"/gi, '');

    // Fix unclosed void elements
    fixed = fixed.replace(/<(br|hr)(?![^>]*\/>)([^>]*)>/gi, '<$1$2/>');

    return fixed;
  }
}

module.exports = ENMLValidator;
```

### Step 4: Token Inspector

```javascript
// utils/token-inspector.js

class TokenInspector {
  static async inspect(client) {
    const userStore = client.getUserStore();
    const noteStore = client.getNoteStore();

    const results = {
      timestamp: new Date().toISOString(),
      user: null,
      accounting: null,
      businessUser: null,
      notebooks: null,
      tags: null,
      errors: []
    };

    // User info
    try {
      const user = await userStore.getUser();
      results.user = {
        id: user.id,
        username: user.username,
        email: user.email,
        name: user.name,
        timezone: user.timezone,
        privilege: this.privilegeToString(user.privilege),
        created: new Date(user.created),
        updated: new Date(user.updated),
        active: user.active
      };

      if (user.accounting) {
        results.accounting = {
          uploadLimit: this.formatBytes(user.accounting.uploadLimit),
          uploaded: this.formatBytes(user.accounting.uploaded),
          remaining: this.formatBytes(
            user.accounting.uploadLimit - user.accounting.uploaded
          ),
          uploadLimitEnd: new Date(user.accounting.uploadLimitEnd),
          premiumServiceStart: user.accounting.premiumServiceStart ?
            new Date(user.accounting.premiumServiceStart) : null
        };
      }
    } catch (error) {
      results.errors.push({
        operation: 'getUser',
        error: error.message
      });
    }

    // Notebook count
    try {
      const notebooks = await noteStore.listNotebooks();
      results.notebooks = {
        count: notebooks.length,
        limit: 250,
        remaining: 250 - notebooks.length
      };
    } catch (error) {
      results.errors.push({
        operation: 'listNotebooks',
        error: error.message
      });
    }

    // Tag count
    try {
      const tags = await noteStore.listTags();
      results.tags = {
        count: tags.length,
        limit: 100000,
        remaining: 100000 - tags.length
      };
    } catch (error) {
      results.errors.push({
        operation: 'listTags',
        error: error.message
      });
    }

    return results;
  }

  static privilegeToString(privilege) {
    const map = {
      1: 'NORMAL',
      2: 'PREMIUM',
      3: 'VIP',
      5: 'MANAGER',
      7: 'SUPPORT',
      8: 'ADMIN'
    };
    return map[privilege] || 'UNKNOWN';
  }

  static formatBytes(bytes) {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    let i = 0;
    while (bytes >= 1024 && i < units.length - 1) {
      bytes /= 1024;
      i++;
    }
    return `${bytes.toFixed(2)} ${units[i]}`;
  }
}

module.exports = TokenInspector;
```

### Step 5: Diagnostic CLI

```javascript
// scripts/diagnose.js
require('dotenv').config();
const Evernote = require('evernote');
const TokenInspector = require('../utils/token-inspector');
const ENMLValidator = require('../utils/enml-validator');

async function runDiagnostics() {
  console.log('=== Evernote Diagnostic Report ===\n');

  // 1. Check environment
  console.log('1. Environment Check');
  console.log('-------------------');
  console.log('EVERNOTE_ACCESS_TOKEN:', process.env.EVERNOTE_ACCESS_TOKEN ? 'Set' : 'NOT SET');
  console.log('EVERNOTE_SANDBOX:', process.env.EVERNOTE_SANDBOX || 'Not set (defaulting to production)');
  console.log();

  if (!process.env.EVERNOTE_ACCESS_TOKEN) {
    console.error('ERROR: No access token configured');
    process.exit(1);
  }

  // 2. Test connection
  console.log('2. Connection Test');
  console.log('-----------------');

  const client = new Evernote.Client({
    token: process.env.EVERNOTE_ACCESS_TOKEN,
    sandbox: process.env.EVERNOTE_SANDBOX === 'true'
  });

  try {
    const inspection = await TokenInspector.inspect(client);

    if (inspection.user) {
      console.log('User:', inspection.user.username);
      console.log('Account type:', inspection.user.privilege);
      console.log('Active:', inspection.user.active);
    }

    if (inspection.accounting) {
      console.log('Upload quota:', inspection.accounting.remaining, 'remaining');
      console.log('Quota resets:', inspection.accounting.uploadLimitEnd);
    }

    if (inspection.notebooks) {
      console.log('Notebooks:', inspection.notebooks.count, '/', inspection.notebooks.limit);
    }

    if (inspection.tags) {
      console.log('Tags:', inspection.tags.count);
    }

    if (inspection.errors.length > 0) {
      console.log('\nErrors encountered:');
      inspection.errors.forEach(e => console.log(`  - ${e.operation}: ${e.error}`));
    }

  } catch (error) {
    console.error('Connection failed:', error.message);
    if (error.errorCode === 4) {
      console.error('Token is invalid. Please re-authenticate.');
    }
    if (error.errorCode === 5) {
      console.error('Token has expired. Please re-authenticate.');
    }
    process.exit(1);
  }

  // 3. Test note creation
  console.log('\n3. Note Creation Test');
  console.log('--------------------');

  const testContent = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note><p>Diagnostic test note</p></en-note>`;

  const validation = ENMLValidator.validate(testContent);
  console.log('ENML Validation:', validation.valid ? 'PASSED' : 'FAILED');
  if (!validation.valid) {
    validation.errors.forEach(e => console.log(`  Error: ${e.message}`));
  }

  console.log('\n=== Diagnostic Complete ===');
}

runDiagnostics().catch(console.error);
```

### Step 6: Package.json Scripts

```json
{
  "scripts": {
    "diagnose": "node scripts/diagnose.js",
    "diagnose:verbose": "EVERNOTE_DEBUG=true node scripts/diagnose.js",
    "validate:enml": "node -e \"require('./utils/enml-validator').validate(require('fs').readFileSync(process.argv[1], 'utf8'))\" --"
  }
}
```


## Usage

```bash
npm run diagnose

npm run diagnose:verbose

npm run validate:enml note-content.xml
```
