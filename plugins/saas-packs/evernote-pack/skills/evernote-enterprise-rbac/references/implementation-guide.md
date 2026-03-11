# Evernote Enterprise RBAC - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Permission Model

```javascript
// models/permissions.js

const PermissionLevel = {
  NONE: 0,
  READ: 1,
  READ_ACTIVITY: 2,
  MODIFY: 3,
  FULL_ACCESS: 4
};

const NotebookPrivilegeLevel = {
  READ_NOTEBOOK: 'READ_NOTEBOOK',
  MODIFY_NOTEBOOK_PLUS_ACTIVITY: 'MODIFY_NOTEBOOK_PLUS_ACTIVITY',
  READ_NOTEBOOK_PLUS_ACTIVITY: 'READ_NOTEBOOK_PLUS_ACTIVITY',
  GROUP: 'GROUP',
  FULL_ACCESS: 'FULL_ACCESS'
};

class Permission {
  constructor(data) {
    this.level = data.level;
    this.scope = data.scope; // 'note', 'notebook', 'global'
    this.targetGuid = data.targetGuid;
    this.grantedBy = data.grantedBy;
    this.expiresAt = data.expiresAt;
  }

  canRead() {
    return this.level >= PermissionLevel.READ;
  }

  canModify() {
    return this.level >= PermissionLevel.MODIFY;
  }

  canDelete() {
    return this.level >= PermissionLevel.FULL_ACCESS;
  }

  canShare() {
    return this.level >= PermissionLevel.FULL_ACCESS;
  }

  isExpired() {
    return this.expiresAt && Date.now() > this.expiresAt;
  }
}

module.exports = { PermissionLevel, NotebookPrivilegeLevel, Permission };
```

### Step 2: Role Definitions

```javascript
// models/roles.js

const Roles = {
  // System roles
  SUPER_ADMIN: {
    name: 'super_admin',
    description: 'Full system access',
    permissions: ['*'],
    evernoteAccess: 'full'
  },

  ADMIN: {
    name: 'admin',
    description: 'Organization administrator',
    permissions: [
      'users:read', 'users:write',
      'notebooks:read', 'notebooks:write',
      'notes:read', 'notes:write',
      'settings:read', 'settings:write'
    ],
    evernoteAccess: 'full'
  },

  MANAGER: {
    name: 'manager',
    description: 'Team manager',
    permissions: [
      'users:read',
      'notebooks:read', 'notebooks:write',
      'notes:read', 'notes:write'
    ],
    evernoteAccess: 'modify'
  },

  MEMBER: {
    name: 'member',
    description: 'Regular team member',
    permissions: [
      'notebooks:read',
      'notes:read', 'notes:write'
    ],
    evernoteAccess: 'modify'
  },

  VIEWER: {
    name: 'viewer',
    description: 'Read-only access',
    permissions: [
      'notebooks:read',
      'notes:read'
    ],
    evernoteAccess: 'read'
  },

  GUEST: {
    name: 'guest',
    description: 'Limited guest access',
    permissions: [
      'shared:read'
    ],
    evernoteAccess: 'read'
  }
};

class Role {
  constructor(roleConfig) {
    this.name = roleConfig.name;
    this.description = roleConfig.description;
    this.permissions = roleConfig.permissions;
    this.evernoteAccess = roleConfig.evernoteAccess;
  }

  hasPermission(permission) {
    if (this.permissions.includes('*')) return true;
    return this.permissions.includes(permission);
  }

  canAccessEvernote(level) {
    const levels = ['none', 'read', 'modify', 'full'];
    return levels.indexOf(this.evernoteAccess) >= levels.indexOf(level);
  }
}

module.exports = { Roles, Role };
```

### Step 3: RBAC Service

```javascript
// services/rbac-service.js
const { Role, Roles } = require('../models/roles');
const { Permission, PermissionLevel } = require('../models/permissions');

class RBACService {
  constructor(db) {
    this.db = db;
    this.permissionCache = new Map();
  }

  /**
   * Assign role to user
   */
  async assignRole(userId, roleName, organizationId = null) {
    await this.db.query(`
      INSERT INTO user_roles (user_id, role_name, organization_id)
      VALUES ($1, $2, $3)
      ON CONFLICT (user_id, organization_id) DO UPDATE SET
        role_name = EXCLUDED.role_name,
        updated_at = NOW()
    `, [userId, roleName, organizationId]);

    this.invalidateCache(userId);
  }

  /**
   * Get user's role
   */
  async getUserRole(userId, organizationId = null) {
    const result = await this.db.query(`
      SELECT role_name FROM user_roles
      WHERE user_id = $1 AND (organization_id = $2 OR organization_id IS NULL)
      ORDER BY organization_id NULLS LAST
      LIMIT 1
    `, [userId, organizationId]);

    if (result.rows.length === 0) {
      return new Role(Roles.GUEST);
    }

    const roleConfig = Roles[result.rows[0].role_name.toUpperCase()];
    return roleConfig ? new Role(roleConfig) : new Role(Roles.GUEST);
  }

  /**
   * Check if user has permission
   */
  async hasPermission(userId, permission, organizationId = null) {
    const role = await this.getUserRole(userId, organizationId);
    return role.hasPermission(permission);
  }

  /**
   * Grant note-level permission
   */
  async grantNotePermission(noteGuid, userId, level, grantedBy, expiresAt = null) {
    await this.db.query(`
      INSERT INTO note_permissions (note_guid, user_id, permission_level, granted_by, expires_at)
      VALUES ($1, $2, $3, $4, $5)
      ON CONFLICT (note_guid, user_id) DO UPDATE SET
        permission_level = EXCLUDED.permission_level,
        granted_by = EXCLUDED.granted_by,
        expires_at = EXCLUDED.expires_at,
        updated_at = NOW()
    `, [noteGuid, userId, level, grantedBy, expiresAt]);

    this.invalidateCache(userId);
  }

  /**
   * Check user's permission on a note
   */
  async getNotePermission(noteGuid, userId) {
    // Check direct permission
    const direct = await this.db.query(`
      SELECT permission_level, expires_at FROM note_permissions
      WHERE note_guid = $1 AND user_id = $2
    `, [noteGuid, userId]);

    if (direct.rows.length > 0) {
      const perm = direct.rows[0];
      if (!perm.expires_at || Date.now() < new Date(perm.expires_at).getTime()) {
        return new Permission({
          level: perm.permission_level,
          scope: 'note',
          targetGuid: noteGuid
        });
      }
    }

    // Check notebook-level permission
    const notebook = await this.db.query(`
      SELECT np.permission_level, np.expires_at
      FROM notebook_permissions np
      JOIN notes n ON n.notebook_guid = np.notebook_guid
      WHERE n.guid = $1 AND np.user_id = $2
    `, [noteGuid, userId]);

    if (notebook.rows.length > 0) {
      const perm = notebook.rows[0];
      if (!perm.expires_at || Date.now() < new Date(perm.expires_at).getTime()) {
        return new Permission({
          level: perm.permission_level,
          scope: 'notebook',
          targetGuid: noteGuid
        });
      }
    }

    // No permission
    return new Permission({
      level: PermissionLevel.NONE,
      scope: 'none',
      targetGuid: noteGuid
    });
  }

  /**
   * List accessible notebooks for user
   */
  async getAccessibleNotebooks(userId, organizationId = null) {
    const role = await this.getUserRole(userId, organizationId);

    // Admins and above see all
    if (role.hasPermission('notebooks:read') && role.name === 'admin') {
      return this.db.query(`
        SELECT * FROM notebooks WHERE organization_id = $1
      `, [organizationId]);
    }

    // Others see only permitted notebooks
    return this.db.query(`
      SELECT n.* FROM notebooks n
      LEFT JOIN notebook_permissions np ON n.guid = np.notebook_guid AND np.user_id = $2
      WHERE n.organization_id = $1
        AND (n.owner_id = $2 OR np.permission_level IS NOT NULL)
    `, [organizationId, userId]);
  }

  invalidateCache(userId) {
    // Clear cached permissions for user
    for (const key of this.permissionCache.keys()) {
      if (key.startsWith(`${userId}:`)) {
        this.permissionCache.delete(key);
      }
    }
  }
}

module.exports = RBACService;
```

### Step 4: Authorization Middleware

```javascript
// middleware/authorization.js
const RBACService = require('../services/rbac-service');

function authorize(requiredPermission) {
  return async (req, res, next) => {
    const rbac = new RBACService(req.app.get('db'));
    const userId = req.user?.id;
    const organizationId = req.params.organizationId || req.user?.organizationId;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const hasPermission = await rbac.hasPermission(userId, requiredPermission, organizationId);

    if (!hasPermission) {
      return res.status(403).json({
        error: 'Forbidden',
        required: requiredPermission
      });
    }

    next();
  };
}

function authorizeNoteAccess(requiredLevel) {
  return async (req, res, next) => {
    const rbac = new RBACService(req.app.get('db'));
    const userId = req.user?.id;
    const noteGuid = req.params.noteGuid;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const permission = await rbac.getNotePermission(noteGuid, userId);

    if (!checkPermissionLevel(permission, requiredLevel)) {
      return res.status(403).json({
        error: 'Forbidden',
        required: requiredLevel,
        current: permission.level
      });
    }

    req.notePermission = permission;
    next();
  };
}

function checkPermissionLevel(permission, required) {
  const levels = {
    'read': permission.canRead(),
    'modify': permission.canModify(),
    'delete': permission.canDelete(),
    'share': permission.canShare()
  };
  return levels[required] || false;
}

module.exports = { authorize, authorizeNoteAccess };
```

### Step 5: Multi-Tenant Support

```javascript
// services/tenant-service.js

class TenantService {
  constructor(db) {
    this.db = db;
  }

  /**
   * Create new organization (tenant)
   */
  async createOrganization(data) {
    const result = await this.db.query(`
      INSERT INTO organizations (name, slug, owner_id, settings)
      VALUES ($1, $2, $3, $4)
      RETURNING *
    `, [data.name, data.slug, data.ownerId, JSON.stringify(data.settings || {})]);

    const org = result.rows[0];

    // Assign owner as admin
    await this.db.query(`
      INSERT INTO user_roles (user_id, role_name, organization_id)
      VALUES ($1, 'admin', $2)
    `, [data.ownerId, org.id]);

    return org;
  }

  /**
   * Add user to organization
   */
  async addMember(organizationId, userId, roleName = 'member') {
    // Check if already member
    const existing = await this.db.query(`
      SELECT id FROM organization_members
      WHERE organization_id = $1 AND user_id = $2
    `, [organizationId, userId]);

    if (existing.rows.length > 0) {
      throw new Error('User already member of organization');
    }

    await this.db.query(`
      INSERT INTO organization_members (organization_id, user_id)
      VALUES ($1, $2)
    `, [organizationId, userId]);

    await this.db.query(`
      INSERT INTO user_roles (user_id, role_name, organization_id)
      VALUES ($1, $2, $3)
    `, [userId, roleName, organizationId]);

    return { success: true };
  }

  /**
   * Remove user from organization
   */
  async removeMember(organizationId, userId) {
    await this.db.query(`
      DELETE FROM user_roles WHERE user_id = $1 AND organization_id = $2
    `, [userId, organizationId]);

    await this.db.query(`
      DELETE FROM organization_members WHERE organization_id = $1 AND user_id = $2
    `, [organizationId, userId]);

    return { success: true };
  }

  /**
   * Get organization settings
   */
  async getSettings(organizationId) {
    const result = await this.db.query(`
      SELECT settings FROM organizations WHERE id = $1
    `, [organizationId]);

    return result.rows[0]?.settings || {};
  }

  /**
   * Update organization settings
   */
  async updateSettings(organizationId, settings) {
    await this.db.query(`
      UPDATE organizations SET settings = $1, updated_at = NOW()
      WHERE id = $2
    `, [JSON.stringify(settings), organizationId]);

    return { success: true };
  }
}

module.exports = TenantService;
```

### Step 6: Evernote Business Integration

```javascript
// services/evernote-business-service.js
const Evernote = require('evernote');

class EvernoteBusinessService {
  constructor(accessToken, businessToken) {
    this.personalClient = new Evernote.Client({
      token: accessToken,
      sandbox: false
    });

    this.businessToken = businessToken;
  }

  /**
   * Get business user store
   */
  async getBusinessUserStore() {
    const userStore = this.personalClient.getUserStore();

    // Get business info
    const user = await userStore.getUser();

    if (!user.businessUserInfo) {
      throw new Error('User is not a business member');
    }

    // Create business client
    const businessClient = new Evernote.Client({
      token: this.businessToken,
      sandbox: false
    });

    return businessClient.getUserStore();
  }

  /**
   * Get business note store
   */
  async getBusinessNoteStore() {
    const userStore = this.personalClient.getUserStore();
    const user = await userStore.getUser();

    if (!user.businessUserInfo) {
      throw new Error('User is not a business member');
    }

    const businessClient = new Evernote.Client({
      token: this.businessToken,
      sandbox: false
    });

    return businessClient.getNoteStore();
  }

  /**
   * List business notebooks
   */
  async listBusinessNotebooks() {
    const noteStore = await this.getBusinessNoteStore();
    return noteStore.listNotebooks();
  }

  /**
   * Create business notebook
   */
  async createBusinessNotebook(name) {
    const noteStore = await this.getBusinessNoteStore();

    const notebook = new Evernote.Types.Notebook();
    notebook.name = name;

    return noteStore.createNotebook(notebook);
  }

  /**
   * Share notebook with team
   */
  async shareNotebookWithTeam(notebookGuid, emails, privilege) {
    const noteStore = await this.getBusinessNoteStore();

    const sharedNotebook = new Evernote.Types.SharedNotebook();
    sharedNotebook.notebookGuid = notebookGuid;
    sharedNotebook.email = emails.join(',');
    sharedNotebook.privilege = privilege;

    return noteStore.createSharedNotebook(sharedNotebook);
  }
}

module.exports = EvernoteBusinessService;
```

### Step 7: API Routes with RBAC

```javascript
// routes/notes.js
const express = require('express');
const { authorize, authorizeNoteAccess } = require('../middleware/authorization');

const router = express.Router();

// List notes - requires read permission
router.get('/',
  authorize('notes:read'),
  async (req, res) => {
    // ... list notes
  }
);

// Get single note - requires note-level read
router.get('/:noteGuid',
  authorizeNoteAccess('read'),
  async (req, res) => {
    // ... get note
  }
);

// Update note - requires note-level modify
router.put('/:noteGuid',
  authorizeNoteAccess('modify'),
  async (req, res) => {
    // ... update note
  }
);

// Delete note - requires note-level delete
router.delete('/:noteGuid',
  authorizeNoteAccess('delete'),
  async (req, res) => {
    // ... delete note
  }
);

// Share note - requires note-level share
router.post('/:noteGuid/share',
  authorizeNoteAccess('share'),
  async (req, res) => {
    // ... share note
  }
);

module.exports = router;
```


## Evernote Permission Levels

| Level | Scope | Capabilities |
|-------|-------|--------------|
| Read | Note | View content |
| Modify | Note | Edit content |
| Full Access | Note | Edit, share, delete |
| Notebook Read | Notebook | Read all notes |
| Notebook Modify | Notebook | Edit all notes |
| Notebook Full | Notebook | Full control |


## Database Schema

```sql
-- Organizations (tenants)
CREATE TABLE organizations (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(100) UNIQUE NOT NULL,
  owner_id INTEGER,
  settings JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Organization members
CREATE TABLE organization_members (
  organization_id INTEGER REFERENCES organizations(id),
  user_id INTEGER,
  joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (organization_id, user_id)
);

-- User roles
CREATE TABLE user_roles (
  user_id INTEGER,
  role_name VARCHAR(50) NOT NULL,
  organization_id INTEGER REFERENCES organizations(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, organization_id)
);

-- Note permissions
CREATE TABLE note_permissions (
  note_guid UUID,
  user_id INTEGER,
  permission_level INTEGER NOT NULL,
  granted_by INTEGER,
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (note_guid, user_id)
);

-- Notebook permissions
CREATE TABLE notebook_permissions (
  notebook_guid UUID,
  user_id INTEGER,
  permission_level INTEGER NOT NULL,
  granted_by INTEGER,
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (notebook_guid, user_id)
);
```
