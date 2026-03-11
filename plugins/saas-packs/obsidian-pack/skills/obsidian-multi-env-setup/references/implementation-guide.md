# Obsidian Multi-Environment Setup - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Create Environment Structure
```bash
#!/bin/bash

OBSIDIAN_ENVS="$HOME/ObsidianEnvs"

mkdir -p "$OBSIDIAN_ENVS/development/.obsidian/plugins"
mkdir -p "$OBSIDIAN_ENVS/development/Test Notes"
mkdir -p "$OBSIDIAN_ENVS/testing/.obsidian/plugins"
mkdir -p "$OBSIDIAN_ENVS/testing/Test Notes"
mkdir -p "$OBSIDIAN_ENVS/staging/.obsidian/plugins"

echo "Created Obsidian environments at: $OBSIDIAN_ENVS"

cat > "$OBSIDIAN_ENVS/development/Test Notes/Welcome.md" << 'EOF'

This vault is for **active plugin development**.


## Complete Examples

### Quick Environment Reset Script
```bash
#!/bin/bash

TESTING_VAULT="$HOME/ObsidianEnvs/testing"

rm -rf "$TESTING_VAULT/Test Notes"/*

npx ts-node scripts/generate-test-data.ts

./setup-testing-vault.sh

echo "Testing environment reset complete"
```

### Environment Indicator Component
```typescript
// src/ui/components/env-indicator.ts
import { Plugin } from 'obsidian';
import { getEnvironment } from '../config/environment';

export function addEnvironmentIndicator(plugin: Plugin): void {
  const env = getEnvironment();

  if (env !== 'production') {
    const statusBar = plugin.addStatusBarItem();
    statusBar.setText(`[${env.toUpperCase()}]`);
    statusBar.addClass(`env-indicator-${env}`);
  }
}
```


## Environment Types

| Environment | Purpose | Plugin Source | Data |
|-------------|---------|---------------|------|
| Development | Active coding | Symlinked (live) | Test data |
| Testing | QA/Validation | Built release | Test data |
| Production | Real usage | Community/Release | Real notes |


## Test Content

- [[Link to test]]
- #test-tag
- Regular content


## Frontmatter Test

---
title: Test Note
tags: [development, test]
created: 2024-01-01
---
EOF

cat > "$OBSIDIAN_ENVS/testing/Test Notes/Welcome.md" << 'EOF'

This vault is for **QA and validation testing**.


## Test Scenarios

- [ ] Basic functionality
- [ ] Edge cases
- [ ] Performance
- [ ] Mobile compatibility
EOF

echo "Created test notes"
```

### Step 2: Link Plugin to Development Environment
```bash
#!/bin/bash

PLUGIN_DIR="$HOME/projects/my-obsidian-plugin"
DEV_VAULT="$HOME/ObsidianEnvs/development"
PLUGIN_NAME=$(jq -r '.id' "$PLUGIN_DIR/manifest.json")

ln -sf "$PLUGIN_DIR" "$DEV_VAULT/.obsidian/plugins/$PLUGIN_NAME"

echo "Linked $PLUGIN_NAME to development vault"
echo "Plugin source: $PLUGIN_DIR"
echo "Vault location: $DEV_VAULT/.obsidian/plugins/$PLUGIN_NAME"
```

### Step 3: Configure Environment-Specific Settings
```typescript
// src/config/environment.ts
export type Environment = 'development' | 'testing' | 'production';

export interface EnvironmentConfig {
  debug: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  apiEndpoint: string;
  features: {
    experimental: boolean;
    analytics: boolean;
  };
}

const configs: Record<Environment, EnvironmentConfig> = {
  development: {
    debug: true,
    logLevel: 'debug',
    apiEndpoint: 'http://localhost:3000',
    features: {
      experimental: true,
      analytics: false,
    },
  },
  testing: {
    debug: true,
    logLevel: 'info',
    apiEndpoint: 'https://staging.api.example.com',
    features: {
      experimental: true,
      analytics: false,
    },
  },
  production: {
    debug: false,
    logLevel: 'error',
    apiEndpoint: 'https://api.example.com',
    features: {
      experimental: false,
      analytics: true,
    },
  },
};

export function getEnvironment(): Environment {
  // Detect based on vault name or build mode
  if (process.env.NODE_ENV === 'production') {
    return 'production';
  }

  // Could also detect from vault path
  return 'development';
}

export function getConfig(): EnvironmentConfig {
  return configs[getEnvironment()];
}
```

### Step 4: Testing Vault Configuration
```bash
#!/bin/bash

TESTING_VAULT="$HOME/ObsidianEnvs/testing"
PLUGIN_DIR="$HOME/projects/my-obsidian-plugin"

cd "$PLUGIN_DIR"
npm run build

PLUGIN_NAME=$(jq -r '.id' manifest.json)
TEST_PLUGIN_DIR="$TESTING_VAULT/.obsidian/plugins/$PLUGIN_NAME"

mkdir -p "$TEST_PLUGIN_DIR"
cp main.js manifest.json "$TEST_PLUGIN_DIR/"
[ -f styles.css ] && cp styles.css "$TEST_PLUGIN_DIR/"

echo "Copied release build to testing vault"
```

### Step 5: Automated Environment Switching
```bash
#!/bin/bash

ENV=$1
BASE_DIR="$HOME/ObsidianEnvs"

case $ENV in
  dev|development)
    open "obsidian://open?vault=$BASE_DIR/development"
    echo "Opening development vault"
    ;;
  test|testing)
    open "obsidian://open?vault=$BASE_DIR/testing"
    echo "Opening testing vault"
    ;;
  stage|staging)
    open "obsidian://open?vault=$BASE_DIR/staging"
    echo "Opening staging vault"
    ;;
  prod|production)
    echo "Opening production vault (your main vault)"
    # Update with your production vault path
    open "obsidian://open?vault=$HOME/MyNotes"
    ;;
  *)
    echo "Usage: obsidian-env [dev|test|stage|prod]"
    exit 1
    ;;
esac
```

### Step 6: Test Data Generation
```typescript
// scripts/generate-test-data.ts
import * as fs from 'fs';
import * as path from 'path';

const TEST_VAULT = process.env.TEST_VAULT || './test-vault';

interface TestNote {
  name: string;
  content: string;
  frontmatter?: Record<string, any>;
}

const testNotes: TestNote[] = [
  {
    name: 'Empty Note.md',
    content: '',
  },
  {
    name: 'Simple Note.md',
    content: '# Simple Note\n\nJust some content.',
  },
  {
    name: 'Note with Links.md',
    content: '# Links Test\n\n[[Simple Note]]\n[[Nonexistent Link]]\n\n![[Simple Note]]',
  },
  {
    name: 'Note with Frontmatter.md',
    frontmatter: {
      title: 'Frontmatter Test',
      tags: ['test', 'frontmatter'],
      date: '2024-01-15',
      nested: {
        key: 'value',
      },
    },
    content: '# Frontmatter Test\n\nThis note has frontmatter.',
  },
  {
    name: 'Special Characters !@#.md',
    content: '# Special Characters\n\nNote with special chars in filename.',
  },
  {
    name: 'Long Note.md',
    content: generateLongContent(1000),
  },
];

function generateLongContent(lines: number): string {
  const paragraphs = [];
  for (let i = 0; i < lines; i++) {
    paragraphs.push(`Paragraph ${i + 1}: Lorem ipsum dolor sit amet.`);
  }
  return '# Long Note\n\n' + paragraphs.join('\n\n');
}

function formatFrontmatter(fm: Record<string, any>): string {
  const yaml = Object.entries(fm)
    .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
    .join('\n');
  return `---\n${yaml}\n---\n\n`;
}

async function generateTestData() {
  const notesDir = path.join(TEST_VAULT, 'Test Notes');
  fs.mkdirSync(notesDir, { recursive: true });

  for (const note of testNotes) {
    const content = note.frontmatter
      ? formatFrontmatter(note.frontmatter) + note.content
      : note.content;

    const filePath = path.join(notesDir, note.name);
    fs.writeFileSync(filePath, content);
    console.log(`Created: ${note.name}`);
  }

  // Create nested folder structure
  const folders = [
    'Folder A/Subfolder 1',
    'Folder A/Subfolder 2',
    'Folder B',
    '.hidden-folder',
  ];

  for (const folder of folders) {
    const folderPath = path.join(TEST_VAULT, folder);
    fs.mkdirSync(folderPath, { recursive: true });
    fs.writeFileSync(
      path.join(folderPath, 'Note.md'),
      `# Note in ${folder}\n\nContent.`
    );
  }

  console.log('Test data generation complete!');
}

generateTestData();
```

### Step 7: CI Integration for Environments
```yaml
name: Test in Multiple Environments

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        obsidian-version: ['1.4.0', '1.5.0', 'latest']

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Generate test vault
        run: |
          mkdir -p test-vault/.obsidian/plugins/my-plugin
          cp main.js manifest.json test-vault/.obsidian/plugins/my-plugin/

      - name: Run tests
        run: npm test
        env:
          TEST_VAULT: ./test-vault
          OBSIDIAN_VERSION: ${{ matrix.obsidian-version }}
```
