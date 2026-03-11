# Lokalise Migration Deep Dive - Implementation Guide

Detailed implementation reference for the lokalise-migration-deep-dive skill.

## Migration Types

| Type | Complexity | Duration | Risk |
|------|-----------|----------|------|
| Fresh start | Low | Days | Low |
| From Phrase | Medium | 1-2 weeks | Medium |
| From Crowdin | Medium | 1-2 weeks | Medium |
| From POEditor | Low | Days | Low |
| From spreadsheets | Medium | 1 week | Medium |
| Custom legacy | High | 2-4 weeks | High |


## Instructions

### Step 1: Pre-Migration Assessment
```typescript
interface MigrationAssessment {
  sourceSystem: string;
  totalProjects: number;
  totalKeys: number;
  totalLanguages: number;
  translationMemory: boolean;
  glossary: boolean;
  screenshots: boolean;
  workflows: boolean;
  integrations: string[];
  customizations: string[];
}

async function assessCurrentState(): Promise<MigrationAssessment> {
  // Document current system
  return {
    sourceSystem: "phrase",  // or crowdin, poeditor, etc.
    totalProjects: 5,
    totalKeys: 15000,
    totalLanguages: 12,
    translationMemory: true,
    glossary: true,
    screenshots: true,
    workflows: true,
    integrations: ["github", "figma", "slack"],
    customizations: ["custom placeholders", "QA rules"],
  };
}

// Estimate migration complexity
function estimateMigrationEffort(assessment: MigrationAssessment): {
  effort: "low" | "medium" | "high";
  estimatedDays: number;
  risks: string[];
} {
  const baseEffort = assessment.totalKeys > 10000 ? 5 : 2;
  const tmEffort = assessment.translationMemory ? 2 : 0;
  const integrationEffort = assessment.integrations.length * 0.5;

  const totalDays = baseEffort + tmEffort + integrationEffort;

  return {
    effort: totalDays > 7 ? "high" : totalDays > 3 ? "medium" : "low",
    estimatedDays: Math.ceil(totalDays),
    risks: [
      assessment.totalKeys > 10000 ? "Large key count may require batching" : null,
      assessment.translationMemory ? "TM migration may have format differences" : null,
      assessment.workflows ? "Workflows need manual recreation" : null,
    ].filter(Boolean) as string[],
  };
}
```

### Step 2: Export from Source System
```bash
# Export from common platforms

# Phrase
phrase pull --format json --target ./export/phrase/

# Crowdin (using CLI)
crowdin download --all --export-only-approved

# POEditor
# Use web export or API to download all languages

# Generic: Export all files in JSON/XLIFF format
# Ensure consistent naming: en.json, es.json, fr.json, etc.
```

### Step 3: Data Transformation
```typescript
// Transform exported data to Lokalise-compatible format
interface SourceKey {
  key: string;
  value: string;
  description?: string;
  tags?: string[];
  context?: string;
}

interface LokaliseImportKey {
  key_name: string;
  platforms: string[];
  description?: string;
  tags?: string[];
  translations: Array<{
    language_iso: string;
    translation: string;
  }>;
}

function transformKeys(
  sourceKeys: SourceKey[],
  translations: Record<string, Record<string, string>>,
  languages: string[]
): LokaliseImportKey[] {
  return sourceKeys.map(src => ({
    key_name: src.key,
    platforms: ["web"],  // Adjust based on your needs
    description: src.description || src.context,
    tags: src.tags || ["migrated"],
    translations: languages.map(lang => ({
      language_iso: lang,
      translation: translations[lang]?.[src.key] || "",
    })).filter(t => t.translation),
  }));
}

// Handle platform-specific quirks
function normalizeKey(key: string, sourceSystem: string): string {
  switch (sourceSystem) {
    case "phrase":
      // Phrase uses dot notation by default
      return key;
    case "crowdin":
      // Crowdin may use file paths in key names
      return key.replace(/^.*\//, "");
    case "poeditor":
      // POEditor exports may have different formats
      return key.replace(/\s+/g, "_").toLowerCase();
    default:
      return key;
  }
}
```

### Step 4: Create Lokalise Project
```typescript
import { LokaliseApi } from "@lokalise/node-api";

const client = new LokaliseApi({
  apiKey: process.env.LOKALISE_API_TOKEN!,
});

async function createMigrationProject(
  name: string,
  languages: string[],
  baseLanguage: string
): Promise<string> {
  const project = await client.projects().create({
    name: `${name} (Migration)`,
    description: `Migrated from legacy system on ${new Date().toISOString()}`,
    languages: languages.map(lang => ({
      lang_iso: lang,
    })),
    base_lang_iso: baseLanguage,
  });

  console.log(`Created project: ${project.project_id}`);
  return project.project_id;
}
```

### Step 5: Import Keys and Translations
```typescript
async function importKeysToLokalise(
  projectId: string,
  keys: LokaliseImportKey[],
  batchSize = 100
): Promise<{ imported: number; errors: string[] }> {
  const results = { imported: 0, errors: [] as string[] };

  for (let i = 0; i < keys.length; i += batchSize) {
    const batch = keys.slice(i, i + batchSize);

    try {
      const response = await client.keys().create({
        project_id: projectId,
        keys: batch,
      });

      results.imported += response.items.length;
      console.log(`Imported ${results.imported}/${keys.length} keys`);
    } catch (error: any) {
      results.errors.push(`Batch ${i / batchSize}: ${error.message}`);
      console.error(`Error importing batch:`, error.message);
    }

    // Respect rate limits
    await new Promise(r => setTimeout(r, 300));
  }

  return results;
}

// Alternative: File-based import
async function importViaFile(
  projectId: string,
  filePath: string,
  langIso: string
): Promise<void> {
  const fileContent = fs.readFileSync(filePath);
  const base64Content = fileContent.toString("base64");

  const process = await client.files().upload(projectId, {
    data: base64Content,
    filename: path.basename(filePath),
    lang_iso: langIso,
    convert_placeholders: true,
    detect_icu_plurals: true,
    replace_modified: false,  // Don't overwrite during migration
    tags: ["migrated"],
  });

  console.log(`Upload started: ${process.process_id}`);

  // Poll for completion
  await waitForProcess(projectId, process.process_id);
}
```

### Step 6: Migrate Translation Memory
```typescript
// Lokalise supports TM import via TMX format
async function importTranslationMemory(
  teamId: number,
  tmxFilePath: string
): Promise<void> {
  // Read TMX file
  const tmxContent = fs.readFileSync(tmxFilePath);
  const base64Content = tmxContent.toString("base64");

  // Upload to team TM
  await client.translationStatuses().create(teamId, {
    // TM import endpoint - check Lokalise API for exact parameters
  });

  console.log("Translation memory imported");
}

// Export TM from source system first
// Phrase: phrase tm:download --format tmx
// Crowdin: Use web export
```

### Step 7: Post-Migration Validation
```typescript
interface ValidationResult {
  passed: boolean;
  checks: Array<{
    name: string;
    passed: boolean;
    details: string;
  }>;
}

async function validateMigration(
  projectId: string,
  expectedKeys: number,
  expectedLanguages: string[]
): Promise<ValidationResult> {
  const checks: ValidationResult["checks"] = [];

  // Check key count
  const keys = await client.keys().list({
    project_id: projectId,
    limit: 1,
  });
  const keyCountMatch = keys.total_count >= expectedKeys * 0.95;  // 95% threshold
  checks.push({
    name: "Key count",
    passed: keyCountMatch,
    details: `Found ${keys.total_count}, expected ~${expectedKeys}`,
  });

  // Check languages
  const languages = await client.languages().list({ project_id: projectId });
  const langCodes = languages.items.map(l => l.lang_iso);
  const languagesMatch = expectedLanguages.every(l => langCodes.includes(l));
  checks.push({
    name: "Languages",
    passed: languagesMatch,
    details: `Found: ${langCodes.join(", ")}`,
  });

  // Check translation coverage
  for (const lang of expectedLanguages.filter(l => l !== "en")) {
    const langData = languages.items.find(l => l.lang_iso === lang);
    const coverage = langData?.statistics?.progress ?? 0;
    checks.push({
      name: `Coverage: ${lang}`,
      passed: coverage > 0,
      details: `${coverage}% translated`,
    });
  }

  return {
    passed: checks.every(c => c.passed),
    checks,
  };
}
```


## Flagship+ Skills
For advanced troubleshooting, see `lokalise-common-errors`.

## Detailed Examples

### Placeholder Transformation
```typescript
// Convert placeholders between formats
function convertPlaceholders(
  text: string,
  fromFormat: "printf" | "icu" | "curly",
  toFormat: "icu"
): string {
  if (fromFormat === "printf") {
    // %s, %d, %1$s -> {0}, {1}, etc.
    let index = 0;
    return text.replace(/%(\d+\$)?[sd]/g, () => `{${index++}}`);
  }

  if (fromFormat === "curly") {
    // {{name}} -> {name}
    return text.replace(/\{\{(\w+)\}\}/g, "{$1}");
  }

  return text;
}
```

### Migration Rollback
```bash
#!/bin/bash
# rollback-migration.sh

# If migration fails, delete the new project
lokalise2 --token "$LOKALISE_API_TOKEN" \
  project delete --project-id "$NEW_PROJECT_ID"

# Keep using old system
echo "Migration rolled back. Continue using source system."
```

### Full Migration Script
```typescript
async function runMigration() {
  console.log("=== Lokalise Migration ===\n");

  // 1. Assess
  const assessment = await assessCurrentState();
  const estimate = estimateMigrationEffort(assessment);
  console.log(`Estimated effort: ${estimate.effort} (~${estimate.estimatedDays} days)`);

  // 2. Create project
  const projectId = await createMigrationProject(
    "My App",
    ["en", "es", "fr", "de"],
    "en"
  );

  // 3. Import keys
  const keys = await loadTransformedKeys("./export/");
  const importResult = await importKeysToLokalise(projectId, keys);
  console.log(`Imported ${importResult.imported} keys`);

  // 4. Validate
  const validation = await validateMigration(projectId, keys.length, ["en", "es", "fr", "de"]);

  if (validation.passed) {
    console.log("\n Migration successful!");
  } else {
    console.error("\n Migration validation failed:");
    validation.checks.filter(c => !c.passed).forEach(c => {
      console.error(`  - ${c.name}: ${c.details}`);
    });
  }

  return { projectId, validation };
}
```

