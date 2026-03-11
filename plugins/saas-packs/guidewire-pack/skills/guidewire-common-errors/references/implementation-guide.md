# Guidewire Common Errors — Implementation Guide

## 401 Authentication Error Handling

```typescript
class TokenManager {
  private token: string | null = null;
  private expiry: Date | null = null;

  async getValidToken(): Promise<string> {
    if (this.isTokenValid()) {
      return this.token!;
    }

    try {
      const response = await this.refreshToken();
      this.token = response.access_token;
      this.expiry = new Date(Date.now() + (response.expires_in - 60) * 1000);
      return this.token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      throw new AuthenticationError('Unable to obtain valid token');
    }
  }

  private isTokenValid(): boolean {
    return this.token !== null &&
           this.expiry !== null &&
           this.expiry > new Date();
  }
}
```

## 403 Permission Error Resolution

```json
// Error response
{
  "status": 403,
  "error": "Forbidden",
  "message": "Caller does not have permission to access endpoint: POST /account/v1/accounts",
  "details": {
    "requiredRole": "pc_account_admin",
    "callerRoles": ["pc_policy_read"]
  }
}
```

**Resolution:**
1. Log into Guidewire Cloud Console
2. Navigate to Identity & Access > API Roles
3. Find your service account
4. Add the required API role (`pc_account_admin`)
5. Wait 5 minutes for role propagation

## 409 Conflict (Optimistic Locking) Retry

```typescript
async function updateWithRetry<T>(
  path: string,
  getData: () => Promise<T>,
  updateFn: (data: T) => Partial<T>,
  maxRetries: number = 3
): Promise<T> {
  let attempt = 0;

  while (attempt < maxRetries) {
    try {
      const current = await client.request<{ data: T; checksum: string }>('GET', path);
      const updated = {
        data: {
          attributes: updateFn(current.data),
          checksum: current.checksum
        }
      };

      return await client.request<T>('PATCH', path, updated);
    } catch (error) {
      if (error.response?.status === 409 && attempt < maxRetries - 1) {
        attempt++;
        console.log(`Conflict detected, retrying (${attempt}/${maxRetries})`);
        await sleep(1000 * attempt);
        continue;
      }
      throw error;
    }
  }

  throw new Error('Max retries exceeded for optimistic locking conflict');
}
```

## 422 Validation Error Parser

```typescript
interface ValidationErrorResponse {
  status: 422;
  error: 'Unprocessable Entity';
  details: Array<{
    field: string;
    message: string;
    code: string;
    rejectedValue?: any;
  }>;
}

function handleValidationError(error: ValidationErrorResponse): never {
  console.error('Validation Errors:');

  error.details.forEach(detail => {
    console.error(`  [${detail.code}] ${detail.field}: ${detail.message}`);
    if (detail.rejectedValue !== undefined) {
      console.error(`    Rejected value: ${JSON.stringify(detail.rejectedValue)}`);
    }
  });

  const fieldErrors = error.details.reduce((acc, detail) => {
    acc[detail.field] = acc[detail.field] || [];
    acc[detail.field].push(detail.message);
    return acc;
  }, {} as Record<string, string[]>);

  throw new ValidationError('Request validation failed', fieldErrors);
}
```

## Gosu Exception Patterns

### NullPointerException

```gosu
// Bad: Direct property access
var account = getAccount()
print(account.AccountNumber)  // NPE if account is null

// Good: Null-safe access
var account = getAccount()
if (account != null) {
  print(account.AccountNumber)
}

// Better: Elvis operator
var accountNumber = account?.AccountNumber ?: "Unknown"
```

### QueryException

```gosu
// Bad: Returns multiple rows unexpectedly
var account = Query.make(Account)
  .compare(Account#AccountStatus, Equals, AccountStatus.TC_ACTIVE)
  .select()
  .AtMostOneRow  // Throws if multiple results!

// Good: Handle multiple results explicitly
var accounts = Query.make(Account)
  .compare(Account#AccountStatus, Equals, AccountStatus.TC_ACTIVE)
  .select()
  .toList()

if (accounts.Count > 1) {
  LOG.warn("Multiple active accounts found, using first")
}
var account = accounts.first()
```

### TransactionException

```gosu
// Error: Entity from different bundle
function badUpdate(policy : Policy) {
  Transaction.runWithNewBundle(\bundle -> {
    policy.Status = PolicyStatus.TC_INFORCE  // TransactionException!
  })
}

// Good: Add entity to bundle first
function goodUpdate(policy : Policy) {
  Transaction.runWithNewBundle(\bundle -> {
    var p = bundle.add(policy)  // Add to new bundle
    p.Status = PolicyStatus.TC_INFORCE
  })
}
```

### ValidationException

```gosu
try {
  Transaction.runWithNewBundle(\bundle -> {
    var submission = createSubmission(bundle)
    bundle.commit()
  })
} catch (e : gw.api.database.ValidationException) {
  LOG.error("Validation failed: ${e.Message}")
  e.ValidationResult.Errors.each(\err -> {
    LOG.error("  ${err.FieldPath}: ${err.Message}")
  })
  throw e
}
```

## Integration Error Handling

### REST API Client Errors

```gosu
uses gw.api.rest.FaultToleranceException
uses gw.api.rest.CircuitBreakerOpenException

class IntegrationService {
  function callExternalService(request : Request) : Response {
    try {
      return _client.post("/api/resource", request)
    } catch (e : CircuitBreakerOpenException) {
      LOG.warn("Circuit breaker open, using fallback")
      return getFallbackResponse()
    } catch (e : FaultToleranceException) {
      if (e.Cause typeis java.net.SocketTimeoutException) {
        LOG.error("External service timeout")
        throw new IntegrationTimeoutException("Service timed out", e)
      }
      LOG.error("Integration error: ${e.Message}")
      throw new IntegrationException("External service error", e)
    }
  }
}
```

### Message Queue Errors

```gosu
uses gw.api.messaging.MessageTransport

class MessageHandler {
  function handleDeliveryFailure(message : Message, error : Exception) {
    var retryCount = message.RetryCount ?: 0

    if (retryCount < 3) {
      message.RetryCount = retryCount + 1
      message.ScheduledSendTime = Date.Now.addMinutes(Math.pow(2, retryCount) as int)
      message.Status = MessageStatus.TC_PENDING
      LOG.info("Scheduling retry ${retryCount + 1} for message ${message.ID}")
    } else {
      message.Status = MessageStatus.TC_ERROR
      LOG.error("Message ${message.ID} failed after ${retryCount} retries: ${error.Message}")
      notifySupport(message, error)
    }
  }
}
```

## Database Deadlock Detection

```gosu
uses java.sql.SQLException

function executeWithDeadlockRetry<T>(operation() : T, maxRetries : int = 3) : T {
  var attempt = 0

  while (true) {
    try {
      return operation()
    } catch (e : SQLException) {
      if (isDeadlock(e) && attempt < maxRetries) {
        attempt++
        LOG.warn("Deadlock detected, retry ${attempt}/${maxRetries}")
        Thread.sleep(100 * attempt)
        continue
      }
      throw e
    }
  }
}

private function isDeadlock(e : SQLException) : boolean {
  // Oracle: ORA-00060, SQL Server: 1205, PostgreSQL: 40P01
  return e.ErrorCode == 60 ||
         e.ErrorCode == 1205 ||
         e.SQLState == "40P01"
}
```

## Standardized Error Wrapper

```typescript
class GuidewireApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: any,
    public traceId?: string
  ) {
    super(message);
    this.name = 'GuidewireApiError';
  }

  static fromResponse(response: any): GuidewireApiError {
    return new GuidewireApiError(
      response.status,
      response.error || 'UNKNOWN',
      response.message || 'An error occurred',
      response.details,
      response.headers?.['x-gw-trace-id']
    );
  }

  toUserMessage(): string {
    switch (this.code) {
      case 'invalid_token': return 'Your session has expired. Please log in again.';
      case 'forbidden': return 'You do not have permission to perform this action.';
      case 'not_found': return 'The requested resource was not found.';
      case 'validation_error': return 'Please correct the errors in your submission.';
      default: return 'An unexpected error occurred. Please try again.';
    }
  }
}
```
