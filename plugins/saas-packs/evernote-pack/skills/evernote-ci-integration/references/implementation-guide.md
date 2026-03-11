# Evernote CI Integration - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: GitHub Actions Workflow

```yaml
name: Evernote Integration CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm run test:unit

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

  integration-tests:
    runs-on: ubuntu-latest
    needs: [lint, unit-tests]
    # Only run on main branch to preserve rate limits
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run integration tests
        env:
          EVERNOTE_CONSUMER_KEY: ${{ secrets.EVERNOTE_CONSUMER_KEY }}
          EVERNOTE_CONSUMER_SECRET: ${{ secrets.EVERNOTE_CONSUMER_SECRET }}
          EVERNOTE_ACCESS_TOKEN: ${{ secrets.EVERNOTE_SANDBOX_TOKEN }}
          EVERNOTE_SANDBOX: 'true'
        run: npm run test:integration

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Snyk security scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high
```

### Step 2: Test Configuration

```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'node',
  testMatch: [
    '**/tests/**/*.test.js'
  ],
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.test.js'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  setupFilesAfterEnv: ['./tests/setup.js'],

  // Separate test suites
  projects: [
    {
      displayName: 'unit',
      testMatch: ['<rootDir>/tests/unit/**/*.test.js']
    },
    {
      displayName: 'integration',
      testMatch: ['<rootDir>/tests/integration/**/*.test.js'],
      testTimeout: 30000
    }
  ]
};
```

```javascript
// tests/setup.js
const dotenv = require('dotenv');

// Load test environment
dotenv.config({ path: '.env.test' });

// Global test setup
beforeAll(() => {
  // Verify test environment
  if (process.env.NODE_ENV === 'production') {
    throw new Error('Cannot run tests in production environment');
  }

  // Ensure sandbox mode for Evernote tests
  if (process.env.EVERNOTE_SANDBOX !== 'true') {
    console.warn('WARNING: EVERNOTE_SANDBOX should be true for tests');
  }
});

// Global teardown
afterAll(async () => {
  // Clean up test resources
});
```

### Step 3: Mock Evernote Client for Unit Tests

```javascript
// tests/mocks/evernote-mock.js

class MockNoteStore {
  constructor() {
    this.notebooks = [];
    this.notes = [];
    this.tags = [];
  }

  async listNotebooks() {
    return this.notebooks;
  }

  async createNotebook(notebook) {
    const created = {
      ...notebook,
      guid: `notebook-${Date.now()}`,
      created: Date.now(),
      updated: Date.now()
    };
    this.notebooks.push(created);
    return created;
  }

  async listTags() {
    return this.tags;
  }

  async createNote(note) {
    // Validate ENML
    if (!note.content.includes('<?xml version="1.0"')) {
      const error = new Error('Invalid ENML');
      error.errorCode = 1;
      error.parameter = 'Note.content';
      throw error;
    }

    const created = {
      ...note,
      guid: `note-${Date.now()}`,
      created: Date.now(),
      updated: Date.now()
    };
    this.notes.push(created);
    return created;
  }

  async getNote(guid, withContent, withResources) {
    const note = this.notes.find(n => n.guid === guid);
    if (!note) {
      const error = new Error('Note not found');
      error.identifier = 'Note.guid';
      error.key = guid;
      throw error;
    }
    return note;
  }

  async findNotesMetadata(filter, offset, maxNotes, spec) {
    let filtered = [...this.notes];

    if (filter.words) {
      const words = filter.words.toLowerCase();
      filtered = filtered.filter(n =>
        n.title.toLowerCase().includes(words) ||
        n.content.toLowerCase().includes(words)
      );
    }

    return {
      notes: filtered.slice(offset, offset + maxNotes),
      totalNotes: filtered.length
    };
  }

  // Reset for tests
  reset() {
    this.notebooks = [];
    this.notes = [];
    this.tags = [];
  }
}

class MockUserStore {
  async getUser() {
    return {
      id: 12345,
      username: 'testuser',
      email: 'test@example.com',
      name: 'Test User',
      privilege: 1,
      created: Date.now() - 86400000,
      updated: Date.now(),
      active: true,
      accounting: {
        uploadLimit: 62914560,
        uploaded: 1000000,
        uploadLimitEnd: Date.now() + 86400000 * 30
      }
    };
  }
}

class MockEvernoteClient {
  constructor(options = {}) {
    this.options = options;
    this._noteStore = new MockNoteStore();
    this._userStore = new MockUserStore();
  }

  getNoteStore() {
    return this._noteStore;
  }

  getUserStore() {
    return this._userStore;
  }

  // For OAuth testing
  getRequestToken(callbackUrl, callback) {
    callback(null, 'mock-oauth-token', 'mock-oauth-secret');
  }

  getAuthorizeUrl(oauthToken) {
    return `https://sandbox.evernote.com/OAuth.action?oauth_token=${oauthToken}`;
  }

  getAccessToken(oauthToken, oauthTokenSecret, oauthVerifier, callback) {
    callback(null, 'mock-access-token', 'mock-access-secret', {
      edam_expires: String(Date.now() + 31536000000)
    });
  }
}

module.exports = {
  MockEvernoteClient,
  MockNoteStore,
  MockUserStore
};
```

### Step 4: Unit Test Examples

```javascript
// tests/unit/note-service.test.js
const { MockEvernoteClient } = require('../mocks/evernote-mock');
const NoteService = require('../../src/services/note-service');

describe('NoteService', () => {
  let noteService;
  let mockClient;

  beforeEach(() => {
    mockClient = new MockEvernoteClient();
    noteService = new NoteService(mockClient.getNoteStore());
  });

  describe('createNote', () => {
    it('should create a note with valid ENML', async () => {
      const result = await noteService.createNote({
        title: 'Test Note',
        content: '<p>Test content</p>'
      });

      expect(result.guid).toBeDefined();
      expect(result.title).toBe('Test Note');
    });

    it('should sanitize note title', async () => {
      const result = await noteService.createNote({
        title: 'Title\nwith\nnewlines',
        content: '<p>Content</p>'
      });

      expect(result.title).not.toContain('\n');
    });

    it('should reject invalid ENML', async () => {
      // Remove ENML wrapping for this test
      const badService = {
        noteStore: mockClient.getNoteStore(),
        createNote: async (params) => {
          const note = { title: params.title, content: params.content };
          return mockClient.getNoteStore().createNote(note);
        }
      };

      await expect(
        badService.createNote({
          title: 'Bad Note',
          content: '<p>No ENML wrapper</p>'
        })
      ).rejects.toMatchObject({
        errorCode: 1,
        parameter: 'Note.content'
      });
    });
  });

  describe('searchNotes', () => {
    beforeEach(async () => {
      // Seed test data
      await noteService.createNote({ title: 'Meeting Notes', content: '<p>Q1 Review</p>' });
      await noteService.createNote({ title: 'Todo List', content: '<p>Tasks</p>' });
    });

    it('should find notes by title', async () => {
      const results = await noteService.search('meeting');

      expect(results.notes.length).toBe(1);
      expect(results.notes[0].title).toContain('Meeting');
    });
  });
});
```

### Step 5: Integration Test Examples

```javascript
// tests/integration/evernote-api.test.js
const Evernote = require('evernote');

// Skip if no credentials
const hasCredentials = process.env.EVERNOTE_ACCESS_TOKEN;

(hasCredentials ? describe : describe.skip)('Evernote API Integration', () => {
  let client;
  let noteStore;
  let createdNoteGuids = [];

  beforeAll(() => {
    client = new Evernote.Client({
      token: process.env.EVERNOTE_ACCESS_TOKEN,
      sandbox: process.env.EVERNOTE_SANDBOX === 'true'
    });
    noteStore = client.getNoteStore();
  });

  afterAll(async () => {
    // Clean up created notes
    for (const guid of createdNoteGuids) {
      try {
        await noteStore.deleteNote(guid);
      } catch (error) {
        console.log(`Cleanup: Could not delete ${guid}`);
      }
    }
  });

  it('should authenticate and get user info', async () => {
    const userStore = client.getUserStore();
    const user = await userStore.getUser();

    expect(user.id).toBeDefined();
    expect(user.username).toBeDefined();
  });

  it('should list notebooks', async () => {
    const notebooks = await noteStore.listNotebooks();

    expect(Array.isArray(notebooks)).toBe(true);
    expect(notebooks.length).toBeGreaterThan(0);
  });

  it('should create and retrieve a note', async () => {
    const testTitle = `CI Test Note - ${Date.now()}`;
    const content = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note><p>Integration test content</p></en-note>`;

    const note = new Evernote.Types.Note();
    note.title = testTitle;
    note.content = content;

    const created = await noteStore.createNote(note);
    createdNoteGuids.push(created.guid);

    expect(created.guid).toBeDefined();
    expect(created.title).toBe(testTitle);

    // Retrieve and verify
    const retrieved = await noteStore.getNote(created.guid, true, false, false, false);
    expect(retrieved.content).toContain('Integration test content');
  });

  it('should handle rate limits gracefully', async () => {
    // This test intentionally makes multiple calls
    // to verify rate limit handling works

    const promises = [];
    for (let i = 0; i < 5; i++) {
      promises.push(noteStore.listNotebooks());
    }

    const results = await Promise.all(promises);
    expect(results.every(r => Array.isArray(r))).toBe(true);
  }, 30000);
});
```

### Step 6: Secrets Management

```yaml


```

```yaml
jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment: production  # Requires approval

    steps:
      - uses: actions/checkout@v4

      - name: Deploy
        env:
          EVERNOTE_CONSUMER_KEY: ${{ secrets.EVERNOTE_PROD_CONSUMER_KEY }}
          EVERNOTE_CONSUMER_SECRET: ${{ secrets.EVERNOTE_PROD_CONSUMER_SECRET }}
        run: npm run deploy
```

### Step 7: Package.json Scripts

```json
{
  "scripts": {
    "test": "jest",
    "test:unit": "jest --selectProjects unit",
    "test:integration": "jest --selectProjects integration --runInBand",
    "test:coverage": "jest --coverage",
    "lint": "eslint src/ tests/",
    "lint:fix": "eslint src/ tests/ --fix",
    "typecheck": "tsc --noEmit",
    "ci": "npm run lint && npm run typecheck && npm run test:unit",
    "ci:full": "npm run ci && npm run test:integration"
  }
}
```


## Best Practices

| Practice | Reason |
|----------|--------|
| Run unit tests on every PR | Fast feedback, no API usage |
| Limit integration tests | Preserve rate limits |
| Use sandbox for all CI | Never test against production |
| Store secrets securely | Protect API credentials |
| Clean up test data | Don't leave garbage in sandbox |
