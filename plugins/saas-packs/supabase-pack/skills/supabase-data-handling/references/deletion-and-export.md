# User Deletion and Data Export

Implement GDPR Article 17 (right to erasure) with `auth.admin.deleteUser()` and Article 15 (right of access) with SQL-based data export.

## Right to deletion — complete user erasure

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);

interface DeletionResult {
  userId: string;
  tablesProcessed: string[];
  storageFilesDeleted: number;
  authDeleted: boolean;
  auditLogId: string;
  completedAt: string;
}

async function deleteUserData(userId: string): Promise<DeletionResult> {
  const tablesProcessed: string[] = [];
  let storageFilesDeleted = 0;

  // 1. Delete user data from application tables (cascade order)
  const tablesToPurge = ['comments', 'orders', 'documents', 'profiles'];

  for (const table of tablesToPurge) {
    const { error } = await supabase
      .from(table)
      .delete()
      .eq('user_id', userId);

    if (error && !error.message.includes('does not exist')) {
      console.error(`Failed to delete from ${table}:`, error.message);
    } else {
      tablesProcessed.push(table);
    }
  }

  // 2. Delete user files from storage
  const { data: buckets } = await supabase.storage.listBuckets();
  for (const bucket of buckets ?? []) {
    const { data: files } = await supabase.storage
      .from(bucket.name)
      .list(`users/${userId}`);

    if (files && files.length > 0) {
      const paths = files.map((f) => `users/${userId}/${f.name}`);
      const { error } = await supabase.storage
        .from(bucket.name)
        .remove(paths);

      if (!error) storageFilesDeleted += paths.length;
    }
  }

  // 3. Delete the auth user (removes from auth.users)
  const { error: authError } = await supabase.auth.admin.deleteUser(userId);
  const authDeleted = !authError;

  if (authError) {
    console.error('Auth deletion failed:', authError.message);
  }

  // 4. Create audit log entry (required — must survive deletion)
  const { data: auditEntry } = await supabase
    .from('gdpr_audit_log')
    .insert({
      action: 'USER_DELETION',
      subject_id: userId,
      tables_purged: tablesProcessed,
      storage_files_deleted: storageFilesDeleted,
      auth_deleted: authDeleted,
      performed_by: 'system',
      legal_basis: 'GDPR Article 17 — Right to Erasure',
    })
    .select('id')
    .single();

  return {
    userId,
    tablesProcessed,
    storageFilesDeleted,
    authDeleted,
    auditLogId: auditEntry?.id ?? 'unknown',
    completedAt: new Date().toISOString(),
  };
}

// GDPR audit log table (create this migration)
// CREATE TABLE gdpr_audit_log (
//   id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
//   action text NOT NULL,
//   subject_id uuid NOT NULL,
//   tables_purged text[] DEFAULT '{}',
//   storage_files_deleted int DEFAULT 0,
//   auth_deleted boolean DEFAULT false,
//   performed_by text NOT NULL,
//   legal_basis text,
//   created_at timestamptz DEFAULT now()
// );
// -- Audit logs must NEVER be deleted (compliance requirement)
// ALTER TABLE gdpr_audit_log ENABLE ROW LEVEL SECURITY;
// CREATE POLICY "admin_only" ON gdpr_audit_log FOR ALL USING (false);
```

## Data subject access request (DSAR) — export all user data

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);

interface DataExport {
  exportedAt: string;
  subjectId: string;
  legalBasis: string;
  data: Record<string, unknown[]>;
  storageFiles: string[];
}

async function exportUserData(userId: string): Promise<DataExport> {
  const exportData: Record<string, unknown[]> = {};

  // Export from each table containing user data
  const tables = ['profiles', 'orders', 'documents', 'comments'];

  for (const table of tables) {
    const { data, error } = await supabase
      .from(table)
      .select('*')
      .eq('user_id', userId);

    if (!error && data) {
      exportData[table] = data;
    }
  }

  // List user files in storage
  const storageFiles: string[] = [];
  const { data: buckets } = await supabase.storage.listBuckets();
  for (const bucket of buckets ?? []) {
    const { data: files } = await supabase.storage
      .from(bucket.name)
      .list(`users/${userId}`);

    for (const file of files ?? []) {
      storageFiles.push(`${bucket.name}/users/${userId}/${file.name}`);
    }
  }

  // Log the export for compliance
  await supabase.from('gdpr_audit_log').insert({
    action: 'DATA_EXPORT',
    subject_id: userId,
    performed_by: 'system',
    legal_basis: 'GDPR Article 15 — Right of Access',
  });

  return {
    exportedAt: new Date().toISOString(),
    subjectId: userId,
    legalBasis: 'GDPR Article 15 — Right of Access',
    data: exportData,
    storageFiles,
  };
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
