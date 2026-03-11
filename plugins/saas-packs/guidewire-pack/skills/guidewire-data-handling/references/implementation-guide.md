# Guidewire Data Handling - Implementation Guide

## Instructions

### Step 1: Entity CRUD Operations

```gosu
// Gosu entity management patterns
package gw.data.entity

uses gw.api.database.Query
uses gw.api.util.Logger
uses gw.transaction.Transaction

class EntityManager {
  private static final var LOG = Logger.forCategory("EntityManager")

  // CREATE - Single entity
  static function createAccount(data : AccountData) : Account {
    return Transaction.runWithNewBundle(\bundle -> {
      var account = new Account(bundle)
      account.AccountNumber = generateAccountNumber()

      var contact = new Person(bundle)
      contact.FirstName = data.FirstName
      contact.LastName = data.LastName
      contact.DateOfBirth = data.DateOfBirth
      contact.EmailAddress1 = data.Email

      var address = new Address(bundle)
      address.AddressLine1 = data.AddressLine1
      address.City = data.City
      address.State = State.get(data.StateCode)
      address.PostalCode = data.PostalCode
      contact.PrimaryAddress = address

      account.AccountHolderContact = contact

      LOG.info("Created account: ${account.AccountNumber}")
      return account
    })
  }

  // READ - Single entity
  static function findAccountByNumber(accountNumber : String) : Account {
    return Query.make(Account)
      .compare(Account#AccountNumber, Equals, accountNumber)
      .select()
      .AtMostOneRow
  }

  // READ - Multiple entities with filtering
  static function findActiveAccountsByState(stateCode : String, limit : int = 100) : List<Account> {
    return Query.make(Account)
      .compare(Account#AccountStatus, Equals, AccountStatus.TC_ACTIVE)
      .join(Account#AccountHolderContact)
      .join(Contact#PrimaryAddress)
      .compare(Address#State, Equals, State.get(stateCode))
      .select()
      .orderBy(\a -> a.AccountNumber)
      .take(limit)
      .toList()
  }

  // UPDATE - Single entity
  static function updateAccount(accountNumber : String, data : AccountUpdateData) : Account {
    return Transaction.runWithNewBundle(\bundle -> {
      var account = findAccountByNumber(accountNumber)
      if (account == null) {
        throw new IllegalArgumentException("Account not found: ${accountNumber}")
      }

      account = bundle.add(account)

      if (data.Email != null) {
        account.AccountHolderContact.EmailAddress1 = data.Email
      }

      if (data.Phone != null) {
        account.AccountHolderContact.HomePhone = data.Phone
      }

      LOG.info("Updated account: ${accountNumber}")
      return account
    })
  }

  // DELETE - Single entity (soft delete)
  static function deactivateAccount(accountNumber : String) {
    Transaction.runWithNewBundle(\bundle -> {
      var account = findAccountByNumber(accountNumber)
      if (account == null) {
        throw new IllegalArgumentException("Account not found: ${accountNumber}")
      }

      account = bundle.add(account)
      account.AccountStatus = AccountStatus.TC_INACTIVE

      LOG.info("Deactivated account: ${accountNumber}")
    })
  }

  private static function generateAccountNumber() : String {
    return "ACC-${System.currentTimeMillis()}"
  }
}
```

### Step 2: Batch Data Operations

```gosu
// Batch processing patterns
package gw.data.batch

uses gw.api.database.Query
uses gw.api.util.Logger
uses gw.transaction.Transaction
uses java.util.concurrent.atomic.AtomicInteger

class BatchProcessor {
  private static final var LOG = Logger.forCategory("BatchProcessor")
  private static final var DEFAULT_BATCH_SIZE = 100

  // Process large datasets in batches
  static function processPolicies(processor(policy : Policy)) : BatchResult {
    var result = new BatchResult()
    var batchCount = new AtomicInteger(0)

    var query = Query.make(Policy)
      .compare(Policy#Status, Equals, PolicyStatus.TC_INFORCE)

    var iterator = query.select().iterator()
    var batch = new ArrayList<Policy>()

    while (iterator.hasNext()) {
      batch.add(iterator.next())

      if (batch.size() >= DEFAULT_BATCH_SIZE) {
        processBatch(batch, processor, result)
        batch.clear()
        batchCount.incrementAndGet()
        LOG.info("Processed batch ${batchCount.get()}")
      }
    }

    // Process remaining
    if (!batch.Empty) {
      processBatch(batch, processor, result)
    }

    LOG.info("Batch processing complete: ${result.Processed} processed, ${result.Failed} failed")
    return result
  }

  private static function processBatch(
    batch : List<Policy>,
    processor(policy : Policy),
    result : BatchResult
  ) {
    Transaction.runWithNewBundle(\bundle -> {
      batch.each(\policy -> {
        try {
          var p = bundle.add(policy)
          processor(p)
          result.incrementProcessed()
        } catch (e : Exception) {
          LOG.error("Failed to process policy ${policy.PolicyNumber}", e)
          result.addError(policy.PolicyNumber, e.Message)
          result.incrementFailed()
        }
      })
    })
  }

  // Parallel batch processing
  static function processParallel<T>(
    items : List<T>,
    processor(item : T),
    threadCount : int = 4
  ) : BatchResult {
    var result = new BatchResult()
    var executor = java.util.concurrent.Executors.newFixedThreadPool(threadCount)

    try {
      var futures = items.partition(DEFAULT_BATCH_SIZE).map(\batch -> {
        executor.submit(\-> {
          Transaction.runWithNewBundle(\bundle -> {
            batch.each(\item -> {
              try {
                processor(item)
                result.incrementProcessed()
              } catch (e : Exception) {
                LOG.error("Processing failed", e)
                result.incrementFailed()
              }
            })
          })
        })
      })

      // Wait for completion
      futures.each(\f -> f.get())
    } finally {
      executor.shutdown()
    }

    return result
  }
}

class BatchResult {
  private var _processed : AtomicInteger = new AtomicInteger(0)
  private var _failed : AtomicInteger = new AtomicInteger(0)
  private var _errors = new java.util.concurrent.ConcurrentHashMap<String, String>()

  property get Processed() : int { return _processed.get() }
  property get Failed() : int { return _failed.get() }
  property get Errors() : Map<String, String> { return _errors }

  function incrementProcessed() { _processed.incrementAndGet() }
  function incrementFailed() { _failed.incrementAndGet() }
  function addError(key : String, message : String) { _errors.put(key, message) }
}
```

### Step 3: Data Migration

```typescript
// API-based data migration
interface MigrationConfig {
  sourceSystem: string;
  targetEnvironment: string;
  batchSize: number;
  dryRun: boolean;
}

interface MigrationResult {
  totalRecords: number;
  successCount: number;
  errorCount: number;
  errors: Array<{ id: string; error: string }>;
  duration: number;
}

class DataMigration {
  private config: MigrationConfig;
  private guidewireClient: GuidewireClient;

  constructor(config: MigrationConfig) {
    this.config = config;
    this.guidewireClient = new GuidewireClient(config.targetEnvironment);
  }

  async migrateAccounts(sourceAccounts: SourceAccount[]): Promise<MigrationResult> {
    const startTime = Date.now();
    const result: MigrationResult = {
      totalRecords: sourceAccounts.length,
      successCount: 0,
      errorCount: 0,
      errors: [],
      duration: 0
    };

    console.log(`Starting migration of ${sourceAccounts.length} accounts`);

    // Process in batches
    for (let i = 0; i < sourceAccounts.length; i += this.config.batchSize) {
      const batch = sourceAccounts.slice(i, i + this.config.batchSize);
      console.log(`Processing batch ${Math.floor(i / this.config.batchSize) + 1}`);

      await Promise.all(batch.map(async (sourceAccount) => {
        try {
          const gwAccount = this.transformAccount(sourceAccount);

          if (!this.config.dryRun) {
            await this.guidewireClient.createAccount(gwAccount);
          }

          result.successCount++;
        } catch (error) {
          result.errorCount++;
          result.errors.push({
            id: sourceAccount.id,
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      }));

      // Rate limiting pause between batches
      await sleep(1000);
    }

    result.duration = Date.now() - startTime;
    console.log(`Migration complete: ${result.successCount} succeeded, ${result.errorCount} failed`);

    return result;
  }

  private transformAccount(source: SourceAccount): GuidewireAccount {
    return {
      accountHolder: {
        contactSubtype: source.isCompany ? 'Company' : 'Person',
        firstName: source.firstName,
        lastName: source.lastName,
        companyName: source.companyName,
        primaryAddress: {
          addressLine1: source.address.line1,
          addressLine2: source.address.line2,
          city: source.address.city,
          state: { code: this.mapStateCode(source.address.state) },
          postalCode: source.address.zip,
          country: { code: 'US' }
        },
        emailAddress1: source.email,
        homePhone: source.phone
      },
      producerCodes: [{ id: this.mapProducerCode(source.agentCode) }]
    };
  }

  private mapStateCode(sourceState: string): string {
    // Map source system state codes to Guidewire codes
    const stateMap: Record<string, string> = {
      'California': 'CA',
      'CA': 'CA',
      // Add more mappings
    };
    return stateMap[sourceState] || sourceState;
  }
}
```

### Step 4: Data Validation

```gosu
// Data validation framework
package gw.data.validation

uses gw.api.util.Logger

class DataValidator {
  private static final var LOG = Logger.forCategory("DataValidator")

  // Validate account data
  static function validateAccount(account : Account) : ValidationResult {
    var result = new ValidationResult()

    // Required fields
    if (account.AccountHolderContact == null) {
      result.addError("AccountHolderContact", "Account holder contact is required")
    }

    if (account.AccountNumber == null || account.AccountNumber.Empty) {
      result.addError("AccountNumber", "Account number is required")
    }

    // Contact validation
    if (account.AccountHolderContact != null) {
      var contact = account.AccountHolderContact
      if (contact typeis Person) {
        if (contact.FirstName == null || contact.FirstName.Empty) {
          result.addError("FirstName", "First name is required for person")
        }
        if (contact.LastName == null || contact.LastName.Empty) {
          result.addError("LastName", "Last name is required for person")
        }
      } else if (contact typeis Company) {
        if (contact.Name == null || contact.Name.Empty) {
          result.addError("CompanyName", "Company name is required")
        }
      }

      // Address validation
      if (contact.PrimaryAddress != null) {
        validateAddress(contact.PrimaryAddress, result)
      } else {
        result.addError("PrimaryAddress", "Primary address is required")
      }
    }

    return result
  }

  private static function validateAddress(address : Address, result : ValidationResult) {
    if (address.AddressLine1 == null || address.AddressLine1.Empty) {
      result.addError("AddressLine1", "Address line 1 is required")
    }
    if (address.City == null || address.City.Empty) {
      result.addError("City", "City is required")
    }
    if (address.State == null) {
      result.addError("State", "State is required")
    }
    if (address.PostalCode == null || address.PostalCode.Empty) {
      result.addError("PostalCode", "Postal code is required")
    }

    // Postal code format validation
    if (address.PostalCode != null && !address.PostalCode.matches("^\\d{5}(-\\d{4})?$")) {
      result.addError("PostalCode", "Invalid postal code format")
    }
  }

  // Validate policy data
  static function validatePolicy(policy : Policy) : ValidationResult {
    var result = new ValidationResult()

    if (policy.Account == null) {
      result.addError("Account", "Policy must be associated with an account")
    }

    if (policy.EffectiveDate == null) {
      result.addError("EffectiveDate", "Effective date is required")
    }

    if (policy.ExpirationDate == null) {
      result.addError("ExpirationDate", "Expiration date is required")
    }

    if (policy.EffectiveDate != null && policy.ExpirationDate != null) {
      if (policy.ExpirationDate.before(policy.EffectiveDate)) {
        result.addError("ExpirationDate", "Expiration date must be after effective date")
      }
    }

    return result
  }
}

class ValidationResult {
  private var _errors = new ArrayList<ValidationError>()

  property get HasErrors() : boolean { return !_errors.Empty }
  property get Errors() : List<ValidationError> { return _errors }

  function addError(field : String, message : String) {
    _errors.add(new ValidationError(field, message))
  }

  function throwIfInvalid() {
    if (HasErrors) {
      throw new ValidationException(
        "Validation failed: " + _errors.map(\e -> e.toString()).join(", ")
      )
    }
  }
}
```

### Step 5: Data Export

```gosu
// Data export utilities
package gw.data.export

uses gw.api.database.Query
uses java.io.FileWriter
uses java.io.BufferedWriter

class DataExporter {

  // Export to CSV
  static function exportAccountsToCSV(filename : String, filter : AccountFilter = null) {
    var writer = new BufferedWriter(new FileWriter(filename))

    try {
      // Write header
      writer.write("AccountNumber,FirstName,LastName,Email,Phone,Address,City,State,Zip\\n")

      // Query accounts
      var query = Query.make(Account)
      if (filter != null) {
        if (filter.Status != null) {
          query.compare(Account#AccountStatus, Equals, filter.Status)
        }
        if (filter.CreatedAfter != null) {
          query.compare(Account#CreateTime, GreaterThan, filter.CreatedAfter)
        }
      }

      // Stream results to file
      query.select().each(\account -> {
        var contact = account.AccountHolderContact
        var address = contact.PrimaryAddress

        writer.write(escapeCSV(account.AccountNumber) + ",")
        writer.write(escapeCSV(contact typeis Person ? contact.FirstName : "") + ",")
        writer.write(escapeCSV(contact typeis Person ? contact.LastName : contact.Name) + ",")
        writer.write(escapeCSV(contact.EmailAddress1 ?: "") + ",")
        writer.write(escapeCSV(contact.HomePhone ?: "") + ",")
        writer.write(escapeCSV(address?.AddressLine1 ?: "") + ",")
        writer.write(escapeCSV(address?.City ?: "") + ",")
        writer.write(escapeCSV(address?.State?.Code ?: "") + ",")
        writer.write(escapeCSV(address?.PostalCode ?: "") + "\\n")
      })
    } finally {
      writer.close()
    }
  }

  // Export to JSON
  static function exportAccountsToJSON(filename : String, limit : int = 1000) : int {
    var accounts = Query.make(Account)
      .compare(Account#AccountStatus, Equals, AccountStatus.TC_ACTIVE)
      .select()
      .take(limit)
      .toList()

    var json = accounts.map(\a -> accountToMap(a))
    var jsonString = gw.api.json.JsonObject.toJson(json)

    var writer = new FileWriter(filename)
    writer.write(jsonString)
    writer.close()

    return accounts.Count
  }

  private static function accountToMap(account : Account) : Map<String, Object> {
    var contact = account.AccountHolderContact
    return {
      "accountNumber" -> account.AccountNumber,
      "status" -> account.AccountStatus.Code,
      "contact" -> {
        "name" -> contact.DisplayName,
        "email" -> contact.EmailAddress1,
        "phone" -> contact.HomePhone
      },
      "createdDate" -> account.CreateTime.toString()
    }
  }

  private static function escapeCSV(value : String) : String {
    if (value.contains(",") || value.contains("\"") || value.contains("\\n")) {
      return "\"" + value.replace("\"", "\"\"") + "\""
    }
    return value
  }
}
```

### Step 6: Data Governance

```typescript
// Data governance and PII handling
interface PIIField {
  fieldPath: string;
  classification: 'PII' | 'PHI' | 'PCI' | 'SENSITIVE';
  maskingRule: 'full' | 'partial' | 'hash';
}

const piiFields: PIIField[] = [
  { fieldPath: 'contact.ssn', classification: 'PII', maskingRule: 'partial' },
  { fieldPath: 'contact.dateOfBirth', classification: 'PII', maskingRule: 'partial' },
  { fieldPath: 'contact.emailAddress1', classification: 'PII', maskingRule: 'partial' },
  { fieldPath: 'bankAccount.accountNumber', classification: 'PCI', maskingRule: 'partial' },
  { fieldPath: 'bankAccount.routingNumber', classification: 'PCI', maskingRule: 'full' }
];

class PIIMasker {
  mask(data: any, fields: PIIField[]): any {
    const masked = JSON.parse(JSON.stringify(data));

    fields.forEach(field => {
      const value = this.getNestedValue(masked, field.fieldPath);
      if (value) {
        const maskedValue = this.applyMaskingRule(value, field.maskingRule);
        this.setNestedValue(masked, field.fieldPath, maskedValue);
      }
    });

    return masked;
  }

  private applyMaskingRule(value: string, rule: string): string {
    switch (rule) {
      case 'full':
        return '*'.repeat(value.length);
      case 'partial':
        if (value.length <= 4) return '****';
        return '*'.repeat(value.length - 4) + value.slice(-4);
      case 'hash':
        return this.hashValue(value);
      default:
        return '****';
    }
  }

  private hashValue(value: string): string {
    // SHA-256 hash for one-way masking
    const crypto = require('crypto');
    return crypto.createHash('sha256').update(value).digest('hex').substring(0, 16);
  }
}

// Data retention policy
class DataRetentionPolicy {
  private retentionRules: Map<string, number> = new Map([
    ['claim', 7 * 365],        // 7 years
    ['policy', 10 * 365],      // 10 years
    ['auditLog', 90],          // 90 days
    ['sessionData', 1],        // 1 day
  ]);

  async enforceRetention(): Promise<RetentionResult> {
    const result: RetentionResult = { deleted: {}, errors: [] };

    for (const [entityType, retentionDays] of this.retentionRules) {
      try {
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

        const deletedCount = await this.deleteOldRecords(entityType, cutoffDate);
        result.deleted[entityType] = deletedCount;
      } catch (error) {
        result.errors.push({ entityType, error: error.message });
      }
    }

    return result;
  }
}
```

## Data Handling Best Practices

| Practice | Description |
|----------|-------------|
| Use Bundles | Always use Transaction.runWithNewBundle for writes |
| Batch Processing | Process large datasets in batches of 100-500 |
| Lazy Loading | Use select() and iterate, don't toList() large results |
| Index Awareness | Query on indexed fields for performance |
| Validation First | Validate data before database operations |
| Audit Trail | Log all data modifications |
| PII Protection | Mask or encrypt sensitive data |
