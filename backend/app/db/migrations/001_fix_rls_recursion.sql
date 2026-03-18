-- Migration: Fix RLS + onboarding
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New Query)
--
-- Problem: During onboarding, the org is created before the user record,
-- so get_my_org_id() returns NULL and the SELECT policy on organizations
-- blocks the .select('id') after insert. Fix: use a SECURITY DEFINER
-- function that creates both org + user atomically.

-- ═══════════════════════════════════════════
-- Step 1: Drop ALL existing policies
-- ═══════════════════════════════════════════

DO $$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT policyname, tablename
    FROM pg_policies
    WHERE schemaname = 'public'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I', r.policyname, r.tablename);
  END LOOP;
END $$;

-- ═══════════════════════════════════════════
-- Step 2: Create helper functions
-- ═══════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.get_my_org_id()
RETURNS UUID
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT org_id FROM public.users WHERE id = auth.uid()
$$;

-- Onboarding: creates org + user in one atomic call, bypasses RLS
CREATE OR REPLACE FUNCTION public.onboard_user(
  p_workspace_name TEXT,
  p_email TEXT
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_org_id UUID;
BEGIN
  INSERT INTO organizations (name)
  VALUES (p_workspace_name)
  RETURNING id INTO v_org_id;

  INSERT INTO users (id, org_id, role, email)
  VALUES (auth.uid(), v_org_id, 'owner', p_email);

  RETURN v_org_id;
END;
$$;

-- ═══════════════════════════════════════════
-- Step 3: Recreate policies
-- ═══════════════════════════════════════════

-- Users
CREATE POLICY "users_select" ON users
  FOR SELECT USING (id = auth.uid() OR org_id = public.get_my_org_id());
CREATE POLICY "users_insert" ON users
  FOR INSERT WITH CHECK (id = auth.uid());
CREATE POLICY "users_update" ON users
  FOR UPDATE USING (id = auth.uid());

-- Organizations
CREATE POLICY "orgs_insert" ON organizations
  FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "orgs_select" ON organizations
  FOR SELECT USING (id = public.get_my_org_id());
CREATE POLICY "orgs_update" ON organizations
  FOR UPDATE USING (id = public.get_my_org_id());

-- Audits
CREATE POLICY "org_isolation_audits" ON audits
  USING (org_id = public.get_my_org_id());
CREATE POLICY "audits_insert" ON audits
  FOR INSERT WITH CHECK (org_id = public.get_my_org_id());

-- Issues
CREATE POLICY "org_isolation_issues" ON issues
  USING (org_id = public.get_my_org_id());

-- Reports
CREATE POLICY "org_isolation_reports" ON reports
  USING (org_id = public.get_my_org_id());

-- Integrations
CREATE POLICY "org_isolation_integrations" ON integrations
  USING (org_id = public.get_my_org_id());

-- Pull requests
CREATE POLICY "org_isolation_pull_requests" ON pull_requests
  USING (org_id = public.get_my_org_id());

-- Events
CREATE POLICY "org_isolation_events" ON events
  USING (org_id = public.get_my_org_id());

-- Session recordings
CREATE POLICY "org_isolation_session_recordings" ON session_recordings
  USING (org_id = public.get_my_org_id());

-- Audit embeddings
CREATE POLICY "org_isolation_audit_embeddings" ON audit_embeddings
  USING (org_id = public.get_my_org_id());
