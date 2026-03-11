# Guidewire Enterprise RBAC - Implementation Guide

## RBAC Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Guidewire RBAC Architecture                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         Guidewire Hub (IdP)                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │   Users     │  │   Groups    │  │ Applications│  │   Roles     │    │   │
│  │  │             │  │             │  │             │  │             │    │   │
│  │  │ • Internal  │  │ • AD Sync   │  │ • Browser   │  │ • API Roles │    │   │
│  │  │ • External  │  │ • Manual    │  │ • Service   │  │ • App Roles │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│                    ┌───────────────────┼───────────────────┐                    │
│                    │                   │                   │                    │
│                    ▼                   ▼                   ▼                    │
│  ┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐ │
│  │     PolicyCenter      │ │     ClaimCenter       │ │    BillingCenter      │ │
│  │                       │ │                       │ │                       │ │
│  │ System Roles:         │ │ System Roles:         │ │ System Roles:         │ │
│  │ • Underwriter         │ │ • Claims Adjuster     │ │ • Billing Admin       │ │
│  │ • Policy Admin        │ │ • Claims Supervisor   │ │ • Payment Handler     │ │
│  │ • Agent               │ │ • SIU Investigator    │ │ • Collections Agent   │ │
│  │                       │ │                       │ │                       │ │
│  │ API Roles:            │ │ API Roles:            │ │ API Roles:            │ │
│  │ • pc_policy_read      │ │ • cc_claim_read       │ │ • bc_billing_read     │ │
│  │ • pc_policy_admin     │ │ • cc_claim_admin      │ │ • bc_payment_admin    │ │
│  └───────────────────────┘ └───────────────────────┘ └───────────────────────┘ │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Configure API Roles in GCC

```yaml
# API Role Configuration
# Guidewire Cloud Console > Identity & Access > API Roles

api_roles:
  # Read-only roles
  - name: pc_policy_read
    application: PolicyCenter
    description: Read-only access to policies and accounts
    permissions:
      - endpoint: /account/v1/accounts
        operations: [GET]
      - endpoint: /account/v1/accounts/{id}
        operations: [GET]
      - endpoint: /policy/v1/policies
        operations: [GET]
      - endpoint: /policy/v1/policies/{id}
        operations: [GET]

  # Admin roles
  - name: pc_policy_admin
    application: PolicyCenter
    description: Full access to policy administration
    permissions:
      - endpoint: /account/v1/accounts
        operations: [GET, POST, PATCH]
      - endpoint: /job/v1/submissions
        operations: [GET, POST, PATCH]
      - endpoint: /job/v1/submissions/{id}/quote
        operations: [POST]
      - endpoint: /job/v1/submissions/{id}/bind
        operations: [POST]
      - endpoint: /policy/v1/policies
        operations: [GET, POST, PATCH]

  # Claims roles
  - name: cc_claim_admin
    application: ClaimCenter
    description: Full access to claims management
    permissions:
      - endpoint: /claim/v1/claims
        operations: [GET, POST, PATCH]
      - endpoint: /fnol/v1/fnol
        operations: [POST]
      - endpoint: /claim/v1/claims/{id}/exposures
        operations: [GET, POST, PATCH]
      - endpoint: /claim/v1/claims/{id}/payments
        operations: [GET, POST]
```

### Step 2: Service Account Configuration

```typescript
// Service account management
interface ServiceAccount {
  clientId: string;
  name: string;
  description: string;
  apiRoles: string[];
  environments: string[];
}

const serviceAccounts: ServiceAccount[] = [
  {
    clientId: 'integration-service-prod',
    name: 'Integration Service',
    description: 'Backend integration service for policy and claims sync',
    apiRoles: ['pc_policy_admin', 'cc_claim_read'],
    environments: ['production']
  },
  {
    clientId: 'agent-portal-prod',
    name: 'Agent Portal',
    description: 'Agent-facing portal application',
    apiRoles: ['pc_policy_read', 'pc_submission_handler'],
    environments: ['production', 'uat']
  },
  {
    clientId: 'reporting-service',
    name: 'Reporting Service',
    description: 'Read-only access for reporting',
    apiRoles: ['pc_policy_read', 'cc_claim_read', 'bc_billing_read'],
    environments: ['production']
  }
];

// Register service account in GCC
async function registerServiceAccount(account: ServiceAccount): Promise<void> {
  const response = await gccClient.post('/api/v1/applications', {
    clientId: account.clientId,
    name: account.name,
    description: account.description,
    type: 'service',
    apiRoles: account.apiRoles.map(role => ({ name: role }))
  });

  console.log(`Registered service account: ${account.clientId}`);
}
```

### Step 3: User Role Management in Gosu

```gosu
// User role management
package gw.security.roles

uses gw.api.util.Logger
uses gw.pl.persistence.core.Bundle

class RoleManager {
  private static final var LOG = Logger.forCategory("RoleManager")

  // Assign role to user
  static function assignRole(user : User, roleCode : String) {
    var role = Role.get(roleCode)
    if (role == null) {
      throw new IllegalArgumentException("Role not found: ${roleCode}")
    }

    if (user.hasRole(role)) {
      LOG.info("User ${user.UserName} already has role ${roleCode}")
      return
    }

    gw.transaction.Transaction.runWithNewBundle(\bundle -> {
      var u = bundle.add(user)
      var userRole = new UserRole(bundle)
      userRole.User = u
      userRole.Role = role
      LOG.info("Assigned role ${roleCode} to user ${user.UserName}")
    })
  }

  // Remove role from user
  static function removeRole(user : User, roleCode : String) {
    var role = Role.get(roleCode)
    if (role == null) {
      throw new IllegalArgumentException("Role not found: ${roleCode}")
    }

    gw.transaction.Transaction.runWithNewBundle(\bundle -> {
      var u = bundle.add(user)
      var userRole = u.Roles.firstWhere(\ur -> ur.Role == role)
      if (userRole != null) {
        bundle.delete(userRole)
        LOG.info("Removed role ${roleCode} from user ${user.UserName}")
      }
    })
  }

  // Check if user has permission
  static function hasPermission(user : User, permission : String) : boolean {
    return user.Roles.hasMatch(\ur ->
      ur.Role.Permissions.hasMatch(\p -> p.Code == permission)
    )
  }

  // Get all permissions for user
  static function getUserPermissions(user : User) : Set<String> {
    var permissions = new HashSet<String>()
    user.Roles.each(\ur -> {
      ur.Role.Permissions.each(\p -> {
        permissions.add(p.Code)
      })
    })
    return permissions
  }
}
```

### Step 4: Custom Permission Checks

```gosu
// Custom permission framework
package gw.security.permissions

uses gw.api.util.Logger
uses gw.api.web.SessionUtil

class PermissionChecker {
  private static final var LOG = Logger.forCategory("PermissionChecker")

  // Check permission with audit logging
  static function checkPermission(permission : String) : boolean {
    var user = SessionUtil.CurrentUser
    if (user == null) {
      LOG.warn("Permission check failed: No user in session")
      return false
    }

    var hasPermission = RoleManager.hasPermission(user, permission)

    if (!hasPermission) {
      LOG.warn("Permission denied: ${permission} for user ${user.UserName}")
      auditPermissionDenial(user, permission)
    }

    return hasPermission
  }

  // Require permission (throws if denied)
  static function requirePermission(permission : String) {
    if (!checkPermission(permission)) {
      throw new SecurityException("Permission denied: ${permission}")
    }
  }

  // Check entity-level permission
  static function canAccessEntity(entity : KeyableBean, operation : String) : boolean {
    var user = SessionUtil.CurrentUser
    if (user == null) {
      return false
    }

    // Check ownership
    if (isOwner(user, entity)) {
      return true
    }

    // Check hierarchical access
    if (hasHierarchicalAccess(user, entity)) {
      return true
    }

    // Check role-based access
    var permission = "${entity.IntrinsicType.Name}_${operation}"
    return checkPermission(permission)
  }

  private static function isOwner(user : User, entity : KeyableBean) : boolean {
    // Check if user created or is assigned to entity
    if (entity typeis Policy) {
      return entity.CreateUser == user
    } else if (entity typeis Claim) {
      return entity.AssignedUser == user
    }
    return false
  }

  private static function hasHierarchicalAccess(user : User, entity : KeyableBean) : boolean {
    // Check organizational hierarchy
    if (entity typeis Policy) {
      var policyOrg = entity.ProducerCodeOfRecord?.Organization
      return user.Organization == policyOrg || isParentOrg(user.Organization, policyOrg)
    }
    return false
  }

  private static function auditPermissionDenial(user : User, permission : String) {
    // Log to audit trail
    gw.api.audit.AuditLogger.log(
      "PERMISSION_DENIED",
      "User ${user.UserName} denied permission: ${permission}",
      user.PublicID
    )
  }
}
```

### Step 5: Row-Level Security

```gosu
// Row-level security implementation
package gw.security.rls

uses gw.api.database.Query
uses gw.api.web.SessionUtil

class RowLevelSecurity {

  // Apply security filters to queries
  static function applySecurityFilter<T extends KeyableBean>(query : Query<T>) : Query<T> {
    var user = SessionUtil.CurrentUser
    if (user == null || user.hasRole(Role.get("SystemAdmin"))) {
      return query  // No filtering for system admins
    }

    var entityType = query.getTargetType()

    if (entityType == Policy) {
      return applyPolicySecurityFilter(query as Query<Policy>, user) as Query<T>
    } else if (entityType == Claim) {
      return applyClaimSecurityFilter(query as Query<Claim>, user) as Query<T>
    } else if (entityType == Account) {
      return applyAccountSecurityFilter(query as Query<Account>, user) as Query<T>
    }

    return query
  }

  private static function applyPolicySecurityFilter(
    query : Query<Policy>,
    user : User
  ) : Query<Policy> {
    // Filter by user's organization or producer code
    var userProducerCodes = user.ProducerCodes.map(\pc -> pc.Code)

    if (!userProducerCodes.Empty) {
      query.join(Policy#ProducerCodeOfRecord)
        .compareIn(ProducerCode#Code, userProducerCodes)
    }

    return query
  }

  private static function applyClaimSecurityFilter(
    query : Query<Claim>,
    user : User
  ) : Query<Claim> {
    // Filter by assigned user or group
    var userGroups = user.GroupUsers.map(\gu -> gu.Group)

    query.or(\orClause -> {
      orClause.compare(Claim#AssignedUser, Equals, user)
      if (!userGroups.Empty) {
        orClause.compareIn(Claim#AssignedGroup, userGroups)
      }
    })

    return query
  }

  private static function applyAccountSecurityFilter(
    query : Query<Account>,
    user : User
  ) : Query<Account> {
    // Filter by producer code assignment
    var userProducerCodes = user.ProducerCodes.map(\pc -> pc.PublicID)

    if (!userProducerCodes.Empty) {
      query.subselect(Account#ID, CompareIn,
        Query.make(AccountProducerCode)
          .compareIn(AccountProducerCode#ProducerCode, userProducerCodes)
          .subselect(AccountProducerCode#Account, CompareIn, Account#ID)
      )
    }

    return query
  }
}

// Secured query helper
class SecuredQuery {
  static function make<T extends KeyableBean>(type : Type<T>) : Query<T> {
    var query = Query.make(type)
    return RowLevelSecurity.applySecurityFilter(query)
  }
}

// Usage
class PolicyService {
  static function findPoliciesForCurrentUser() : List<Policy> {
    // Automatically applies row-level security
    return SecuredQuery.make(Policy)
      .compare(Policy#Status, Equals, PolicyStatus.TC_INFORCE)
      .select()
      .toList()
  }
}
```

### Step 6: API Authorization Middleware

```typescript
// API authorization middleware
import { Request, Response, NextFunction } from 'express';

interface SecurityContext {
  userId: string;
  roles: string[];
  apiRoles: string[];
  organizationId: string;
  producerCodes: string[];
}

// Extract security context from JWT
function extractSecurityContext(token: JWTPayload): SecurityContext {
  return {
    userId: token.sub,
    roles: token.roles || [],
    apiRoles: token.api_roles || [],
    organizationId: token.org_id,
    producerCodes: token.producer_codes || []
  };
}

// Require specific API role
function requireApiRole(...requiredRoles: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    const context = (req as any).securityContext as SecurityContext;

    if (!context) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const hasRequiredRole = requiredRoles.some(role =>
      context.apiRoles.includes(role)
    );

    if (!hasRequiredRole) {
      return res.status(403).json({
        error: 'Forbidden',
        message: 'Insufficient API role permissions',
        requiredRoles,
        userRoles: context.apiRoles
      });
    }

    next();
  };
}

// Row-level security filter for API responses
function applySecurityFilter<T>(
  data: T[],
  context: SecurityContext,
  filterFn: (item: T, context: SecurityContext) => boolean
): T[] {
  if (context.roles.includes('SystemAdmin')) {
    return data;
  }
  return data.filter(item => filterFn(item, context));
}

// Usage in routes
app.get('/api/policies',
  authMiddleware,
  requireApiRole('pc_policy_read', 'pc_policy_admin'),
  async (req, res) => {
    const context = (req as any).securityContext;

    let policies = await guidewireClient.getPolicies();

    // Apply row-level security
    policies = applySecurityFilter(policies, context, (policy, ctx) => {
      return ctx.producerCodes.includes(policy.producerCode) ||
             ctx.organizationId === policy.organizationId;
    });

    res.json(policies);
  }
);
```

## Role Matrix

| Role | PolicyCenter | ClaimCenter | BillingCenter |
|------|-------------|-------------|---------------|
| System Admin | Full Access | Full Access | Full Access |
| Underwriter | Submissions, Quotes | Read Only | Read Only |
| Claims Adjuster | Read Only | Claims, Payments | Read Only |
| Billing Admin | Read Only | Read Only | Full Access |
| Agent | Submissions, Read | FNOL Only | Read Only |
| Auditor | Read Only | Read Only | Read Only |

## Best Practices

| Practice | Description |
|----------|-------------|
| Least Privilege | Grant minimum necessary permissions |
| Role Separation | Separate roles by function, not convenience |
| Regular Audits | Review role assignments quarterly |
| Service Accounts | Use dedicated accounts for integrations |
| API Role Scoping | Scope API roles to specific endpoints |
