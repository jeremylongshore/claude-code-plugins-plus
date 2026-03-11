# Clerk Data Handling - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: User Data Export
```typescript
// lib/data-export.ts
import { clerkClient } from '@clerk/nextjs/server'
import { db } from './db'

interface UserDataExport {
  clerk: ClerkUserData
  application: ApplicationUserData
  exportedAt: string
}

interface ClerkUserData {
  id: string
  email: string | undefined
  firstName: string | null
  lastName: string | null
  createdAt: Date
  lastSignIn: Date | null
  metadata: Record<string, any>
}

interface ApplicationUserData {
  profile: any
  orders: any[]
  preferences: any
  activityLog: any[]
}

export async function exportUserData(userId: string): Promise<UserDataExport> {
  const client = await clerkClient()

  // Get Clerk user data
  const clerkUser = await client.users.getUser(userId)

  // Get application data
  const [profile, orders, preferences, activityLog] = await Promise.all([
    db.userProfile.findUnique({ where: { clerkId: userId } }),
    db.order.findMany({ where: { userId }, orderBy: { createdAt: 'desc' } }),
    db.userPreference.findMany({ where: { userId } }),
    db.activityLog.findMany({
      where: { userId },
      orderBy: { timestamp: 'desc' },
      take: 1000
    })
  ])

  return {
    clerk: {
      id: clerkUser.id,
      email: clerkUser.primaryEmailAddress?.emailAddress,
      firstName: clerkUser.firstName,
      lastName: clerkUser.lastName,
      createdAt: new Date(clerkUser.createdAt),
      lastSignIn: clerkUser.lastSignInAt ? new Date(clerkUser.lastSignInAt) : null,
      metadata: {
        public: clerkUser.publicMetadata,
        // Note: privateMetadata should be handled carefully
      }
    },
    application: {
      profile: sanitizeForExport(profile),
      orders: orders.map(sanitizeForExport),
      preferences: preferences.map(sanitizeForExport),
      activityLog: activityLog.map(sanitizeForExport)
    },
    exportedAt: new Date().toISOString()
  }
}

function sanitizeForExport(data: any): any {
  if (!data) return null

  // Remove internal fields
  const { id, createdAt, updatedAt, ...rest } = data
  return rest
}
```

### Step 2: User Deletion (Right to be Forgotten)
```typescript
// lib/user-deletion.ts
import { clerkClient } from '@clerk/nextjs/server'
import { db } from './db'

interface DeletionResult {
  success: boolean
  deletedFrom: string[]
  errors: string[]
}

export async function deleteUserCompletely(userId: string): Promise<DeletionResult> {
  const result: DeletionResult = {
    success: true,
    deletedFrom: [],
    errors: []
  }

  // Step 1: Delete from application database
  try {
    await db.$transaction([
      // Delete related records first (foreign key constraints)
      db.activityLog.deleteMany({ where: { userId } }),
      db.order.deleteMany({ where: { userId } }),
      db.userPreference.deleteMany({ where: { userId } }),
      db.userProfile.delete({ where: { clerkId: userId } })
    ])
    result.deletedFrom.push('application_database')
  } catch (error: any) {
    result.errors.push(`Database deletion failed: ${error.message}`)
    result.success = false
  }

  // Step 2: Delete from Clerk
  try {
    const client = await clerkClient()
    await client.users.deleteUser(userId)
    result.deletedFrom.push('clerk')
  } catch (error: any) {
    result.errors.push(`Clerk deletion failed: ${error.message}`)
    result.success = false
  }

  // Step 3: Delete from external services
  try {
    await deleteFromExternalServices(userId)
    result.deletedFrom.push('external_services')
  } catch (error: any) {
    result.errors.push(`External service deletion failed: ${error.message}`)
  }

  // Log deletion for audit
  await logDeletionEvent(userId, result)

  return result
}

async function deleteFromExternalServices(userId: string) {
  // Delete from analytics
  // Delete from email service
  // Delete from payment provider
  // etc.
}

async function logDeletionEvent(userId: string, result: DeletionResult) {
  // Maintain audit log of deletions (anonymized)
  await db.deletionLog.create({
    data: {
      anonymizedId: hashUserId(userId),
      deletedAt: new Date(),
      success: result.success,
      errors: result.errors
    }
  })
}
```

### Step 3: Data Retention Policies
```typescript
// lib/data-retention.ts
import { db } from './db'
import { clerkClient } from '@clerk/nextjs/server'

interface RetentionPolicy {
  activityLogs: number // days
  sessions: number // days
  inactiveUsers: number // days
}

const RETENTION_POLICY: RetentionPolicy = {
  activityLogs: 90,
  sessions: 30,
  inactiveUsers: 365
}

export async function enforceRetentionPolicy() {
  const now = new Date()

  // Clean up old activity logs
  const activityCutoff = new Date(
    now.getTime() - RETENTION_POLICY.activityLogs * 24 * 60 * 60 * 1000
  )

  const deletedLogs = await db.activityLog.deleteMany({
    where: {
      timestamp: { lt: activityCutoff }
    }
  })

  console.log(`Deleted ${deletedLogs.count} old activity logs`)

  // Identify inactive users for notification
  const inactiveCutoff = new Date(
    now.getTime() - RETENTION_POLICY.inactiveUsers * 24 * 60 * 60 * 1000
  )

  const inactiveUsers = await db.userProfile.findMany({
    where: {
      lastActiveAt: { lt: inactiveCutoff },
      notifiedAboutInactivity: false
    }
  })

  // Notify inactive users before deletion
  for (const user of inactiveUsers) {
    await notifyInactiveUser(user.clerkId)
    await db.userProfile.update({
      where: { id: user.id },
      data: { notifiedAboutInactivity: true }
    })
  }

  console.log(`Notified ${inactiveUsers.length} inactive users`)
}
```

### Step 4: Consent Management
```typescript
// lib/consent.ts
import { currentUser } from '@clerk/nextjs/server'

interface ConsentRecord {
  marketing: boolean
  analytics: boolean
  thirdParty: boolean
  updatedAt: Date
}

export async function getConsent(userId: string): Promise<ConsentRecord | null> {
  const user = await currentUser()

  if (!user) return null

  return {
    marketing: user.publicMetadata?.consent?.marketing ?? false,
    analytics: user.publicMetadata?.consent?.analytics ?? false,
    thirdParty: user.publicMetadata?.consent?.thirdParty ?? false,
    updatedAt: new Date(user.publicMetadata?.consent?.updatedAt || user.createdAt)
  }
}

export async function updateConsent(
  userId: string,
  consent: Partial<ConsentRecord>
) {
  const client = await clerkClient()

  const user = await client.users.getUser(userId)
  const currentConsent = user.publicMetadata?.consent || {}

  await client.users.updateUser(userId, {
    publicMetadata: {
      ...user.publicMetadata,
      consent: {
        ...currentConsent,
        ...consent,
        updatedAt: new Date().toISOString()
      }
    }
  })

  // Log consent change for audit
  await logConsentChange(userId, consent)
}
```

### Step 5: GDPR API Endpoints
```typescript
// app/api/user/data/route.ts
import { auth } from '@clerk/nextjs/server'
import { exportUserData } from '@/lib/data-export'

// Data Export (GDPR Article 20)
export async function GET() {
  const { userId } = await auth()

  if (!userId) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const userData = await exportUserData(userId)

  return new Response(JSON.stringify(userData, null, 2), {
    headers: {
      'Content-Type': 'application/json',
      'Content-Disposition': `attachment; filename="user-data-${userId}.json"`
    }
  })
}

// app/api/user/delete/route.ts
import { deleteUserCompletely } from '@/lib/user-deletion'

// Data Deletion (GDPR Article 17)
export async function DELETE() {
  const { userId } = await auth()

  if (!userId) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // Require confirmation
  const confirmed = request.headers.get('X-Confirm-Delete') === 'true'
  if (!confirmed) {
    return Response.json(
      { error: 'Confirmation required', requiresHeader: 'X-Confirm-Delete: true' },
      { status: 400 }
    )
  }

  const result = await deleteUserCompletely(userId)

  if (result.success) {
    return Response.json({ message: 'Account deleted successfully' })
  } else {
    return Response.json(
      { error: 'Partial deletion', details: result },
      { status: 500 }
    )
  }
}
```

### Step 6: Audit Logging
```typescript
// lib/audit-log.ts
interface AuditEvent {
  type: 'data_access' | 'data_export' | 'data_deletion' | 'consent_change'
  userId: string
  performedBy: string
  details: Record<string, any>
  timestamp: Date
}

export async function logAuditEvent(event: Omit<AuditEvent, 'timestamp'>) {
  await db.auditLog.create({
    data: {
      ...event,
      timestamp: new Date()
    }
  })

  // For compliance, also log to external service
  if (process.env.AUDIT_LOG_ENDPOINT) {
    await fetch(process.env.AUDIT_LOG_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...event, timestamp: new Date() })
    })
  }
}
```

## Privacy Checklist

- [ ] Data export functionality (GDPR Article 20)
- [ ] Data deletion functionality (GDPR Article 17)
- [ ] Consent management
- [ ] Data retention policies
- [ ] Audit logging
- [ ] Privacy policy updated
- [ ] Cookie consent implemented
- [ ] Data processing agreements
