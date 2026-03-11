# Obsidian Enterprise RBAC - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Permission System
```typescript
// src/rbac/permissions.ts
export type Role = 'viewer' | 'editor' | 'contributor' | 'manager' | 'admin';
export type Permission = 'read' | 'write' | 'delete' | 'admin' | 'settings';

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  teamIds: string[];
  projectIds: string[];
}

export interface FolderPermission {
  path: string;
  allowedRoles: Role[];
  allowedTeams?: string[];
  allowedUsers?: string[];
}

const rolePermissions: Record<Role, Permission[]> = {
  viewer: ['read'],
  editor: ['read', 'write'],
  contributor: ['read', 'write', 'delete'], // delete own only
  manager: ['read', 'write', 'delete', 'settings'],
  admin: ['read', 'write', 'delete', 'admin', 'settings'],
};

export class PermissionService {
  private currentUser: User | null = null;
  private folderPermissions: FolderPermission[] = [];

  setCurrentUser(user: User): void {
    this.currentUser = user;
  }

  setFolderPermissions(permissions: FolderPermission[]): void {
    this.folderPermissions = permissions;
  }

  hasPermission(permission: Permission): boolean {
    if (!this.currentUser) return false;
    return rolePermissions[this.currentUser.role].includes(permission);
  }

  canAccessFolder(path: string): boolean {
    if (!this.currentUser) return false;

    // Admin can access everything
    if (this.currentUser.role === 'admin') return true;

    // Check folder permissions
    const folderPerm = this.findFolderPermission(path);
    if (!folderPerm) return true; // No restrictions

    // Check role
    if (folderPerm.allowedRoles.includes(this.currentUser.role)) {
      return true;
    }

    // Check team membership
    if (folderPerm.allowedTeams) {
      const hasTeam = folderPerm.allowedTeams.some(
        teamId => this.currentUser!.teamIds.includes(teamId)
      );
      if (hasTeam) return true;
    }

    // Check user allowlist
    if (folderPerm.allowedUsers) {
      if (folderPerm.allowedUsers.includes(this.currentUser.id)) {
        return true;
      }
    }

    return false;
  }

  canReadFile(path: string): boolean {
    return this.hasPermission('read') && this.canAccessFolder(path);
  }

  canWriteFile(path: string): boolean {
    return this.hasPermission('write') && this.canAccessFolder(path);
  }

  canDeleteFile(path: string, ownerId?: string): boolean {
    if (!this.currentUser) return false;

    // Contributor can only delete own files
    if (this.currentUser.role === 'contributor') {
      return ownerId === this.currentUser.id && this.canAccessFolder(path);
    }

    return this.hasPermission('delete') && this.canAccessFolder(path);
  }

  private findFolderPermission(path: string): FolderPermission | null {
    // Find most specific matching folder permission
    let match: FolderPermission | null = null;
    let matchLength = 0;

    for (const perm of this.folderPermissions) {
      if (path.startsWith(perm.path) && perm.path.length > matchLength) {
        match = perm;
        matchLength = perm.path.length;
      }
    }

    return match;
  }
}
```

### Step 2: Protected Operations Wrapper
```typescript
// src/rbac/protected-vault.ts
import { App, TFile, Notice } from 'obsidian';
import { PermissionService } from './permissions';

export class ProtectedVault {
  constructor(
    private app: App,
    private permissions: PermissionService
  ) {}

  async readFile(file: TFile): Promise<string | null> {
    if (!this.permissions.canReadFile(file.path)) {
      new Notice('Permission denied: Cannot read this file');
      return null;
    }
    return this.app.vault.read(file);
  }

  async writeFile(file: TFile, content: string): Promise<boolean> {
    if (!this.permissions.canWriteFile(file.path)) {
      new Notice('Permission denied: Cannot write to this file');
      return false;
    }
    await this.app.vault.modify(file, content);
    return true;
  }

  async createFile(path: string, content: string): Promise<TFile | null> {
    if (!this.permissions.canWriteFile(path)) {
      new Notice('Permission denied: Cannot create files in this folder');
      return null;
    }
    return this.app.vault.create(path, content);
  }

  async deleteFile(file: TFile, ownerId?: string): Promise<boolean> {
    if (!this.permissions.canDeleteFile(file.path, ownerId)) {
      new Notice('Permission denied: Cannot delete this file');
      return false;
    }
    await this.app.vault.delete(file);
    return true;
  }

  getAccessibleFiles(): TFile[] {
    return this.app.vault.getMarkdownFiles().filter(
      file => this.permissions.canReadFile(file.path)
    );
  }
}
```

### Step 3: User Management
```typescript
// src/rbac/user-manager.ts
import { Plugin } from 'obsidian';

export interface TeamConfig {
  id: string;
  name: string;
  members: string[];
  folders: string[];
}

export interface RBACConfig {
  enabled: boolean;
  users: Record<string, {
    role: Role;
    teams: string[];
  }>;
  teams: TeamConfig[];
  folderPermissions: FolderPermission[];
}

export class UserManager {
  private config: RBACConfig;
  private plugin: Plugin;

  constructor(plugin: Plugin) {
    this.plugin = plugin;
    this.config = this.loadConfig();
  }

  private loadConfig(): RBACConfig {
    // Load from plugin settings or external config
    return {
      enabled: true,
      users: {},
      teams: [],
      folderPermissions: [],
    };
  }

  getCurrentUser(): User | null {
    // Get current user from auth system
    // This could be from local storage, external auth, etc.
    const userId = this.getCurrentUserId();
    if (!userId) return null;

    const userConfig = this.config.users[userId];
    if (!userConfig) return null;

    return {
      id: userId,
      name: this.getUserName(userId),
      email: this.getUserEmail(userId),
      role: userConfig.role,
      teamIds: userConfig.teams,
      projectIds: this.getProjectsForUser(userId),
    };
  }

  private getCurrentUserId(): string | null {
    // Implementation depends on auth system
    // Could be from: local file, external service, etc.
    return localStorage.getItem('obsidian-user-id');
  }

  private getUserName(userId: string): string {
    // Fetch from user directory
    return userId;
  }

  private getUserEmail(userId: string): string {
    // Fetch from user directory
    return `${userId}@example.com`;
  }

  private getProjectsForUser(userId: string): string[] {
    // Get projects user has access to
    return [];
  }

  getTeams(): TeamConfig[] {
    return this.config.teams;
  }

  getFolderPermissions(): FolderPermission[] {
    return this.config.folderPermissions;
  }

  // Admin functions
  async addUser(userId: string, role: Role, teams: string[]): Promise<void> {
    this.config.users[userId] = { role, teams };
    await this.saveConfig();
  }

  async updateUserRole(userId: string, role: Role): Promise<void> {
    if (this.config.users[userId]) {
      this.config.users[userId].role = role;
      await this.saveConfig();
    }
  }

  async addFolderPermission(permission: FolderPermission): Promise<void> {
    this.config.folderPermissions.push(permission);
    await this.saveConfig();
  }

  private async saveConfig(): Promise<void> {
    // Save to plugin data or external storage
  }
}
```

### Step 4: Audit Logging
```typescript
// src/rbac/audit-log.ts
export interface AuditEntry {
  timestamp: string;
  userId: string;
  action: 'read' | 'write' | 'delete' | 'permission_denied' | 'login' | 'logout';
  resource: string;
  details?: Record<string, any>;
  success: boolean;
}

export class AuditLogger {
  private entries: AuditEntry[] = [];
  private maxEntries = 1000;

  log(entry: Omit<AuditEntry, 'timestamp'>): void {
    const fullEntry: AuditEntry = {
      ...entry,
      timestamp: new Date().toISOString(),
    };

    this.entries.push(fullEntry);

    // Trim old entries
    if (this.entries.length > this.maxEntries) {
      this.entries = this.entries.slice(-this.maxEntries);
    }

    // Console log for debugging
    console.log(`[Audit] ${fullEntry.action}: ${fullEntry.resource}`, {
      user: fullEntry.userId,
      success: fullEntry.success,
    });
  }

  logAccess(userId: string, path: string, action: 'read' | 'write' | 'delete', success: boolean): void {
    this.log({
      userId,
      action,
      resource: path,
      success,
    });
  }

  logPermissionDenied(userId: string, path: string, requestedAction: string): void {
    this.log({
      userId,
      action: 'permission_denied',
      resource: path,
      details: { requestedAction },
      success: false,
    });
  }

  getEntries(filter?: {
    userId?: string;
    action?: AuditEntry['action'];
    since?: Date;
  }): AuditEntry[] {
    let results = [...this.entries];

    if (filter?.userId) {
      results = results.filter(e => e.userId === filter.userId);
    }

    if (filter?.action) {
      results = results.filter(e => e.action === filter.action);
    }

    if (filter?.since) {
      results = results.filter(e =>
        new Date(e.timestamp) >= filter.since!
      );
    }

    return results;
  }

  getPermissionDenials(): AuditEntry[] {
    return this.entries.filter(e => e.action === 'permission_denied');
  }

  export(): string {
    return JSON.stringify(this.entries, null, 2);
  }
}
```

### Step 5: UI Integration
```typescript
// src/rbac/rbac-ui.ts
import { App, Modal, Setting } from 'obsidian';
import { Role, User, PermissionService } from './permissions';

export class UserRoleModal extends Modal {
  private user: User;
  private onSave: (role: Role) => void;

  constructor(app: App, user: User, onSave: (role: Role) => void) {
    super(app);
    this.user = user;
    this.onSave = onSave;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.empty();

    contentEl.createEl('h2', { text: `Edit User: ${this.user.name}` });

    new Setting(contentEl)
      .setName('Role')
      .setDesc('User role determines permissions')
      .addDropdown(dropdown => {
        dropdown
          .addOption('viewer', 'Viewer')
          .addOption('editor', 'Editor')
          .addOption('contributor', 'Contributor')
          .addOption('manager', 'Manager')
          .addOption('admin', 'Admin')
          .setValue(this.user.role)
          .onChange(value => {
            this.user.role = value as Role;
          });
      });

    new Setting(contentEl)
      .addButton(btn => btn
        .setButtonText('Save')
        .setCta()
        .onClick(() => {
          this.onSave(this.user.role);
          this.close();
        }))
      .addButton(btn => btn
        .setButtonText('Cancel')
        .onClick(() => this.close()));
  }
}

// Status bar indicator
export function addRoleIndicator(plugin: Plugin, permissions: PermissionService): void {
  const user = permissions.getCurrentUser();
  if (!user) return;

  const statusBar = plugin.addStatusBarItem();
  statusBar.setText(`${user.role.toUpperCase()}`);
  statusBar.addClass(`role-indicator-${user.role}`);
}
```


## Complete Examples

### Configuration File
```yaml
enabled: true

users:
  alice:
    role: admin
    teams: [management, engineering]
  bob:
    role: editor
    teams: [engineering]
  charlie:
    role: viewer
    teams: [support]

teams:
  - id: management
    name: Management
    folders: [management/, projects/]
  - id: engineering
    name: Engineering
    folders: [engineering/, projects/]
  - id: support
    name: Support
    folders: [support/, public/]

folderPermissions:
  - path: public/
    allowedRoles: [viewer, editor, contributor, manager, admin]
  - path: management/
    allowedRoles: [manager, admin]
    allowedTeams: [management]
  - path: admin/
    allowedRoles: [admin]
```


## Access Control Concepts

### Role Hierarchy
| Role | Read | Write | Delete | Admin | Settings |
|------|------|-------|--------|-------|----------|
| Viewer | Yes | No | No | No | No |
| Editor | Yes | Yes | No | No | No |
| Contributor | Yes | Yes | Own | No | No |
| Manager | Yes | Yes | Yes | No | View |
| Admin | Yes | Yes | Yes | Yes | Full |

### Folder-Based Permissions
```
vault/
├── public/           # All roles can read
├── team/             # Editors+ can read/write
├── projects/
│   ├── project-a/    # Project members only
│   └── project-b/    # Project members only
├── management/       # Managers+ only
└── admin/            # Admins only
```
