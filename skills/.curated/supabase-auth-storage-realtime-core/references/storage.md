# Supabase Storage — Full Walkthrough

Supabase Storage organizes files into buckets. Public buckets serve files via CDN URLs; private buckets require signed URLs or authenticated requests.

## TypeScript

```typescript
// ── Upload a file ──
const file = new File(['hello world'], 'hello.txt', { type: 'text/plain' })
const { data, error } = await supabase.storage
  .from('avatars')  // bucket name
  .upload('user123/avatar.png', file, {
    cacheControl: '3600',
    upsert: false,       // true → overwrite existing
    contentType: 'image/png',
  })
// data.path → 'user123/avatar.png'

// ── Download a file ──
const { data: blob, error: dlError } = await supabase.storage
  .from('avatars')
  .download('user123/avatar.png')
// blob is a Blob object — use URL.createObjectURL(blob) for display

// ── Get public URL (public buckets only, no auth required) ──
const { data: { publicUrl } } = supabase.storage
  .from('avatars')
  .getPublicUrl('user123/avatar.png')
// publicUrl → 'https://<project>.supabase.co/storage/v1/object/public/avatars/user123/avatar.png'

// ── Create signed URL (private buckets, time-limited access) ──
const { data: signedUrlData, error: signError } = await supabase.storage
  .from('documents')
  .createSignedUrl('reports/q4-2025.pdf', 3600)  // expires in 1 hour
// signedUrlData.signedUrl → one-time use URL with token parameter

// ── List files in a path ──
const { data: files, error: listError } = await supabase.storage
  .from('documents')
  .list('reports', {
    limit: 100,
    offset: 0,
    sortBy: { column: 'name', order: 'asc' },
  })

// ── Delete files ──
const { error: removeError } = await supabase.storage
  .from('documents')
  .remove(['reports/old-report.pdf', 'reports/draft.docx'])
```

## Bucket RLS policies — enforce access control in SQL migrations

```sql
-- Create buckets (run in a migration or SQL editor)
INSERT INTO storage.buckets (id, name, public)
VALUES ('avatars', 'avatars', true);   -- public: anyone can read

INSERT INTO storage.buckets (id, name, public)
VALUES ('documents', 'documents', false);  -- private: signed URLs only

-- Allow authenticated users to upload to their own folder
-- Convention: store files at <user_id>/filename.ext
CREATE POLICY "avatar_upload"
  ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'avatars'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

-- Allow anyone to view avatars (public bucket)
CREATE POLICY "avatar_public_read"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'avatars');

-- Allow users to manage only their own documents (all operations)
CREATE POLICY "documents_user_crud"
  ON storage.objects FOR ALL
  USING (
    bucket_id = 'documents'
    AND auth.uid()::text = (storage.foldername(name))[1]
  )
  WITH CHECK (
    bucket_id = 'documents'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

-- Allow users to delete only files they uploaded
CREATE POLICY "documents_owner_delete"
  ON storage.objects FOR DELETE
  USING (
    bucket_id = 'documents'
    AND auth.uid() = owner
  );
```

Python equivalents for the storage calls: [python-examples.md](python-examples.md).
