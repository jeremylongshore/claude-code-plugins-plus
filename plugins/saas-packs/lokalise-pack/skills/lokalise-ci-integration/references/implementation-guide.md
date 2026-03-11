# Lokalise CI Integration - Implementation Guide

Detailed implementation reference for the lokalise-ci-integration skill.

## Instructions

### Step 1: Push Source Strings on Merge
```yaml
# .github/workflows/lokalise-push.yml
name: Push Source Strings to Lokalise

on:
  push:
    branches: [main]
    paths:
      - 'src/locales/en.json'
      - 'src/locales/en/**'

jobs:
  push-translations:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Lokalise CLI
        run: |
          curl -sfL https://raw.githubusercontent.com/nicholasgasior/gvm/master/bin/gvm | bash
          npm install -g @lokalise/cli2

      - name: Push source strings
        env:
          LOKALISE_API_TOKEN: ${{ secrets.LOKALISE_API_TOKEN }}
          LOKALISE_PROJECT_ID: ${{ secrets.LOKALISE_PROJECT_ID }}
        run: |
          lokalise2 file upload \
            --token "$LOKALISE_API_TOKEN" \
            --project-id "$LOKALISE_PROJECT_ID" \
            --file "src/locales/en.json" \
            --lang-iso "en" \
            --replace-modified \
            --distinguish-by-file \
            --poll \
            --poll-timeout 120
```

### Step 2: Pull Translations Before Build
```yaml
# .github/workflows/build-with-translations.yml
name: Build with Latest Translations

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Pull translations from Lokalise
        env:
          LOKALISE_API_TOKEN: ${{ secrets.LOKALISE_API_TOKEN }}
          LOKALISE_PROJECT_ID: ${{ secrets.LOKALISE_PROJECT_ID }}
        run: |
          lokalise2 file download \
            --token "$LOKALISE_API_TOKEN" \
            --project-id "$LOKALISE_PROJECT_ID" \
            --format json \
            --original-filenames true \
            --directory-prefix "" \
            --export-empty-as "skip" \
            --unzip-to "src/locales/"

      - name: Check for translation changes
        run: |
          if git diff --quiet src/locales/; then
            echo "No translation changes"
          else
            echo "TRANSLATIONS_CHANGED=true" >> $GITHUB_ENV
            git diff --stat src/locales/
          fi

      - name: Build application
        run: npm ci && npm run build
```

### Step 3: Translation Completeness Check on PR
```yaml
# .github/workflows/translation-check.yml
name: Translation Completeness

on:
  pull_request:
    paths:
      - 'src/locales/**'

jobs:
  check-translations:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check translation completeness
        run: |
          node -e "
            const en = require('./src/locales/en.json');
            const enKeys = Object.keys(en).length;
            const locales = ['es', 'fr', 'de', 'ja'];
            let allGood = true;

            console.log('| Locale | Keys | Coverage |');
            console.log('|--------|------|----------|');

            for (const locale of locales) {
              try {
                const trans = require('./src/locales/' + locale + '.json');
                const transKeys = Object.keys(trans).length;
                const pct = ((transKeys / enKeys) * 100).toFixed(1);
                const status = transKeys >= enKeys ? 'OK' : 'INCOMPLETE';
                console.log('| ' + locale + ' | ' + transKeys + '/' + enKeys + ' | ' + pct + '% ' + status + ' |');
                if (transKeys < enKeys) allGood = false;
              } catch {
                console.log('| ' + locale + ' | MISSING | 0% |');
                allGood = false;
              }
            }

            if (!allGood) {
              console.log('\\nWARNING: Some translations are incomplete');
              process.exit(0); // Warn but don't fail
            }
          " >> $GITHUB_STEP_SUMMARY
```

### Step 4: Webhook-Triggered Deploy
```yaml
# .github/workflows/lokalise-webhook.yml
name: Deploy on Translation Update

on:
  repository_dispatch:
    types: [lokalise-translations-updated]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Pull latest translations
        env:
          LOKALISE_API_TOKEN: ${{ secrets.LOKALISE_API_TOKEN }}
          LOKALISE_PROJECT_ID: ${{ secrets.LOKALISE_PROJECT_ID }}
        run: |
          lokalise2 file download \
            --token "$LOKALISE_API_TOKEN" \
            --project-id "$LOKALISE_PROJECT_ID" \
            --format json \
            --unzip-to "src/locales/"

      - name: Commit and deploy
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add src/locales/
          git diff --staged --quiet || git commit -m "chore: update translations from Lokalise"
          git push
```

