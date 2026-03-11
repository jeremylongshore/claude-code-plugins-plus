# Speak Enterprise RBAC - Implementation Guide

Detailed implementation reference for the speak-enterprise-rbac skill.

## Role Definitions for Language Learning

| Role | Permissions | Use Case |
|------|-------------|----------|
| Admin | Full access | Organization administrators |
| Instructor | Create/manage courses, view learner progress | Teachers, tutors |
| Manager | View reports, manage teams | Department heads |
| Learner | Access assigned courses, track own progress | Students, employees |
| Observer | Read-only access to progress | Parents, supervisors |
| Service | API access only | Automated systems |


## Role Implementation

```typescript
enum SpeakRole {
  Admin = 'admin',
  Instructor = 'instructor',
  Manager = 'manager',
  Learner = 'learner',
  Observer = 'observer',
  Service = 'service',
}

interface SpeakPermissions {
  // Lesson permissions
  createLessons: boolean;
  accessAllLanguages: boolean;
  assignCourses: boolean;

  // User permissions
  viewLearnerProgress: boolean;
  viewAllProgress: boolean;
  manageUsers: boolean;

  // Content permissions
  createContent: boolean;
  editContent: boolean;
  deleteContent: boolean;

  // Admin permissions
  manageBilling: boolean;
  manageSettings: boolean;
  viewAuditLogs: boolean;
}

const ROLE_PERMISSIONS: Record<SpeakRole, SpeakPermissions> = {
  admin: {
    createLessons: true,
    accessAllLanguages: true,
    assignCourses: true,
    viewLearnerProgress: true,
    viewAllProgress: true,
    manageUsers: true,
    createContent: true,
    editContent: true,
    deleteContent: true,
    manageBilling: true,
    manageSettings: true,
    viewAuditLogs: true,
  },
  instructor: {
    createLessons: true,
    accessAllLanguages: true,
    assignCourses: true,
    viewLearnerProgress: true,
    viewAllProgress: false, // Only their students
    manageUsers: false,
    createContent: true,
    editContent: true,
    deleteContent: false,
    manageBilling: false,
    manageSettings: false,
    viewAuditLogs: false,
  },
  manager: {
    createLessons: false,
    accessAllLanguages: true,
    assignCourses: true,
    viewLearnerProgress: true,
    viewAllProgress: true, // Team members
    manageUsers: false,
    createContent: false,
    editContent: false,
    deleteContent: false,
    manageBilling: false,
    manageSettings: false,
    viewAuditLogs: false,
  },
  learner: {
    createLessons: false,
    accessAllLanguages: false, // Based on plan
    assignCourses: false,
    viewLearnerProgress: false,
    viewAllProgress: false,
    manageUsers: false,
    createContent: false,
    editContent: false,
    deleteContent: false,
    manageBilling: false,
    manageSettings: false,
    viewAuditLogs: false,
  },
  observer: {
    createLessons: false,
    accessAllLanguages: false,
    assignCourses: false,
    viewLearnerProgress: true, // Assigned learners only
    viewAllProgress: false,
    manageUsers: false,
    createContent: false,
    editContent: false,
    deleteContent: false,
    manageBilling: false,
    manageSettings: false,
    viewAuditLogs: false,
  },
  service: {
    createLessons: false,
    accessAllLanguages: true,
    assignCourses: false,
    viewLearnerProgress: true,
    viewAllProgress: true,
    manageUsers: false,
    createContent: false,
    editContent: false,
    deleteContent: false,
    manageBilling: false,
    manageSettings: false,
    viewAuditLogs: true,
  },
};

function checkPermission(
  role: SpeakRole,
  permission: keyof SpeakPermissions
): boolean {
  return ROLE_PERMISSIONS[role][permission];
}
```


## SSO Integration

### SAML Configuration
```typescript
// Speak SAML setup for enterprise SSO
const samlConfig = {
  entryPoint: 'https://idp.school.edu/saml/sso',
  issuer: 'https://speak.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourschool.com/auth/speak/callback',
  identifierFormat: 'urn:oasis:names:tc:SAML:2.0:nameid-format:emailAddress',
};

// Map IdP groups to Speak roles
const groupRoleMapping: Record<string, SpeakRole> = {
  'Faculty': SpeakRole.Instructor,
  'Students': SpeakRole.Learner,
  'Staff': SpeakRole.Learner,
  'Department-Heads': SpeakRole.Manager,
  'IT-Admins': SpeakRole.Admin,
  'Parents': SpeakRole.Observer,
};

// Extract role from SAML attributes
function mapSamlToRole(samlAttributes: SamlAttributes): SpeakRole {
  const groups = samlAttributes.memberOf || [];

  // Check groups in priority order
  for (const [group, role] of Object.entries(groupRoleMapping)) {
    if (groups.includes(group)) {
      return role;
    }
  }

  // Default to learner
  return SpeakRole.Learner;
}
```

### OAuth2/OIDC Integration
```typescript
import { OAuth2Client } from '@speak/sdk';

const oauthClient = new OAuth2Client({
  clientId: process.env.SPEAK_OAUTH_CLIENT_ID!,
  clientSecret: process.env.SPEAK_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourschool.com/auth/speak/callback',
  scopes: [
    'lessons:read',
    'lessons:write',
    'progress:read',
    'users:read',
  ],
});

// Exchange code for tokens
async function handleOAuthCallback(code: string): Promise<AuthResult> {
  const tokens = await oauthClient.exchangeCode(code);

  // Get user info
  const userInfo = await oauthClient.getUserInfo(tokens.accessToken);

  // Map to internal user with role
  return {
    user: {
      id: userInfo.sub,
      email: userInfo.email,
      name: userInfo.name,
      role: mapOidcToRole(userInfo),
    },
    tokens,
  };
}
```


## Organization Management

```typescript
interface SpeakOrganization {
  id: string;
  name: string;
  type: 'school' | 'business' | 'individual';
  ssoEnabled: boolean;
  enforceSso: boolean;
  allowedDomains: string[];
  defaultRole: SpeakRole;
  enabledLanguages: string[];
  maxSeats: number;
  features: {
    customContent: boolean;
    progressReports: boolean;
    instructorDashboard: boolean;
    parentPortal: boolean;
    apiAccess: boolean;
  };
}

async function createOrganization(
  config: Partial<SpeakOrganization>
): Promise<SpeakOrganization> {
  const org = await speakClient.organizations.create({
    name: config.name!,
    type: config.type || 'business',
    settings: {
      sso: {
        enabled: config.ssoEnabled || false,
        enforced: config.enforceSso || false,
        domains: config.allowedDomains || [],
      },
      defaults: {
        role: config.defaultRole || SpeakRole.Learner,
        languages: config.enabledLanguages || ['en'],
      },
      features: config.features,
    },
  });

  await auditLog({
    action: 'organization_created',
    organizationId: org.id,
    config,
  });

  return org;
}
```


## Team and Class Management

```typescript
interface Team {
  id: string;
  organizationId: string;
  name: string;
  type: 'class' | 'department' | 'cohort';
  instructorIds: string[];
  learnerIds: string[];
  languages: string[];
  curriculum?: CurriculumConfig;
}

class TeamManager {
  async createTeam(config: Partial<Team>): Promise<Team> {
    const team = await db.teams.insert({
      ...config,
      id: crypto.randomUUID(),
      createdAt: new Date(),
    });

    // Assign learners to team
    if (config.learnerIds) {
      await this.assignLearnersToTeam(team.id, config.learnerIds);
    }

    return team;
  }

  async assignLearnersToTeam(teamId: string, learnerIds: string[]): Promise<void> {
    const team = await db.teams.findOne({ id: teamId });

    for (const learnerId of learnerIds) {
      await db.teamMemberships.upsert({
        teamId,
        userId: learnerId,
        role: 'learner',
        assignedAt: new Date(),
        languages: team.languages,
      });

      // Create curriculum progress for learner
      if (team.curriculum) {
        await createCurriculumProgress(learnerId, team.curriculum);
      }
    }
  }

  async getTeamProgress(teamId: string): Promise<TeamProgressReport> {
    const team = await db.teams.findOne({ id: teamId });
    const members = await db.teamMemberships.find({ teamId });

    const progressData = await Promise.all(
      members.map(async (m) => ({
        userId: m.userId,
        progress: await speakClient.progress.get(m.userId),
      }))
    );

    return {
      team,
      totalLearners: members.length,
      averagePronunciation: calculateAverage(progressData, 'pronunciationScore'),
      lessonsCompleted: sum(progressData, 'lessonsCompleted'),
      averageStreak: calculateAverage(progressData, 'currentStreak'),
      languageBreakdown: aggregateByLanguage(progressData),
    };
  }
}
```


## Access Control Middleware

```typescript
function requireSpeakPermission(
  requiredPermission: keyof SpeakPermissions
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as { speakRole: SpeakRole; organizationId: string };

    if (!checkPermission(user.speakRole, requiredPermission)) {
      await auditLog({
        action: 'permission_denied',
        userId: user.id,
        permission: requiredPermission,
        resource: req.path,
      });

      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing permission: ${requiredPermission}`,
      });
    }

    next();
  };
}

// Middleware for resource ownership
function requireResourceAccess(resourceType: 'team' | 'learner' | 'content') {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user;
    const resourceId = req.params.id;

    const hasAccess = await checkResourceAccess(user, resourceType, resourceId);

    if (!hasAccess) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `No access to ${resourceType} ${resourceId}`,
      });
    }

    next();
  };
}

// Usage
app.get('/api/teams/:id/progress',
  requireSpeakPermission('viewLearnerProgress'),
  requireResourceAccess('team'),
  getTeamProgress
);

app.delete('/api/content/:id',
  requireSpeakPermission('deleteContent'),
  requireResourceAccess('content'),
  deleteContent
);
```


## Audit Trail

```typescript
interface SpeakAuditEntry {
  timestamp: Date;
  userId: string;
  role: SpeakRole;
  organizationId: string;
  action: string;
  resource: string;
  resourceId?: string;
  success: boolean;
  ipAddress: string;
  userAgent: string;
  metadata?: Record<string, any>;
}

async function logSpeakAccess(entry: Omit<SpeakAuditEntry, 'timestamp'>): Promise<void> {
  const log: SpeakAuditEntry = { ...entry, timestamp: new Date() };

  await auditDb.insert(log);

  // Alert on suspicious activity
  if (entry.action.includes('delete') && !entry.success) {
    await alertOnSuspiciousActivity(entry);
  }

  // Alert on unusual access patterns
  await detectAnomalousAccess(entry);
}

// Generate compliance reports
async function generateAccessReport(
  organizationId: string,
  dateRange: DateRange
): Promise<AccessReport> {
  const logs = await auditDb.find({
    organizationId,
    timestamp: { $gte: dateRange.start, $lte: dateRange.end },
  });

  return {
    organizationId,
    period: dateRange,
    totalActions: logs.length,
    actionsByType: groupBy(logs, 'action'),
    actionsByRole: groupBy(logs, 'role'),
    failedAccessAttempts: logs.filter(l => !l.success),
    uniqueUsers: new Set(logs.map(l => l.userId)).size,
  };
}
```


## Detailed Examples

### Quick Permission Check
```typescript
if (!checkPermission(user.role, 'viewLearnerProgress')) {
  throw new ForbiddenError('Cannot view learner progress');
}
```

### Instructor Dashboard Access
```typescript
app.get('/instructor/dashboard',
  requireSpeakPermission('viewLearnerProgress'),
  async (req, res) => {
    const teams = await teamManager.getInstructorTeams(req.user.id);
    const progress = await Promise.all(
      teams.map(t => teamManager.getTeamProgress(t.id))
    );
    res.json({ teams, progress });
  }
);
```

