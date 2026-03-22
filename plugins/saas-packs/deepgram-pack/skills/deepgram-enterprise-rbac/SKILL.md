---
name: deepgram-enterprise-rbac
description: |
  Configure enterprise role-based access control for Deepgram integrations.
  Use when implementing team permissions, managing API key scopes,
  or setting up organization-level access controls.
  Trigger: "deepgram RBAC", "deepgram permissions", "deepgram access control",
  "deepgram team roles", "deepgram enterprise", "deepgram key scopes".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, api, rbac, enterprise]

---
# Deepgram Enterprise RBAC

## Overview
Role-based access control for enterprise Deepgram deployments. Maps five application roles to Deepgram API key scopes, implements scoped key provisioning via the Deepgram Management API, Express permission middleware, team management with auto-provisioned keys, and automated key rotation.

## Deepgram Scope Reference

| Scope | Permission | Used By |
|-------|-----------|---------|
| `member` | Full access (all scopes) | Admin only |
| `listen` | STT transcription | Developers, Services |
| `speak` | TTS synthesis | Developers, Services |
| `manage` | Project/key management | Admin |
| `usage:read` | View usage metrics | Analysts, Auditors |
| `keys:read` | List API keys | Auditors |
| `keys:write` | Create/delete keys | Admin |

## Instructions

### Step 1: Define Roles and Scope Mapping

```typescript
interface Role {
  name: string;
  deepgramScopes: string[];
  keyExpiry: number;        // Days
  description: string;
}

const ROLES: Record<string, Role> = {
  admin: {
    name: 'Admin',
    deepgramScopes: ['member'],
    keyExpiry: 90,
    description: 'Full access — project and key management',
  },
  developer: {
    name: 'Developer',
    deepgramScopes: ['listen', 'speak'],
    keyExpiry: 90,
    description: 'STT and TTS — no management access',
  },
  analyst: {
    name: 'Analyst',
    deepgramScopes: ['usage:read'],
    keyExpiry: 365,
    description: 'Read-only usage metrics',
  },
  service: {
    name: 'Service Account',
    deepgramScopes: ['listen'],
    keyExpiry: 90,
    description: 'STT only — for automated systems',
  },
  auditor: {
    name: 'Auditor',
    deepgramScopes: ['usage:read', 'keys:read'],
    keyExpiry: 30,
    description: 'Read-only audit access',
  },
};
```

### Step 2: Scoped Key Provisioning

```typescript
import { createClient } from '@deepgram/sdk';

class DeepgramKeyManager {
  private admin: ReturnType<typeof createClient>;
  private projectId: string;

  constructor(adminKey: string, projectId: string) {
    this.admin = createClient(adminKey);
    this.projectId = projectId;
  }

  async createScopedKey(userId: string, roleName: string): Promise<{
    keyId: string;
    key: string;
    scopes: string[];
    expiresAt: string;
  }> {
    const role = ROLES[roleName];
    if (!role) throw new Error(`Unknown role: ${roleName}`);

    const expirationDate = new Date(Date.now() + role.keyExpiry * 86400000);

    const { result, error } = await this.admin.manage.createProjectKey(
      this.projectId,
      {
        comment: `${roleName}:${userId}:${new Date().toISOString().split('T')[0]}`,
        scopes: role.deepgramScopes,
        expiration_date: expirationDate.toISOString(),
      }
    );

    if (error) throw new Error(`Key creation failed: ${error.message}`);

    console.log(`Created ${roleName} key for ${userId} (expires ${expirationDate.toISOString().split('T')[0]})`);

    return {
      keyId: result.key_id,
      key: result.key,
      scopes: role.deepgramScopes,
      expiresAt: expirationDate.toISOString(),
    };
  }

  async revokeKey(keyId: string) {
    const { error } = await this.admin.manage.deleteProjectKey(
      this.projectId, keyId
    );
    if (error) throw new Error(`Key revocation failed: ${error.message}`);
    console.log(`Revoked key: ${keyId}`);
  }

  async listKeys() {
    const { result, error } = await this.admin.manage.getProjectKeys(this.projectId);
    if (error) throw error;

    return result.api_keys.map((k: any) => ({
      keyId: k.api_key_id,
      comment: k.comment,
      scopes: k.scopes,
      created: k.created,
      expiration: k.expiration_date,
    }));
  }
}
```

### Step 3: Permission Middleware

```typescript
import { Request, Response, NextFunction } from 'express';

interface AuthenticatedRequest extends Request {
  user?: { id: string; role: string; deepgramKeyId: string };
}

function requireRole(...allowedRoles: string[]) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    if (!allowedRoles.includes(req.user.role)) {
      console.warn(`Access denied: user ${req.user.id} (${req.user.role}) tried to access ${req.path}`);
      return res.status(403).json({
        error: 'Insufficient permissions',
        required: allowedRoles,
        current: req.user.role,
      });
    }

    next();
  };
}

function requireScope(...requiredScopes: string[]) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const role = ROLES[req.user.role];
    const hasScopes = requiredScopes.every(
      s => role.deepgramScopes.includes(s) || role.deepgramScopes.includes('member')
    );

    if (!hasScopes) {
      return res.status(403).json({
        error: 'Missing required Deepgram scopes',
        required: requiredScopes,
        current: role.deepgramScopes,
      });
    }

    next();
  };
}

// Route examples:
app.post('/api/transcribe', requireScope('listen'), transcribeHandler);
app.post('/api/tts', requireScope('speak'), ttsHandler);
app.get('/api/usage', requireScope('usage:read'), usageHandler);
app.post('/api/keys', requireRole('admin'), createKeyHandler);
app.get('/api/audit', requireRole('admin', 'auditor'), auditHandler);
```

### Step 4: Team Management

```typescript
interface Team {
  id: string;
  name: string;
  projectId: string;       // Deepgram project ID
  members: Array<{
    userId: string;
    role: string;
    keyId: string;
    joinedAt: string;
  }>;
}

class TeamManager {
  private keyManager: DeepgramKeyManager;

  constructor(adminKey: string, projectId: string) {
    this.keyManager = new DeepgramKeyManager(adminKey, projectId);
  }

  async addMember(team: Team, userId: string, role: string) {
    // Provision Deepgram key with role scopes
    const key = await this.keyManager.createScopedKey(userId, role);

    team.members.push({
      userId,
      role,
      keyId: key.keyId,
      joinedAt: new Date().toISOString(),
    });

    console.log(`Added ${userId} to ${team.name} as ${role}`);
    return key;
  }

  async removeMember(team: Team, userId: string) {
    const member = team.members.find(m => m.userId === userId);
    if (!member) throw new Error(`User ${userId} not in team`);

    // Revoke Deepgram key
    await this.keyManager.revokeKey(member.keyId);

    team.members = team.members.filter(m => m.userId !== userId);
    console.log(`Removed ${userId} from ${team.name}, key revoked`);
  }

  async changeRole(team: Team, userId: string, newRole: string) {
    const member = team.members.find(m => m.userId === userId);
    if (!member) throw new Error(`User ${userId} not in team`);

    // Revoke old key, create new key with new role scopes
    await this.keyManager.revokeKey(member.keyId);
    const newKey = await this.keyManager.createScopedKey(userId, newRole);

    member.role = newRole;
    member.keyId = newKey.keyId;

    console.log(`Changed ${userId} role to ${newRole}`);
    return newKey;
  }
}
```

### Step 5: Automated Key Rotation

```typescript
async function rotateExpiringKeys(
  keyManager: DeepgramKeyManager,
  db: any,
  daysBeforeExpiry = 7
) {
  const keys = await keyManager.listKeys();
  const now = Date.now();
  const threshold = now + daysBeforeExpiry * 86400000;
  let rotated = 0;

  for (const key of keys) {
    if (!key.expiration) continue;
    const expiresAt = new Date(key.expiration).getTime();

    if (expiresAt < threshold) {
      // Parse role from comment (format: "role:userId:date")
      const [role, userId] = (key.comment ?? '').split(':');
      if (!role || !userId) {
        console.warn(`Cannot rotate key ${key.keyId} — unknown format: ${key.comment}`);
        continue;
      }

      console.log(`Rotating key for ${userId} (${role}), expires ${key.expiration}`);

      // Create new key
      const newKey = await keyManager.createScopedKey(userId, role);

      // Update database with new key ID
      await db.query(
        'UPDATE team_members SET key_id = $1 WHERE user_id = $2',
        [newKey.keyId, userId]
      );

      // Revoke old key (after a grace period, or immediately)
      await keyManager.revokeKey(key.keyId);
      rotated++;
    }
  }

  console.log(`Rotated ${rotated} keys expiring within ${daysBeforeExpiry} days`);
  return rotated;
}
```

### Step 6: Access Control Matrix

| Action | Admin | Developer | Analyst | Service | Auditor |
|--------|-------|-----------|---------|---------|---------|
| Transcribe (STT) | Yes | Yes | No | Yes | No |
| Text-to-Speech | Yes | Yes | No | No | No |
| View usage | Yes | No | Yes | No | Yes |
| Manage keys | Yes | No | No | No | No |
| View audit logs | Yes | No | No | No | Yes |
| Create projects | Yes | No | No | No | No |

## Output
- Five-role permission model with Deepgram scope mapping
- Scoped API key provisioning via Management API
- Express middleware (role-based and scope-based)
- Team management with auto-provisioned/revoked keys
- Automated key rotation for expiring keys

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | Key lacks scope | Create new key with correct scopes |
| Key expired | No rotation configured | Enable automated rotation |
| `manage.createProjectKey` fails | Admin key missing `member` scope | Use key with `member` scope |
| Team member can't transcribe | Wrong role assigned | Change role to `developer` or `service` |

## Resources
- [API Key Management](https://developers.deepgram.com/docs/api-key-management)
- [Project Management](https://developers.deepgram.com/docs/projects)
- [Deepgram Enterprise](https://deepgram.com/enterprise)
