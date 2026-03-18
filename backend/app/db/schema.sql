-- Optilens Database Schema
-- Run this in Supabase SQL Editor to set up the database

-- Enable pgvector for re-audit memory
CREATE EXTENSION IF NOT EXISTS vector;

-- Organizations (multi-tenant root)
CREATE TABLE organizations (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  plan        TEXT DEFAULT 'solo' CHECK (plan IN ('solo','team','agency')),
  white_label_config JSONB DEFAULT '{}',
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Users (maps to Supabase auth.users)
CREATE TABLE users (
  id      UUID PRIMARY KEY REFERENCES auth.users(id),
  org_id  UUID REFERENCES organizations(id) ON DELETE CASCADE,
  role    TEXT DEFAULT 'owner' CHECK (role IN ('owner','admin','analyst','viewer')),
  email   TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audits
CREATE TABLE audits (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id               UUID REFERENCES organizations(id) ON DELETE CASCADE,
  created_by           UUID REFERENCES users(id),
  url                  TEXT NOT NULL,
  site_type            TEXT,
  framework_applied    TEXT[],
  status               TEXT DEFAULT 'queued' CHECK (status IN ('queued','running','complete','failed')),
  cro_score            INTEGER CHECK (cro_score BETWEEN 0 AND 100),
  previous_score       INTEGER,
  revenue_leak_monthly NUMERIC,
  revenue_leak_confidence TEXT CHECK (revenue_leak_confidence IN ('High','Medium','Estimated')),
  pages_audited        JSONB DEFAULT '[]',
  agent_outputs        JSONB DEFAULT '{}',
  audit_duration_seconds INTEGER,
  created_at           TIMESTAMPTZ DEFAULT NOW(),
  completed_at         TIMESTAMPTZ
);

-- Issues
CREATE TABLE issues (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  audit_id               UUID REFERENCES audits(id) ON DELETE CASCADE,
  org_id                 UUID REFERENCES organizations(id) ON DELETE CASCADE,
  agent                  TEXT CHECK (agent IN ('ux','copy','performance','seo','github')),
  severity               TEXT CHECK (severity IN ('critical','high','medium','low')),
  category               TEXT,
  title                  TEXT NOT NULL,
  description            TEXT,
  recommendation         TEXT,
  affected_element       TEXT,
  screenshot_url         TEXT,
  ice_score              NUMERIC,
  impact_score           INTEGER CHECK (impact_score BETWEEN 1 AND 10),
  confidence_score       INTEGER CHECK (confidence_score BETWEEN 1 AND 10),
  effort_score           INTEGER CHECK (effort_score BETWEEN 1 AND 10),
  revenue_impact_monthly NUMERIC,
  ab_variants            JSONB DEFAULT '[]',
  status                 TEXT DEFAULT 'open' CHECK (status IN ('open','in_progress','resolved','dismissed')),
  created_at             TIMESTAMPTZ DEFAULT NOW()
);

-- Reports
CREATE TABLE reports (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  audit_id       UUID REFERENCES audits(id) ON DELETE CASCADE,
  org_id         UUID REFERENCES organizations(id) ON DELETE CASCADE,
  pdf_url        TEXT,
  excel_url      TEXT,
  screenshots_zip_url TEXT,
  white_labeled  BOOLEAN DEFAULT FALSE,
  generated_at   TIMESTAMPTZ DEFAULT NOW(),
  expires_at     TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '90 days')
);

-- Integrations (OAuth tokens, encrypted)
CREATE TABLE integrations (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id               UUID REFERENCES organizations(id) ON DELETE CASCADE,
  type                 TEXT CHECK (type IN ('ga4','gsc','github')),
  access_token_encrypted TEXT,
  refresh_token_encrypted TEXT,
  scope                TEXT,
  metadata             JSONB DEFAULT '{}',
  connected_at         TIMESTAMPTZ DEFAULT NOW(),
  last_used_at         TIMESTAMPTZ,
  UNIQUE(org_id, type)
);

-- Pull Requests (GitHub Agent)
CREATE TABLE pull_requests (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  audit_id             UUID REFERENCES audits(id) ON DELETE CASCADE,
  org_id               UUID REFERENCES organizations(id) ON DELETE CASCADE,
  github_pr_url        TEXT,
  github_pr_number     INTEGER,
  repo_name            TEXT,
  status               TEXT DEFAULT 'draft' CHECK (status IN ('draft','pending_approval','approved','merged','rejected')),
  diff_summary         JSONB DEFAULT '{}',
  files_changed        TEXT[],
  projected_lift_percent NUMERIC,
  safety_checklist     JSONB DEFAULT '[]',
  created_at           TIMESTAMPTZ DEFAULT NOW(),
  approved_at          TIMESTAMPTZ,
  approved_by          UUID REFERENCES users(id)
);

-- rrweb events (heatmap + session data)
CREATE TABLE events (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id      UUID REFERENCES organizations(id) ON DELETE CASCADE,
  audit_id    UUID REFERENCES audits(id) ON DELETE SET NULL,
  page_url    TEXT NOT NULL,
  event_type  TEXT CHECK (event_type IN ('click','scroll','move')),
  x           FLOAT,
  y           FLOAT,
  viewport_w  INTEGER,
  viewport_h  INTEGER,
  session_id  TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Session recordings
CREATE TABLE session_recordings (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id         UUID REFERENCES organizations(id) ON DELETE CASCADE,
  page_url       TEXT NOT NULL,
  events_json    JSONB NOT NULL,
  duration_seconds INTEGER,
  session_id     TEXT NOT NULL,
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Audit embeddings (pgvector — for re-audit memory)
CREATE TABLE audit_embeddings (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  audit_id    UUID REFERENCES audits(id) ON DELETE CASCADE,
  org_id      UUID REFERENCES organizations(id) ON DELETE CASCADE,
  content     TEXT NOT NULL,
  embedding   vector(1536),
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════
-- Row Level Security (RLS) — org isolation
-- ═══════════════════════════════════════════

ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE audits ENABLE ROW LEVEL SECURITY;
ALTER TABLE issues ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE pull_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_recordings ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_embeddings ENABLE ROW LEVEL SECURITY;

-- Helper function to get the current user's org_id without triggering RLS.
-- SECURITY DEFINER runs as the function owner (bypasses RLS on users table),
-- which prevents infinite recursion when policies on any table need org_id.
CREATE OR REPLACE FUNCTION public.get_my_org_id()
RETURNS UUID
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT org_id FROM public.users WHERE id = auth.uid()
$$;

-- ── Users table policies ──
-- Users can read their own row + rows in the same org.
-- No subquery on users here — just auth.uid() or the helper function.
CREATE POLICY "users_select" ON users
  FOR SELECT USING (id = auth.uid() OR org_id = public.get_my_org_id());

CREATE POLICY "users_insert" ON users
  FOR INSERT WITH CHECK (id = auth.uid());

CREATE POLICY "users_update" ON users
  FOR UPDATE USING (id = auth.uid());

-- ── Organizations table policies ──
CREATE POLICY "orgs_insert" ON organizations
  FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "orgs_select" ON organizations
  FOR SELECT USING (id = public.get_my_org_id());

CREATE POLICY "orgs_update" ON organizations
  FOR UPDATE USING (id = public.get_my_org_id());

-- ── All other tables — org isolation via helper function ──
CREATE POLICY "org_isolation_audits" ON audits
  USING (org_id = public.get_my_org_id());

CREATE POLICY "audits_insert" ON audits
  FOR INSERT WITH CHECK (org_id = public.get_my_org_id());

CREATE POLICY "org_isolation_issues" ON issues
  USING (org_id = public.get_my_org_id());

CREATE POLICY "org_isolation_reports" ON reports
  USING (org_id = public.get_my_org_id());

CREATE POLICY "org_isolation_integrations" ON integrations
  USING (org_id = public.get_my_org_id());

CREATE POLICY "org_isolation_pull_requests" ON pull_requests
  USING (org_id = public.get_my_org_id());

CREATE POLICY "org_isolation_events" ON events
  USING (org_id = public.get_my_org_id());

CREATE POLICY "org_isolation_session_recordings" ON session_recordings
  USING (org_id = public.get_my_org_id());

CREATE POLICY "org_isolation_audit_embeddings" ON audit_embeddings
  USING (org_id = public.get_my_org_id());

-- ═══════════════════════════════════════════
-- Indexes for performance
-- ═══════════════════════════════════════════

CREATE INDEX idx_audits_org_id ON audits(org_id);
CREATE INDEX idx_audits_status ON audits(status);
CREATE INDEX idx_issues_audit_id ON issues(audit_id);
CREATE INDEX idx_events_org_audit ON events(org_id, audit_id);
CREATE INDEX idx_events_created ON events(created_at);
CREATE INDEX idx_sessions_org ON session_recordings(org_id);
CREATE INDEX idx_embeddings ON audit_embeddings USING ivfflat (embedding vector_cosine_ops);

-- ═══════════════════════════════════════════
-- Storage buckets (create via Supabase dashboard or API)
-- reports: PDFs, Excel files
-- screenshots: annotated screenshots
-- exports: ZIP files
-- All buckets: private, served via signed URLs only
-- ═══════════════════════════════════════════
