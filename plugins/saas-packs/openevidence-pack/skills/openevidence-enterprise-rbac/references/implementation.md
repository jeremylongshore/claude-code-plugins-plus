# OpenEvidence Enterprise RBAC - Implementation Details

## Role and Permission Definitions
```typescript
export enum ClinicalRole { Physician = 'physician', Nurse = 'nurse', Pharmacist = 'pharmacist', Resident = 'resident', Admin = 'admin', Auditor = 'auditor', Integration = 'integration' }

export const ROLE_PERMISSIONS: Record<ClinicalRole, ClinicalPermissions> = {
  [ClinicalRole.Physician]: { clinicalQuery: true, deepConsult: true, drugInfo: true, guidelineAccess: true, exportResults: true, viewAuditLogs: false, manageUsers: false, manageSettings: false },
  [ClinicalRole.Nurse]: { clinicalQuery: true, deepConsult: false, drugInfo: true, guidelineAccess: true, exportResults: false, viewAuditLogs: false, manageUsers: false, manageSettings: false },
  [ClinicalRole.Admin]: { clinicalQuery: true, deepConsult: true, drugInfo: true, guidelineAccess: true, exportResults: true, viewAuditLogs: true, manageUsers: true, manageSettings: true },
  // ... see full definitions in SKILL.md
};
```

## SSO Integration (SAML)
```typescript
import { Strategy as SamlStrategy } from 'passport-saml';
export function configureSAML(config: SAMLConfig): void {
  passport.use(new SamlStrategy({
    entryPoint: config.entryPoint,
    issuer: config.issuer,
    cert: config.cert,
    callbackUrl: config.callbackUrl,
  }, async (profile, done) => {
    const user = await findOrCreateUser({ email: profile.nameID, groups: profile.groups || [] });
    const role = mapGroupsToRole(profile.groups);
    return done(null, { ...user, role });
  }));
}
```

## OAuth2/OIDC Integration
```typescript
import { Strategy as OpenIDConnectStrategy } from 'passport-openidconnect';
export function configureOIDC(config: OIDCConfig): void {
  passport.use(new OpenIDConnectStrategy({ ...config }, async (issuer, profile, done) => {
    const user = await findOrCreateUser({ email: profile.emails?.[0]?.value, providerId: profile.id });
    const role = await getRoleFromClaims(profile._json);
    return done(null, { ...user, role });
  }));
}
```

## Permission Middleware
```typescript
export function requirePermission(permission: keyof ClinicalPermissions) {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    if (!req.user) return res.status(401).json({ error: 'Authentication required' });
    if (!hasPermission(req.user.role, permission)) {
      await auditLogger.logAccess({ userId: req.user.id, action: 'access_denied', resourceType: permission });
      return res.status(403).json({ error: 'Forbidden', message: `Permission '${permission}' required` });
    }
    next();
  };
}
```

## Organization Management
```typescript
export class OrganizationManager {
  async createOrganization(config): Promise<Organization> { /* ... */ }
  async addUser(orgId: string, userId: string, role: ClinicalRole): Promise<void> { /* ... */ }
  async updateUserRole(orgId: string, userId: string, newRole: ClinicalRole): Promise<void> { /* ... */ }
}
```

## Session Management
```typescript
export function configureSession(redis: Redis) {
  return {
    store: new RedisStore({ client: redis }),
    secret: process.env.SESSION_SECRET!,
    cookie: { secure: true, httpOnly: true, maxAge: 8 * 60 * 60 * 1000, sameSite: 'strict' },
    rolling: true,
  };
}
```
