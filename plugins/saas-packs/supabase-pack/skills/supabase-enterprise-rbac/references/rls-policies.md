# RLS Policies with JWT Role Claims

Write Row Level Security policies that read `auth.jwt() ->> 'role'` and `auth.jwt() -> 'app_metadata' ->> 'org_id'` to enforce role-based and organization-scoped access.

## Role-based RLS policies

```sql
-- Create a helper function to extract role from JWT
CREATE OR REPLACE FUNCTION public.get_user_role()
RETURNS text AS $$
  SELECT coalesce(
    auth.jwt() -> 'app_metadata' ->> 'role',
    'viewer'  -- default role if not set
  );
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- Create a helper function to extract org_id from JWT
CREATE OR REPLACE FUNCTION public.get_user_org_id()
RETURNS text AS $$
  SELECT auth.jwt() -> 'app_metadata' ->> 'org_id';
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- Enable RLS on all tables
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_members ENABLE ROW LEVEL SECURITY;

-- Projects: org members can read, editors+ can create/update, admins can delete
CREATE POLICY "org_members_read_projects" ON public.projects
  FOR SELECT USING (
    org_id = get_user_org_id()
  );

CREATE POLICY "editors_create_projects" ON public.projects
  FOR INSERT WITH CHECK (
    org_id = get_user_org_id()
    AND get_user_role() IN ('admin', 'editor')
  );

CREATE POLICY "editors_update_projects" ON public.projects
  FOR UPDATE USING (
    org_id = get_user_org_id()
    AND get_user_role() IN ('admin', 'editor')
  );

CREATE POLICY "admins_delete_projects" ON public.projects
  FOR DELETE USING (
    org_id = get_user_org_id()
    AND get_user_role() = 'admin'
  );

-- Documents: org-scoped with role-based write access
CREATE POLICY "org_read_documents" ON public.documents
  FOR SELECT USING (
    org_id = get_user_org_id()
  );

CREATE POLICY "editors_write_documents" ON public.documents
  FOR INSERT WITH CHECK (
    org_id = get_user_org_id()
    AND get_user_role() IN ('admin', 'editor')
  );

CREATE POLICY "owner_or_admin_update_documents" ON public.documents
  FOR UPDATE USING (
    org_id = get_user_org_id()
    AND (
      created_by = auth.uid()
      OR get_user_role() = 'admin'
    )
  );

-- Team members: admins manage team, members can read
CREATE POLICY "org_read_team" ON public.team_members
  FOR SELECT USING (
    org_id = get_user_org_id()
  );

CREATE POLICY "admins_manage_team" ON public.team_members
  FOR ALL USING (
    org_id = get_user_org_id()
    AND get_user_role() = 'admin'
  );
```

## Organization-scoped access table schema

```sql
-- Organizations table
CREATE TABLE public.organizations (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  name text NOT NULL,
  slug text UNIQUE NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- Team members junction table
CREATE TABLE public.team_members (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  org_id uuid REFERENCES public.organizations(id) ON DELETE CASCADE,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  role text NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'editor', 'member', 'viewer')),
  invited_by uuid REFERENCES auth.users(id),
  created_at timestamptz DEFAULT now(),
  UNIQUE(org_id, user_id)
);

-- Projects scoped to organizations
CREATE TABLE public.projects (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  org_id uuid REFERENCES public.organizations(id) ON DELETE CASCADE,
  name text NOT NULL,
  created_by uuid REFERENCES auth.users(id),
  created_at timestamptz DEFAULT now()
);

-- Index for fast org-scoped queries
CREATE INDEX idx_team_members_org ON public.team_members(org_id);
CREATE INDEX idx_team_members_user ON public.team_members(user_id);
CREATE INDEX idx_projects_org ON public.projects(org_id);
```
