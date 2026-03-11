# Guidewire Hello World - Implementation Guide

## Instructions

### Step 1: Test System Connectivity

```bash
# Get access token first
TOKEN=$(curl -s -X POST "${GW_HUB_URL}/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=${GW_CLIENT_ID}&client_secret=${GW_CLIENT_SECRET}" \
  | jq -r '.access_token')

# Test PolicyCenter system info
curl -s "${POLICYCENTER_URL}/common/v1/system-info" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | jq
```

### Step 2: Query Accounts (PolicyCenter)

```typescript
// List accounts with pagination
interface Account {
  id: string;
  accountNumber: string;
  accountHolder: {
    displayName: string;
  };
  accountStatus: {
    code: string;
  };
}

interface AccountsResponse {
  data: Account[];
  links: {
    next?: string;
    prev?: string;
  };
  count: number;
}

async function listAccounts(limit: number = 25): Promise<AccountsResponse> {
  const response = await client.request<AccountsResponse>(
    'GET',
    `/account/v1/accounts?pageSize=${limit}`
  );

  console.log(`Found ${response.count} accounts`);
  response.data.forEach(account => {
    console.log(`- ${account.accountNumber}: ${account.accountHolder.displayName}`);
  });

  return response;
}
```

### Step 3: Create a Submission (PolicyCenter)

```typescript
// Create a new policy submission
interface CreateSubmissionRequest {
  data: {
    attributes: {
      account: { id: string };
      baseState: { code: string };
      product: { code: string };
      producerCode: { id: string };
      effectiveDate: string;
    };
  };
}

interface Submission {
  id: string;
  jobNumber: string;
  status: { code: string };
}

async function createSubmission(
  accountId: string,
  productCode: string = 'PersonalAuto'
): Promise<Submission> {
  const request: CreateSubmissionRequest = {
    data: {
      attributes: {
        account: { id: accountId },
        baseState: { code: 'CA' },
        product: { code: productCode },
        producerCode: { id: 'pcid:DefaultProducerCode' },
        effectiveDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
          .toISOString().split('T')[0]
      }
    }
  };

  const response = await client.request<{ data: Submission }>(
    'POST',
    '/job/v1/submissions',
    request
  );

  console.log(`Created submission: ${response.data.jobNumber}`);
  return response.data;
}
```

### Step 4: File a Claim (ClaimCenter)

```typescript
// First Notice of Loss (FNOL)
interface FNOLRequest {
  data: {
    attributes: {
      lossDate: string;
      lossType: { code: string };
      lossCause: { code: string };
      description: string;
      reportedDate: string;
      policyNumber: string;
    };
  };
}

interface Claim {
  id: string;
  claimNumber: string;
  status: { code: string };
}

async function createFNOL(policyNumber: string): Promise<Claim> {
  const fnol: FNOLRequest = {
    data: {
      attributes: {
        lossDate: new Date().toISOString().split('T')[0],
        lossType: { code: 'AUTO' },
        lossCause: { code: 'vehcollision' },
        description: 'Vehicle collision at intersection',
        reportedDate: new Date().toISOString().split('T')[0],
        policyNumber: policyNumber
      }
    }
  };

  const response = await client.request<{ data: Claim }>(
    'POST',
    `${process.env.CLAIMCENTER_URL}/claim/v1/claims`,
    fnol
  );

  console.log(`Created claim: ${response.data.claimNumber}`);
  return response.data;
}
```

### Step 5: Query Invoices (BillingCenter)

```typescript
// List account invoices
interface Invoice {
  id: string;
  invoiceNumber: string;
  invoiceDate: string;
  dueDate: string;
  status: { code: string };
  amount: { amount: number; currency: string };
}

interface InvoicesResponse {
  data: Invoice[];
  count: number;
}

async function getAccountInvoices(accountId: string): Promise<InvoicesResponse> {
  const response = await client.request<InvoicesResponse>(
    'GET',
    `${process.env.BILLINGCENTER_URL}/billing/v1/accounts/${accountId}/invoices`
  );

  console.log(`Found ${response.count} invoices`);
  response.data.forEach(invoice => {
    console.log(`- ${invoice.invoiceNumber}: $${invoice.amount.amount} due ${invoice.dueDate}`);
  });

  return response;
}
```

## Gosu Hello World (Server-Side)

```gosu
// Gosu script to query PolicyCenter data
uses gw.api.database.Query
uses entity.Policy
uses entity.Account

class HelloGuidewire {

  static function listActiveAccounts() : List<Account> {
    var query = Query.make(Account)
      .compare(Account#AccountStatus, Equals, AccountStatus.TC_ACTIVE)
      .select()
      .toList()

    query.each(\account -> {
      print("Account: ${account.AccountNumber} - ${account.AccountHolderContact.DisplayName}")
    })

    return query
  }

  static function findPoliciesByAccount(accountNumber : String) : List<Policy> {
    var account = Query.make(Account)
      .compare(Account#AccountNumber, Equals, accountNumber)
      .select()
      .AtMostOneRow

    if (account == null) {
      throw new IllegalArgumentException("Account not found: ${accountNumber}")
    }

    return account.Policies.toList()
  }
}
```

## API Response Structure

All Guidewire Cloud APIs follow this structure:

```typescript
interface GuidewireResponse<T> {
  data: T;                    // The requested resource(s)
  included?: any[];           // Related resources (if requested)
  links?: {
    self: string;
    next?: string;
    prev?: string;
  };
  count?: number;             // Total count for collections
}
```

## Common Resource Patterns

```typescript
// Get single resource
GET /account/v1/accounts/{accountId}

// List resources with filters
GET /account/v1/accounts?filter=accountStatus:eq:Active&pageSize=50

// Create resource
POST /account/v1/accounts
{ "data": { "attributes": { ... } } }

// Update resource (PATCH)
PATCH /account/v1/accounts/{accountId}
{ "data": { "attributes": { ... }, "checksum": "abc123" } }

// Include related resources
GET /account/v1/accounts/{accountId}?include=accountHolder,primaryLocation
```

## Examples

### Complete Hello World Script

```typescript
import { GuidewireClient } from './client';

async function main() {
  const client = new GuidewireClient(
    process.env.GW_CLIENT_ID!,
    process.env.GW_CLIENT_SECRET!,
    process.env.GW_HUB_URL!,
    process.env.POLICYCENTER_URL!
  );

  try {
    // 1. Test connectivity
    console.log('Testing PolicyCenter connectivity...');
    const systemInfo = await client.request('GET', '/common/v1/system-info');
    console.log('Connected:', systemInfo);

    // 2. List accounts
    console.log('\nListing accounts...');
    const accounts = await client.request('GET', '/account/v1/accounts?pageSize=5');
    console.log(`Found ${accounts.count} accounts`);

    // 3. Get account details
    if (accounts.data.length > 0) {
      const accountId = accounts.data[0].id;
      console.log(`\nGetting details for account: ${accountId}`);
      const account = await client.request('GET', `/account/v1/accounts/${accountId}`);
      console.log('Account details:', JSON.stringify(account, null, 2));
    }

    console.log('\nHello World complete!');
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

main();
```
