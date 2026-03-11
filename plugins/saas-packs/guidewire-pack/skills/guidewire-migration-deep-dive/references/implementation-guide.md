# Guidewire Migration Deep Dive - Implementation Guide

## Migration Types

| Migration Type | Description | Complexity | Timeline |
|----------------|-------------|------------|----------|
| Version Upgrade | Same platform, new version | Low-Medium | 3-6 months |
| Cloud Migration | Self-managed to Guidewire Cloud | Medium-High | 6-12 months |
| Platform Replacement | Legacy to Guidewire | High | 12-24 months |
| Consolidation | Multiple systems to one | High | 12-18 months |

## Migration Phases

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Migration Lifecycle                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Phase 1        Phase 2        Phase 3        Phase 4        Phase 5           │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐          │
│  │ ASSESS  │──▶│ PLAN    │──▶│ BUILD   │──▶│ MIGRATE │──▶│OPTIMIZE │          │
│  │         │   │         │   │         │   │         │   │         │          │
│  │ 4-6 wks │   │ 4-8 wks │   │12-20 wks│   │ 4-8 wks │   │ 8-12 wks│          │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘          │
│       │             │             │             │             │                 │
│       ▼             ▼             ▼             ▼             ▼                 │
│  • Discovery    • Roadmap     • Config      • Data        • Performance       │
│  • Inventory    • Resources   • Testing     • Cutover     • Tuning            │
│  • Risk         • Timeline    • Integration • Validation  • Documentation     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Assessment and Discovery

```typescript
// Migration assessment framework
interface AssessmentResult {
  customizations: CustomizationInventory;
  integrations: IntegrationInventory;
  dataVolume: DataVolumeAnalysis;
  risks: Risk[];
  recommendations: Recommendation[];
}

interface CustomizationInventory {
  gosuFiles: number;
  pcfFiles: number;
  entityExtensions: number;
  plugins: number;
  customRules: number;
  estimatedEffort: string;
}

class MigrationAssessment {
  async assess(sourceEnvironment: string): Promise<AssessmentResult> {
    console.log('Starting migration assessment...');

    const customizations = await this.inventoryCustomizations(sourceEnvironment);
    const integrations = await this.inventoryIntegrations(sourceEnvironment);
    const dataVolume = await this.analyzeDataVolume(sourceEnvironment);
    const risks = this.identifyRisks(customizations, integrations, dataVolume);
    const recommendations = this.generateRecommendations(risks);

    return {
      customizations,
      integrations,
      dataVolume,
      risks,
      recommendations
    };
  }

  private async inventoryCustomizations(env: string): Promise<CustomizationInventory> {
    // Analyze codebase for customizations
    const gosuFiles = await this.countFiles(env, '**/*.gs');
    const pcfFiles = await this.countFiles(env, '**/*.pcf');
    const entityExtensions = await this.countFiles(env, '**/*_ext.xml');
    const plugins = await this.countPluginImplementations(env);
    const customRules = await this.countBusinessRules(env);

    const estimatedEffort = this.calculateEffort(
      gosuFiles, pcfFiles, entityExtensions, plugins, customRules
    );

    return {
      gosuFiles,
      pcfFiles,
      entityExtensions,
      plugins,
      customRules,
      estimatedEffort
    };
  }

  private async inventoryIntegrations(env: string): Promise<IntegrationInventory> {
    return {
      inbound: await this.analyzeInboundIntegrations(env),
      outbound: await this.analyzeOutboundIntegrations(env),
      realtime: await this.countRealtimeIntegrations(env),
      batch: await this.countBatchIntegrations(env)
    };
  }

  private identifyRisks(
    customizations: CustomizationInventory,
    integrations: IntegrationInventory,
    dataVolume: DataVolumeAnalysis
  ): Risk[] {
    const risks: Risk[] = [];

    // High customization risk
    if (customizations.gosuFiles > 500) {
      risks.push({
        category: 'Customization',
        severity: 'High',
        description: 'Large number of Gosu customizations may require significant refactoring',
        mitigation: 'Prioritize and categorize customizations, identify OOTB alternatives'
      });
    }

    // Integration complexity risk
    if (integrations.realtime > 20) {
      risks.push({
        category: 'Integration',
        severity: 'Medium',
        description: 'High number of real-time integrations may complicate cutover',
        mitigation: 'Plan phased integration cutover with fallback mechanisms'
      });
    }

    // Data volume risk
    if (dataVolume.totalRecords > 10000000) {
      risks.push({
        category: 'Data',
        severity: 'High',
        description: 'Large data volume may extend migration window',
        mitigation: 'Plan incremental data migration, consider data archiving'
      });
    }

    return risks;
  }
}
```

### Step 2: Data Migration Planning

```typescript
// Data migration strategy
interface DataMigrationPlan {
  phases: MigrationPhase[];
  totalRecords: number;
  estimatedDuration: string;
  rollbackStrategy: RollbackStrategy;
}

interface MigrationPhase {
  name: string;
  entities: EntityMigration[];
  sequence: number;
  dependencies: string[];
  estimatedDuration: string;
}

interface EntityMigration {
  sourceEntity: string;
  targetEntity: string;
  recordCount: number;
  transformations: Transformation[];
  validations: Validation[];
}

class DataMigrationPlanner {
  createPlan(assessment: AssessmentResult): DataMigrationPlan {
    // Define migration phases based on dependencies
    const phases: MigrationPhase[] = [
      {
        name: 'Reference Data',
        sequence: 1,
        dependencies: [],
        estimatedDuration: '2 days',
        entities: [
          { sourceEntity: 'typelists', targetEntity: 'typelists', recordCount: 5000, transformations: [], validations: [] },
          { sourceEntity: 'products', targetEntity: 'products', recordCount: 50, transformations: [], validations: [] },
          { sourceEntity: 'rate_tables', targetEntity: 'rate_tables', recordCount: 10000, transformations: [], validations: [] }
        ]
      },
      {
        name: 'Party Data',
        sequence: 2,
        dependencies: ['Reference Data'],
        estimatedDuration: '3 days',
        entities: [
          { sourceEntity: 'contacts', targetEntity: 'contacts', recordCount: 500000, transformations: [this.contactTransform()], validations: [this.contactValidation()] },
          { sourceEntity: 'accounts', targetEntity: 'accounts', recordCount: 200000, transformations: [], validations: [] }
        ]
      },
      {
        name: 'Policy Data',
        sequence: 3,
        dependencies: ['Party Data'],
        estimatedDuration: '5 days',
        entities: [
          { sourceEntity: 'policies', targetEntity: 'policies', recordCount: 300000, transformations: [this.policyTransform()], validations: [this.policyValidation()] },
          { sourceEntity: 'endorsements', targetEntity: 'policy_transactions', recordCount: 150000, transformations: [], validations: [] }
        ]
      },
      {
        name: 'Claims Data',
        sequence: 4,
        dependencies: ['Policy Data'],
        estimatedDuration: '4 days',
        entities: [
          { sourceEntity: 'claims', targetEntity: 'claims', recordCount: 100000, transformations: [this.claimTransform()], validations: [this.claimValidation()] },
          { sourceEntity: 'payments', targetEntity: 'payments', recordCount: 80000, transformations: [], validations: [] }
        ]
      }
    ];

    return {
      phases,
      totalRecords: this.calculateTotalRecords(phases),
      estimatedDuration: '14 days',
      rollbackStrategy: this.createRollbackStrategy(phases)
    };
  }

  private contactTransform(): Transformation {
    return {
      name: 'Contact Format Standardization',
      rules: [
        { field: 'phone', transform: 'standardize_phone_format' },
        { field: 'ssn', transform: 'encrypt_pii' },
        { field: 'address', transform: 'standardize_address' }
      ]
    };
  }

  private contactValidation(): Validation {
    return {
      name: 'Contact Data Validation',
      rules: [
        { field: 'email', rule: 'valid_email_format' },
        { field: 'state', rule: 'valid_state_code' },
        { field: 'zip', rule: 'valid_postal_code' }
      ]
    };
  }
}
```

### Step 3: Data Migration Execution

```gosu
// Data migration executor
package gw.migration.data

uses gw.api.database.Query
uses gw.api.util.Logger
uses gw.transaction.Transaction
uses java.sql.Connection
uses java.sql.PreparedStatement

class DataMigrationExecutor {
  private static final var LOG = Logger.forCategory("DataMigration")
  private static final var BATCH_SIZE = 500

  // Migrate accounts from legacy system
  static function migrateAccounts(sourceConnection : Connection) : MigrationResult {
    var result = new MigrationResult("accounts")
    var selectStmt = sourceConnection.prepareStatement(
      "SELECT * FROM legacy_accounts WHERE migration_status = 'pending' ORDER BY created_date"
    )

    var rs = selectStmt.executeQuery()
    var batch = new ArrayList<LegacyAccount>()

    while (rs.next()) {
      batch.add(mapLegacyAccount(rs))

      if (batch.size() >= BATCH_SIZE) {
        processBatch(batch, result)
        batch.clear()
      }
    }

    // Process remaining
    if (!batch.Empty) {
      processBatch(batch, result)
    }

    rs.close()
    selectStmt.close()

    LOG.info("Account migration complete: ${result.Succeeded} succeeded, ${result.Failed} failed")
    return result
  }

  private static function processBatch(batch : List<LegacyAccount>, result : MigrationResult) {
    Transaction.runWithNewBundle(\bundle -> {
      batch.each(\legacy -> {
        try {
          // Check if already migrated
          var existing = Query.make(Account)
            .compare(Account#LegacyID_Ext, Equals, legacy.LegacyId)
            .select()
            .AtMostOneRow

          if (existing != null) {
            LOG.debug("Account already migrated: ${legacy.LegacyId}")
            result.incrementSkipped()
            return
          }

          // Create new account
          var account = createAccount(bundle, legacy)

          // Validate
          var validation = validateAccount(account)
          if (validation.HasErrors) {
            LOG.warn("Validation failed for ${legacy.LegacyId}: ${validation.Errors}")
            result.addError(legacy.LegacyId, validation.toString())
            result.incrementFailed()
            return
          }

          result.incrementSucceeded()
        } catch (e : Exception) {
          LOG.error("Migration failed for ${legacy.LegacyId}", e)
          result.addError(legacy.LegacyId, e.Message)
          result.incrementFailed()
        }
      })
    })
  }

  private static function createAccount(bundle : Bundle, legacy : LegacyAccount) : Account {
    var account = new Account(bundle)
    account.AccountNumber = generateAccountNumber(legacy)
    account.LegacyID_Ext = legacy.LegacyId

    // Create contact
    var contact : Contact
    if (legacy.IsCompany) {
      var company = new Company(bundle)
      company.Name = legacy.CompanyName
      company.FEINOfficialID = legacy.FEIN
      contact = company
    } else {
      var person = new Person(bundle)
      person.FirstName = legacy.FirstName
      person.LastName = legacy.LastName
      person.DateOfBirth = legacy.DateOfBirth
      contact = person
    }

    contact.EmailAddress1 = legacy.Email
    contact.HomePhone = legacy.Phone

    // Create address
    var address = new Address(bundle)
    address.AddressLine1 = legacy.Address1
    address.AddressLine2 = legacy.Address2
    address.City = legacy.City
    address.State = mapState(legacy.State)
    address.PostalCode = legacy.Zip
    address.Country = Country.TC_US
    contact.PrimaryAddress = address

    account.AccountHolderContact = contact

    return account
  }
}
```

### Step 4: Integration Cutover Planning

```typescript
// Integration cutover strategy
interface CutoverPlan {
  phases: CutoverPhase[];
  rollbackPoints: RollbackPoint[];
  communicationPlan: CommunicationPlan;
  goNoGoChecklist: ChecklistItem[];
}

interface CutoverPhase {
  name: string;
  startTime: Date;
  duration: string;
  tasks: CutoverTask[];
  verificationSteps: VerificationStep[];
}

class CutoverPlanner {
  createPlan(targetDate: Date): CutoverPlan {
    const phases: CutoverPhase[] = [
      {
        name: 'Pre-Cutover (T-24 hours)',
        startTime: new Date(targetDate.getTime() - 24 * 60 * 60 * 1000),
        duration: '24 hours',
        tasks: [
          { name: 'Final data sync', owner: 'Data Team', duration: '4 hours' },
          { name: 'Disable write operations on legacy', owner: 'Ops Team', duration: '15 min' },
          { name: 'Backup current state', owner: 'DBA', duration: '2 hours' },
          { name: 'Notify stakeholders', owner: 'PM', duration: '30 min' }
        ],
        verificationSteps: [
          { name: 'Verify data sync complete', criteria: 'Record counts match' },
          { name: 'Verify backups successful', criteria: 'Backup verification passed' }
        ]
      },
      {
        name: 'Cutover (T-0)',
        startTime: targetDate,
        duration: '4 hours',
        tasks: [
          { name: 'Switch DNS/Load balancer', owner: 'Infra Team', duration: '15 min' },
          { name: 'Update integration endpoints', owner: 'Integration Team', duration: '30 min' },
          { name: 'Enable Guidewire Cloud', owner: 'GW Admin', duration: '15 min' },
          { name: 'Run smoke tests', owner: 'QA Team', duration: '1 hour' },
          { name: 'Enable user access', owner: 'Security Team', duration: '15 min' }
        ],
        verificationSteps: [
          { name: 'API health checks pass', criteria: 'All endpoints return 200' },
          { name: 'Sample transactions succeed', criteria: '10 test transactions complete' },
          { name: 'Integration tests pass', criteria: 'All critical integrations verified' }
        ]
      },
      {
        name: 'Post-Cutover (T+0 to T+48)',
        startTime: new Date(targetDate.getTime() + 4 * 60 * 60 * 1000),
        duration: '48 hours',
        tasks: [
          { name: 'Monitor error rates', owner: 'Ops Team', duration: 'Continuous' },
          { name: 'Address issues', owner: 'Dev Team', duration: 'As needed' },
          { name: 'User support', owner: 'Support Team', duration: 'Continuous' },
          { name: 'Decommission legacy (after validation)', owner: 'Infra Team', duration: '4 hours' }
        ],
        verificationSteps: [
          { name: 'Error rate < 1%', criteria: 'Dashboard metric' },
          { name: 'No critical issues', criteria: 'JIRA filter' },
          { name: 'User feedback positive', criteria: 'Survey results' }
        ]
      }
    ];

    return {
      phases,
      rollbackPoints: this.createRollbackPoints(phases),
      communicationPlan: this.createCommunicationPlan(),
      goNoGoChecklist: this.createGoNoGoChecklist()
    };
  }

  private createRollbackPoints(phases: CutoverPhase[]): RollbackPoint[] {
    return [
      {
        name: 'Pre-DNS Switch',
        condition: 'Critical issue before DNS change',
        procedure: 'Abort cutover, legacy remains primary',
        estimatedTime: '15 minutes'
      },
      {
        name: 'Post-DNS, Pre-Validation',
        condition: 'Smoke tests failing',
        procedure: 'Revert DNS, disable Guidewire, re-enable legacy',
        estimatedTime: '30 minutes'
      },
      {
        name: 'Post-Go-Live',
        condition: 'Critical production issue within 24 hours',
        procedure: 'Full rollback to legacy with data sync',
        estimatedTime: '4 hours'
      }
    ];
  }

  private createGoNoGoChecklist(): ChecklistItem[] {
    return [
      { item: 'All critical bugs resolved', owner: 'Dev Lead', status: 'pending' },
      { item: 'UAT sign-off received', owner: 'Business Lead', status: 'pending' },
      { item: 'Data migration validated', owner: 'Data Lead', status: 'pending' },
      { item: 'Rollback tested', owner: 'Ops Lead', status: 'pending' },
      { item: 'Support team trained', owner: 'Support Lead', status: 'pending' },
      { item: 'Change approval received', owner: 'Change Manager', status: 'pending' },
      { item: 'Communication sent', owner: 'PM', status: 'pending' }
    ];
  }
}
```

### Step 5: Validation Framework

```gosu
// Post-migration validation
package gw.migration.validation

uses gw.api.database.Query
uses gw.api.util.Logger

class MigrationValidator {
  private static final var LOG = Logger.forCategory("MigrationValidator")

  static function validateMigration() : ValidationReport {
    var report = new ValidationReport()

    // Record count validation
    report.addSection("Record Counts", validateRecordCounts())

    // Data integrity validation
    report.addSection("Data Integrity", validateDataIntegrity())

    // Business rule validation
    report.addSection("Business Rules", validateBusinessRules())

    // Financial reconciliation
    report.addSection("Financial Reconciliation", validateFinancials())

    return report
  }

  private static function validateRecordCounts() : List<ValidationResult> {
    var results = new ArrayList<ValidationResult>()

    // Compare counts with source
    var sourceCounts = getSourceCounts()
    var targetCounts = getTargetCounts()

    sourceCounts.eachKeyAndValue(\entity, sourceCount -> {
      var targetCount = targetCounts.get(entity) ?: 0
      var variance = Math.abs(sourceCount - targetCount)
      var variancePercent = (variance * 100.0 / sourceCount)

      var result = new ValidationResult()
      result.Check = "Record count: ${entity}"
      result.Expected = sourceCount.toString()
      result.Actual = targetCount.toString()
      result.Passed = variancePercent < 0.1  // Allow 0.1% variance

      if (!result.Passed) {
        result.Message = "Variance of ${variancePercent}% exceeds threshold"
      }

      results.add(result)
    })

    return results
  }

  private static function validateDataIntegrity() : List<ValidationResult> {
    var results = new ArrayList<ValidationResult>()

    // Check for orphan records
    var orphanPolicies = Query.make(Policy)
      .compare(Policy#Account, Equals, null)
      .select()
      .Count

    results.add(new ValidationResult() {
      :Check = "Orphan policies",
      :Expected = "0",
      :Actual = orphanPolicies.toString(),
      :Passed = orphanPolicies == 0,
      :Message = orphanPolicies > 0 ? "Found ${orphanPolicies} policies without accounts" : null
    })

    // Check for duplicate records
    var duplicateAccounts = findDuplicateAccounts()
    results.add(new ValidationResult() {
      :Check = "Duplicate accounts",
      :Expected = "0",
      :Actual = duplicateAccounts.Count.toString(),
      :Passed = duplicateAccounts.Empty,
      :Message = !duplicateAccounts.Empty ? "Found ${duplicateAccounts.Count} duplicate accounts" : null
    })

    return results
  }

  private static function validateFinancials() : List<ValidationResult> {
    var results = new ArrayList<ValidationResult>()

    // Total written premium reconciliation
    var sourcePremium = getSourceTotalPremium()
    var targetPremium = Query.make(Policy)
      .select()
      .sum(\p -> p.TotalPremiumRPT.Amount)

    var variance = Math.abs(sourcePremium - targetPremium)
    var variancePercent = (variance * 100.0 / sourcePremium)

    results.add(new ValidationResult() {
      :Check = "Total written premium",
      :Expected = sourcePremium.toString(),
      :Actual = targetPremium.toString(),
      :Passed = variancePercent < 0.01,  // Allow 0.01% variance for rounding
      :Message = variancePercent >= 0.01 ? "Variance of ${variancePercent}%" : null
    })

    return results
  }
}
```

## Migration Checklist

| Phase | Task | Owner | Status |
|-------|------|-------|--------|
| Assessment | Complete inventory | PM | [ ] |
| Assessment | Risk analysis | Architect | [ ] |
| Planning | Data migration plan | Data Lead | [ ] |
| Planning | Integration cutover plan | Integration Lead | [ ] |
| Build | Configuration migration | Dev Team | [ ] |
| Build | Integration updates | Integration Team | [ ] |
| Test | UAT completion | QA Lead | [ ] |
| Test | Performance testing | Performance Team | [ ] |
| Migrate | Data migration execution | Data Team | [ ] |
| Migrate | Cutover execution | Ops Team | [ ] |
| Validate | Post-migration validation | QA Team | [ ] |
| Optimize | Performance tuning | Dev Team | [ ] |
