# Guidewire Upgrade & Migration - Implementation Guide

## Version Upgrade Planning

### Guidewire Release Cadence

| Release Type | Frequency | Support Period | Example |
|--------------|-----------|----------------|---------|
| Major | Annual | 3 years | 2024.x |
| Minor | Quarterly | Until next minor | 202503 |
| Patch | Monthly | Until next patch | 202503.1 |

### Upgrade Path Matrix

```
Current Version     Target Version      Recommended Path
---------------     --------------      ----------------
2022.x             2024.x              2022 -> 2023 -> 2024
2023.x             2024.x              2023 -> 2024
On-Premise 10.x    Cloud 2024.x        Direct migration with PCF
```

## Instructions

### Step 1: Assess Current State

```bash
#!/bin/bash
# assess-current-version.sh

echo "=== Guidewire Version Assessment ==="

# Check current version from build files
CURRENT_VERSION=$(grep -m1 'guidewire.version' gradle.properties | cut -d= -f2)
echo "Current Guidewire Version: $CURRENT_VERSION"

# List custom Gosu files
echo ""
echo "Custom Gosu Files:"
find modules/configuration/gsrc -name "*.gs" -type f | wc -l
echo " Gosu source files"

# List PCF customizations
echo ""
echo "PCF Customizations:"
find modules/configuration/config -name "*.pcf" -type f | wc -l
echo " PCF files"

# List entity extensions
echo ""
echo "Entity Extensions:"
find modules/configuration/config -name "*_ext.xml" -type f | wc -l
echo " extension files"

# List integration points
echo ""
echo "Integration Points:"
grep -r "gw.api.rest" modules/configuration/gsrc --include="*.gs" | wc -l
echo " REST API integrations"

grep -r "gw.api.webservice" modules/configuration/gsrc --include="*.gs" | wc -l
echo " SOAP integrations"
```

### Step 2: Review Breaking Changes

```typescript
// Breaking change analysis script
interface BreakingChange {
  version: string;
  category: 'API' | 'Gosu' | 'Database' | 'Configuration';
  description: string;
  impact: 'High' | 'Medium' | 'Low';
  migration: string;
}

const breakingChanges: BreakingChange[] = [
  {
    version: '2024.03',
    category: 'API',
    description: 'Deprecated endpoints removed from Cloud API',
    impact: 'High',
    migration: 'Update to new endpoint paths - see migration guide'
  },
  {
    version: '2024.03',
    category: 'Gosu',
    description: 'Query API syntax changes for complex joins',
    impact: 'Medium',
    migration: 'Update Query.make() calls with new join syntax'
  },
  {
    version: '2024.01',
    category: 'Database',
    description: 'Column type changes for monetary amounts',
    impact: 'High',
    migration: 'Run provided migration script before upgrade'
  }
];

function analyzeImpact(currentVersion: string, targetVersion: string): void {
  const applicableChanges = breakingChanges.filter(change => {
    return compareVersions(change.version, currentVersion) > 0 &&
           compareVersions(change.version, targetVersion) <= 0;
  });

  console.log('=== Breaking Changes Analysis ===');
  console.log(`From: ${currentVersion} To: ${targetVersion}`);
  console.log(`Total breaking changes: ${applicableChanges.length}`);

  const byCategory = applicableChanges.reduce((acc, change) => {
    acc[change.category] = acc[change.category] || [];
    acc[change.category].push(change);
    return acc;
  }, {} as Record<string, BreakingChange[]>);

  Object.entries(byCategory).forEach(([category, changes]) => {
    console.log(`\n${category}:`);
    changes.forEach(change => {
      console.log(`  [${change.impact}] ${change.description}`);
      console.log(`    Migration: ${change.migration}`);
    });
  });
}
```

### Step 3: Database Upgrade

```groovy
// build.gradle - Database upgrade tasks
tasks.register('backupDatabase') {
    doLast {
        exec {
            commandLine 'pg_dump', '-h', dbHost, '-U', dbUser,
                       '-d', dbName, '-F', 'c',
                       '-f', "backup-${dbName}-${new Date().format('yyyyMMdd-HHmmss')}.dump"
        }
    }
}

tasks.register('upgradeDatabase') {
    dependsOn 'backupDatabase'
    doLast {
        // Run Guidewire database upgrade
        exec {
            commandLine './gradlew', 'dbupgrade',
                       "-PdbHost=${dbHost}",
                       "-PdbName=${dbName}",
                       "-PdbUser=${dbUser}",
                       "-PdbPassword=${dbPassword}"
        }
    }
}

tasks.register('validateDatabaseUpgrade') {
    dependsOn 'upgradeDatabase'
    doLast {
        // Verify schema version
        def result = exec {
            commandLine 'psql', '-h', dbHost, '-U', dbUser, '-d', dbName,
                       '-c', 'SELECT version FROM schema_version ORDER BY id DESC LIMIT 1'
            standardOutput = new ByteArrayOutputStream()
        }
        println "Current schema version: ${result.standardOutput}"
    }
}
```

### Step 4: Code Migration

```gosu
// Automated code migration helpers
package gw.migration

uses gw.api.util.Logger

class CodeMigrationHelper {
  private static final var LOG = Logger.forCategory("Migration")

  // Replace deprecated API calls
  static function migrateDeprecatedAPIs(code : String) : String {
    var migrated = code

    // Example: Migrate old Query syntax
    migrated = migrated.replaceAll(
      "Query\\.make\\(([^)]+)\\)\\.withEqual",
      "Query.make($1).compare"
    )

    // Example: Migrate old date handling
    migrated = migrated.replaceAll(
      "new Date\\(\\)",
      "Date.Today"
    )

    // Example: Migrate deprecated methods
    migrated = migrated.replaceAll(
      "\\.getBundle\\(\\)",
      ".Bundle"
    )

    return migrated
  }

  // Check for deprecated patterns
  static function findDeprecatedPatterns(code : String) : List<String> {
    var issues = new ArrayList<String>()

    var patterns = {
      "deprecated_query" -> "Query.make.*withEqual",
      "old_date" -> "new java.util.Date\\(\\)",
      "string_concat_in_query" -> "\"SELECT.*\\+.*\\+",
      "deprecated_session" -> "SessionInfo.getCurrentSession"
    }

    patterns.eachKeyAndValue(\name, pattern -> {
      if (code.matches(".*${pattern}.*")) {
        issues.add("Found deprecated pattern: ${name}")
      }
    })

    return issues
  }
}
```

### Step 5: Configuration Migration

```bash
#!/bin/bash
# migrate-configuration.sh

TARGET_VERSION="202503"
SOURCE_DIR="./modules/configuration"
BACKUP_DIR="./migration-backup-$(date +%Y%m%d)"

echo "=== Configuration Migration to $TARGET_VERSION ==="

# Backup current configuration
echo "Backing up current configuration..."
mkdir -p "$BACKUP_DIR"
cp -r "$SOURCE_DIR" "$BACKUP_DIR/"

# Update product model references
echo "Updating product model references..."
find "$SOURCE_DIR/config/products" -name "*.xml" -exec sed -i \
  's/xmlns="http:\/\/guidewire.com\/pc\/product\/[0-9]*"/xmlns="http:\/\/guidewire.com\/pc\/product\/'"$TARGET_VERSION"'"/' {} \;

# Update typelist references
echo "Updating typelist references..."
find "$SOURCE_DIR/config/typelist" -name "*.xml" -exec sed -i \
  's/schemaVersion="[0-9]*"/schemaVersion="'"$TARGET_VERSION"'"/' {} \;

# Validate XML files
echo "Validating XML files..."
find "$SOURCE_DIR/config" -name "*.xml" -exec xmllint --noout {} \; 2>&1

echo "Configuration migration complete"
```

### Step 6: Integration Migration

```typescript
// API version migration
interface EndpointMigration {
  oldPath: string;
  newPath: string;
  changes: string[];
}

const endpointMigrations: EndpointMigration[] = [
  {
    oldPath: '/account/v1/accounts/{id}/policies',
    newPath: '/account/v1/accounts/{id}/active-policies',
    changes: ['Path renamed', 'Only returns in-force policies']
  },
  {
    oldPath: '/job/v1/submissions/{id}/quote',
    newPath: '/job/v1/submissions/{id}/actions/quote',
    changes: ['Moved to actions sub-resource']
  }
];

function migrateApiCalls(code: string, fromVersion: string, toVersion: string): string {
  let migratedCode = code;

  endpointMigrations.forEach(migration => {
    const oldPattern = new RegExp(
      migration.oldPath.replace(/\{[^}]+\}/g, '[^/]+'),
      'g'
    );

    if (oldPattern.test(migratedCode)) {
      console.log(`Migrating: ${migration.oldPath} -> ${migration.newPath}`);
      console.log(`  Changes: ${migration.changes.join(', ')}`);

      migratedCode = migratedCode.replace(
        migration.oldPath,
        migration.newPath
      );
    }
  });

  return migratedCode;
}
```

### Step 7: Testing Migration

```gosu
// Migration test suite
package gw.migration.test

uses gw.testharness.v3.PLTestCase
uses gw.testharness.v3.PLAssert

class MigrationTestSuite extends PLTestCase {

  function testQueryAPICompatibility() {
    // Test new Query API syntax works
    var accounts = Query.make(Account)
      .compare(Account#AccountStatus, Equals, AccountStatus.TC_ACTIVE)
      .select()
      .toList()

    PLAssert.assertNotNull(accounts)
  }

  function testEntityExtensions() {
    // Verify custom entity extensions still work
    var policy = createTestPolicy()
    policy.CustomField_Ext = "Test Value"
    policy.Bundle.commit()

    var loaded = Query.make(Policy)
      .compare(Policy#ID, Equals, policy.ID)
      .select()
      .AtMostOneRow

    PLAssert.assertEquals("Test Value", loaded.CustomField_Ext)
  }

  function testIntegrationEndpoints() {
    // Verify integration endpoints respond correctly
    var client = new ExternalServiceClient()
    var response = client.healthCheck()
    PLAssert.assertTrue(response.isHealthy())
  }

  function testDataMigration() {
    // Verify migrated data integrity
    var count = Query.make(Account).select().Count
    PLAssert.assertTrue(count > 0, "Expected migrated accounts")
  }
}
```

## Cloud Migration Checklist

### Pre-Migration

| # | Task | Status |
|---|------|--------|
| 1 | Complete Guidewire Cloud readiness assessment | [ ] |
| 2 | Identify all integration points | [ ] |
| 3 | Document custom Gosu code | [ ] |
| 4 | Assess data volume and migration time | [ ] |
| 5 | Plan downtime window | [ ] |

### Migration Execution

| # | Task | Status |
|---|------|--------|
| 6 | Export configuration from on-premise | [ ] |
| 7 | Transform configuration for Cloud | [ ] |
| 8 | Deploy to Cloud sandbox | [ ] |
| 9 | Run smoke tests | [ ] |
| 10 | Migrate data | [ ] |
| 11 | Update integration endpoints | [ ] |
| 12 | Validate all functionality | [ ] |

### Post-Migration

| # | Task | Status |
|---|------|--------|
| 13 | Performance testing | [ ] |
| 14 | Security validation | [ ] |
| 15 | User acceptance testing | [ ] |
| 16 | Go-live approval | [ ] |

## Rollback Procedure

```bash
#!/bin/bash
# rollback-upgrade.sh

echo "=== Upgrade Rollback ==="

# Restore database backup
LATEST_BACKUP=$(ls -t backup-*.dump | head -1)
echo "Restoring from: $LATEST_BACKUP"

pg_restore -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "$LATEST_BACKUP"

# Restore code to previous version
git checkout previous-version
./gradlew clean build

# Restart services
./gradlew runServer

echo "Rollback complete - verify system functionality"
```
