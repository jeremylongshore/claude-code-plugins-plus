# Guidewire SDK Patterns — Implementation Guide

## Digital SDK Setup

```bash
# Initialize Jutro project with Digital SDK
npx @guidewire/jutro-cli@latest create my-portal --template agent-portal
cd my-portal

# Generate Digital SDK from your Cloud API
npx jutro-cli generate-sdk \
  --api-url https://your-tenant.cloud.guidewire.com/pc \
  --output src/sdk
```

### SDK Configuration

```typescript
// src/sdk/config.ts
import { createSdkConfig } from '@guidewire/digital-sdk';

export const sdkConfig = createSdkConfig({
  baseUrl: process.env.REACT_APP_API_URL,
  auth: {
    type: 'oauth2',
    clientId: process.env.REACT_APP_CLIENT_ID,
    redirectUri: `${window.location.origin}/callback`,
    scope: 'pc.policies'
  },
  headers: { 'Accept-Language': 'en-US' },
  timeout: 30000
});
```

### Entity Operations

```typescript
import { useAccount, useAccounts, createAccount } from '../sdk/account';

// Read single entity
function AccountDetail({ accountId }: { accountId: string }) {
  const { data: account, loading, error } = useAccount(accountId, {
    include: ['accountHolder', 'primaryLocation']
  });

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorBanner error={error} />;

  return (
    <div>
      <h1>{account.accountHolder.displayName}</h1>
      <p>Account #: {account.accountNumber}</p>
      <p>Status: {account.accountStatus.name}</p>
    </div>
  );
}

// List entities with filtering
function AccountList() {
  const { data: accounts, loading, pagination } = useAccounts({
    filter: { accountStatus: 'Active' },
    pageSize: 25,
    sort: '-createdDate'
  });

  return (
    <DataTable
      data={accounts}
      loading={loading}
      pagination={pagination}
      columns={[
        { field: 'accountNumber', header: 'Account #' },
        { field: 'accountHolder.displayName', header: 'Name' },
        { field: 'accountStatus.name', header: 'Status' }
      ]}
    />
  );
}

// Create entity
async function handleCreateAccount(formData: AccountFormData) {
  try {
    const newAccount = await createAccount({
      accountHolder: {
        firstName: formData.firstName,
        lastName: formData.lastName,
        dateOfBirth: formData.dob
      },
      primaryLocation: {
        addressLine1: formData.address,
        city: formData.city,
        state: { code: formData.state },
        postalCode: formData.zip
      }
    });
    console.log('Created account:', newAccount.accountNumber);
    return newAccount;
  } catch (error) {
    handleApiError(error);
  }
}
```

### Schema Validation

```typescript
import { accountSchema, validateAccount } from '../sdk/account';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

function AccountForm() {
  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm({
    resolver: zodResolver(accountSchema)
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Input
        {...register('accountHolder.firstName')}
        label="First Name"
        error={errors.accountHolder?.firstName?.message}
        required
      />
      <Input
        {...register('accountHolder.lastName')}
        label="Last Name"
        error={errors.accountHolder?.lastName?.message}
        required
      />
    </form>
  );
}
```

## REST API Client Plugin

```groovy
// build.gradle
plugins {
    id 'com.guidewire.rest-api-client' version '3.0.0'
}

restApiClient {
    clients {
        externalRating {
            specFile = file('specs/rating-service.yaml')
            packageName = 'gw.integration.rating'
            generateSync = true
            faultTolerance {
                retryAttempts = 3
                retryDelay = 1000
                circuitBreakerThreshold = 5
            }
        }
    }
}
```

### Generated Client Usage (Gosu)

```gosu
package gw.integration.rating

uses gw.integration.rating.api.RatingApi
uses gw.integration.rating.model.RatingRequest
uses gw.integration.rating.model.RatingResponse

class RatingService {
  private static final var LOG = Logger.forCategory("RatingService")
  private static final var _api = new RatingApi()

  static function getRating(policy : Policy) : RatingResponse {
    var request = new RatingRequest()
    request.PolicyNumber = policy.PolicyNumber
    request.EffectiveDate = policy.EffectiveDate
    request.CoverageType = policy.Product.Code
    request.State = policy.PrimaryLocation.State.Code

    try {
      var response = _api.calculateRating(request)
      LOG.info("Rating calculated: ${response.PremiumAmount}")
      return response
    } catch (e : FaultToleranceException) {
      LOG.error("Rating service unavailable", e)
      throw new RatingServiceException("Unable to calculate rating", e)
    }
  }
}
```

### Custom REST Client

```gosu
package gw.integration.external

uses gw.api.rest.RestClient
uses gw.api.rest.RestClientBuilder

class ExternalServiceClient {
  private static final var LOG = Logger.forCategory("ExternalServiceClient")
  private var _client : RestClient

  construct() {
    _client = RestClientBuilder.create()
      .withBaseUrl(ScriptParameters.ExternalServiceUrl)
      .withTimeout(30000)
      .withHeader("Authorization", "Bearer ${getToken()}")
      .withHeader("Content-Type", "application/json")
      .build()
  }

  function getResource(resourceId : String) : ExternalResource {
    var response = _client.get("/resources/${resourceId}")
    validateResponse(response)
    return parseResponse(response, ExternalResource)
  }

  function createResource(resource : ExternalResource) : ExternalResource {
    var response = _client.post("/resources", toJson(resource))
    validateResponse(response)
    return parseResponse(response, ExternalResource)
  }

  private function validateResponse(response : Response) {
    if (response.StatusCode >= 400) {
      LOG.error("API error: ${response.StatusCode} - ${response.Body}")
      throw new ExternalServiceException("External service error: ${response.StatusCode}")
    }
  }
}
```

## Gosu Query Patterns

```gosu
package gw.custom.query

uses gw.api.database.Query

class PolicyQueryService {

  // Simple query
  static function findByPolicyNumber(policyNumber : String) : Policy {
    return Query.make(Policy)
      .compare(Policy#PolicyNumber, Equals, policyNumber)
      .select()
      .AtMostOneRow
  }

  // Query with joins
  static function findPoliciesByProducerCode(producerCode : String) : List<Policy> {
    return Query.make(Policy)
      .join(Policy#ProducerCodeOfRecord)
      .compare(ProducerCode#Code, Equals, producerCode)
      .select()
      .toList()
  }

  // Complex query with subqueries
  static function findActiveHighValuePolicies(minPremium : java.math.BigDecimal) : List<Policy> {
    var query = Query.make(Policy)
    query.compare(Policy#Status, Equals, PolicyStatus.TC_INFORCE)
    query.compare(Policy#TotalPremiumRPT, GreaterThanOrEquals, minPremium)
    query.compare(Policy#ExpirationDate, GreaterThan, Date.Today)

    var subquery = query.subselect(Policy#ID, CompareIn, PolicyPeriod#Policy)
    subquery.join(PolicyPeriod#PersonalAutoLine)
      .compare(PersonalAutoLine#PAVehicles, IsNotNull, null)

    return query.select()
      .orderBy(\p -> p.TotalPremiumRPT)
      .toList()
  }

  // Batch processing pattern
  static function processInBatches<T>(
    query : Query<T>,
    batchSize : int,
    processor(batch : List<T>)
  ) {
    var iterator = query.select().iterator()
    var batch = new ArrayList<T>()

    while (iterator.hasNext()) {
      batch.add(iterator.next())
      if (batch.size() >= batchSize) {
        processor(batch)
        batch.clear()
      }
    }

    if (!batch.Empty) {
      processor(batch)
    }
  }
}
```

## Transaction Patterns

```gosu
package gw.custom.transaction

uses gw.transaction.Transaction as GWTransaction

class TransactionService {

  static function createAccountWithPolicy(accountData : AccountData) : Policy {
    return GWTransaction.runWithNewBundle(\bundle -> {
      var account = new Account(bundle)
      account.AccountNumber = accountData.AccountNumber

      var contact = new Person(bundle)
      contact.FirstName = accountData.FirstName
      contact.LastName = accountData.LastName
      account.AccountHolderContact = contact

      var submission = new Submission(bundle)
      submission.Account = account
      submission.Product = accountData.Product

      return submission.Policy
    })
  }

  static function complexOperation(policy : Policy) {
    GWTransaction.runWithNewBundle(\bundle -> {
      policy = bundle.add(policy)
      try {
        updateCoverages(policy)
        applyEndorsement(policy)
      } catch (e : Exception) {
        throw e // Bundle will rollback automatically
      }
    })
  }

  static function queueAsyncWork(policyId : Key) {
    gw.api.async.AsyncProcess.schedule(
      "ProcessPolicy",
      \-> processPolicy(policyId),
      Date.Now
    )
  }
}
```

## Plugin Patterns

```gosu
package gw.plugin.rating

uses gw.plugin.rating.IRatingPlugin

class CustomRatingPlugin implements IRatingPlugin {
  private static final var LOG = Logger.forCategory("CustomRatingPlugin")

  override function calculatePremium(period : PolicyPeriod) : Money {
    LOG.info("Calculating premium for policy: ${period.PolicyNumber}")

    var basePremium = calculateBasePremium(period)
    var discounts = applyDiscounts(period, basePremium)
    var taxes = calculateTaxes(period, basePremium - discounts)

    return basePremium - discounts + taxes
  }

  private function calculateBasePremium(period : PolicyPeriod) : Money {
    return period.Lines.map(\line -> line.calculatePremium()).sum()
  }

  private function applyDiscounts(period : PolicyPeriod, base : Money) : Money {
    var totalDiscount = Money.ZERO
    if (period.Account.Policies.Count > 1) {
      totalDiscount += base * 0.10
    }
    if (hasGoodDriverDiscount(period)) {
      totalDiscount += base * 0.15
    }
    return totalDiscount
  }
}
```
