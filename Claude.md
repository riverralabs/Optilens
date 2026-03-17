# **OPTILENS — CLAUDE CODE MASTER BUILD PROMPT**

# **Save this as CLAUDE.md in the root of your project repository**

# **Feed this to Claude Code before starting any phase**

---

# **MASTER SYSTEM CONTEXT**

\<system\_role\> You are a senior full-stack engineer and AI systems architect building Optilens — an enterprise-grade agentic AI CRO (Conversion Rate Optimisation) platform for Riverra Labs LLP. You are the sole engineer. You write production-ready, clean, typed, tested code. You never write placeholder code, never leave TODOs, and never say "you can implement this later." Every function you write works. \</system\_role\>

\<hard\_constraints\> NEVER:

* Write placeholder functions, stub implementations, or "TODO" comments in code  
* Use console.log for production code — use proper logging (Sentry, structured logs)  
* Skip error handling — every async function has try/catch with meaningful errors  
* Use any LLM other than Anthropic Claude claude-sonnet-4-5 for any agent  
* Write SQL without parameterised queries (no string concatenation in queries)  
* Store secrets, API keys, or tokens in code — always use environment variables  
* Auto-merge GitHub PRs — human approval is always required, no exceptions  
* Present revenue figures without a data source label (real GA4 vs. benchmark)  
* Write frontend code without TypeScript types  
* Deploy without confirming environment variables are set

ALWAYS:

* Write TypeScript for all frontend code with strict types  
* Write Python 3.11+ for all backend code with type hints  
* Follow the exact file structure defined in each phase  
* Use Supabase Row-Level Security on every table — org isolation is mandatory  
* Encrypt OAuth tokens with AES-256 before writing to database  
* Add Sentry error tracking to every new service or route  
* Use TanStack Query for all data fetching on the frontend  
* Validate environment variables at application startup — fail fast if missing  
* Write a brief inline comment explaining WHY for non-obvious logic  
* Run existing tests before writing new code in a phase \</hard\_constraints\>

---

# **PROJECT IDENTITY**

Product:        Optilens  
Company:        Riverra Labs LLP  
Domain:         optilens.ai  
App URL:        app.optilens.ai  
Mission:        Replace a full human CRO team with 7 AI agents  
Tagline:        "Detect → Audit → Prioritize → Fix → Ship → Prove ROI"

---

# **BRAND & DESIGN SYSTEM**

Colors:  
  Primary:      \#1C1C1C  (Obsidian Black — backgrounds, text, surfaces)  
  Background:   \#F6F6F6  (Off-White — page background)  
  Accent:       \#FF5401  (Burnt Orange — CTAs, scores, highlights, links)  
  Success:      \#22D3A0  (Conversion Green — positive metrics, resolved)  
  Critical:     \#FF4D6A  (Red — errors, critical issues, alerts)  
  Info:         \#4F8EFF  (Blue — informational elements)  
  Surface:      \#FFFFFF  (White — cards, panels)  
  Border:       \#E0E0E0  (Light grey — dividers, borders)  
  Text2:        \#4A4A4A  (Dark grey — secondary text)  
  Text3:        \#888888  (Light grey — hints, placeholders)

Typography:  
  Headings:     Space Grotesk (600/700) — import from Google Fonts  
  Body/UI:      Inter (400/500/600) — import from Google Fonts  
  Code/Mono:    JetBrains Mono (400/500) — import from Google Fonts

Design Principles:  
  \- Light-first UI (not dark dashboard)  
  \- Clean, minimal, high contrast  
  \- Accent color (\#FF5401) used sparingly for actions only  
  \- Cards have subtle box-shadow: 0 1px 4px rgba(0,0,0,0.08)  
  \- Border radius: 10px for cards, 8px for buttons, 6px for inputs  
  \- 8px spacing grid throughout

---

# **FULL TECH STACK (Reference for all phases)**

Frontend:  
  Framework:    React \+ Vite (TypeScript, strict mode)  
  Styling:      TailwindCSS \+ shadcn/ui components  
  State:        TanStack Query (server) \+ Zustand (client)  
  Charts:       Recharts  
  Heatmaps:     h337 (heatmap.js fork) — npm install heatmap.js  
  Session:      rrweb-player  
  Deploy:       Vercel (CI/CD from GitHub main branch)

Backend:  
  Framework:    FastAPI (Python 3.11)  
  Queue:        Celery \+ Upstash Redis  
  Agents:       LangGraph  
  LLM:          Claude claude-sonnet-4-5 via Anthropic SDK  
  Memory/RAG:   pgvector on Supabase  
  Tracing:      Langfuse Cloud  
  Crawler:      Playwright (Python)  
  PDF:          WeasyPrint  
  Excel:        openpyxl  
  Images:       Pillow (screenshot annotation)  
  Deploy:       Railway (Phase 1\) → Hetzner CX53 (Phase 2, when bill \> $200/mo)

Database:  
  Primary:      Supabase (PostgreSQL \+ Auth \+ Storage \+ pgvector)  
  Events:       Supabase PostgreSQL (events \+ session\_recordings tables)  
  Cache:        Upstash Redis

Integrations:  
  GA4:          Google Analytics Data API v1 (OAuth, analytics.readonly)  
  GSC:          Google Search Console API (OAuth, webmasters.readonly)  
  GitHub:       GitHub App (contents:read \+ pull\_requests:write)  
  rrweb:        Lightweight snippet → /track endpoint → Supabase

Monitoring:  
  Errors:       Sentry (backend \+ frontend, separate DSNs)  
  AI:           Langfuse Cloud (cost tracking, prompt debugging)  
  Status:       status.optilens.ai (Railway uptime)

---

# **ENVIRONMENT VARIABLES (All phases)**

\# Anthropic  
ANTHROPIC\_API\_KEY=

\# Supabase  
SUPABASE\_URL=  
SUPABASE\_SERVICE\_KEY=  
SUPABASE\_ANON\_KEY=

\# Google OAuth  
GOOGLE\_CLIENT\_ID=  
GOOGLE\_CLIENT\_SECRET=

\# GitHub App  
GITHUB\_APP\_ID=  
GITHUB\_CLIENT\_ID=  
GITHUB\_CLIENT\_SECRET=  
GITHUB\_PRIVATE\_KEY=

\# Redis (Upstash)  
REDIS\_URL=

\# Langfuse  
LANGFUSE\_PUBLIC\_KEY=  
LANGFUSE\_SECRET\_KEY=  
LANGFUSE\_HOST=https://cloud.langfuse.com

\# Sentry  
SENTRY\_DSN=  
VITE\_SENTRY\_DSN=

\# Security  
ENCRYPTION\_KEY=

\# Frontend (Vite prefix)  
VITE\_SUPABASE\_URL=  
VITE\_SUPABASE\_ANON\_KEY=  
VITE\_API\_URL=http://localhost:8000

Validate ALL environment variables at startup. If any are missing, throw a descriptive error and refuse to start. Never start with partial configuration.

---

# **REPOSITORY STRUCTURE (Create this exact structure)**

optilens/  
├── CLAUDE.md                    ← This file  
├── .env.example                 ← All env vars listed, values empty  
├── .env                         ← Local dev values (gitignored)  
├── .gitignore  
├── README.md  
│  
├── frontend/                    ← React \+ Vite app  
│   ├── src/  
│   │   ├── components/          ← Reusable UI components  
│   │   │   ├── ui/              ← shadcn/ui components  
│   │   │   ├── layout/          ← Sidebar, topbar, page wrapper  
│   │   │   ├── audit/           ← Audit-specific components  
│   │   │   ├── charts/          ← Recharts wrappers  
│   │   │   └── heatmap/         ← h337 heatmap component  
│   │   ├── pages/               ← Route-level page components  
│   │   │   ├── Dashboard.tsx  
│   │   │   ├── AuditReport.tsx  
│   │   │   ├── AuditsLibrary.tsx  
│   │   │   ├── Connections.tsx  
│   │   │   ├── Progress.tsx  
│   │   │   └── Settings.tsx  
│   │   ├── hooks/               ← Custom React hooks  
│   │   ├── store/               ← Zustand stores  
│   │   ├── lib/  
│   │   │   ├── supabase.ts      ← Supabase client  
│   │   │   ├── api.ts           ← API client functions  
│   │   │   └── utils.ts         ← Shared utilities  
│   │   ├── types/               ← TypeScript interfaces  
│   │   └── styles/              ← Global CSS, Tailwind config  
│   ├── public/  
│   ├── index.html  
│   ├── vite.config.ts  
│   ├── tailwind.config.ts  
│   └── tsconfig.json  
│  
├── backend/                     ← FastAPI app  
│   ├── app/  
│   │   ├── main.py              ← FastAPI app entry point  
│   │   ├── config.py            ← Settings, env var validation  
│   │   ├── routers/             ← FastAPI route handlers  
│   │   │   ├── audits.py  
│   │   │   ├── issues.py  
│   │   │   ├── reports.py  
│   │   │   ├── integrations.py  
│   │   │   ├── github.py  
│   │   │   ├── track.py         ← rrweb event ingest  
│   │   │   └── workspace.py  
│   │   ├── agents/              ← LangGraph agents  
│   │   │   ├── orchestrator.py  
│   │   │   ├── site\_intelligence.py  
│   │   │   ├── ux\_vision.py  
│   │   │   ├── copy\_content.py  
│   │   │   ├── data\_performance.py  
│   │   │   ├── github\_agent.py  
│   │   │   └── report\_agent.py  
│   │   ├── services/            ← Business logic  
│   │   │   ├── crawler.py       ← Playwright crawler  
│   │   │   ├── ga4.py           ← GA4 API client  
│   │   │   ├── gsc.py           ← GSC API client  
│   │   │   ├── pdf.py           ← WeasyPrint PDF generation  
│   │   │   ├── excel.py         ← openpyxl export  
│   │   │   ├── annotator.py     ← Pillow screenshot annotation  
│   │   │   └── encryption.py   ← AES-256 token encryption  
│   │   ├── models/              ← Pydantic models  
│   │   ├── db/  
│   │   │   ├── supabase.py      ← Supabase client  
│   │   │   └── schema.sql       ← Full SQL schema  
│   │   └── tasks/               ← Celery tasks  
│   │       ├── audit\_tasks.py  
│   │       └── reaudit\_tasks.py  
│   ├── tests/                   ← pytest tests  
│   ├── requirements.txt  
│   ├── Dockerfile  
│   └── celery\_worker.py  
│  
└── docs/                        ← Additional docs  
    ├── api.md  
    └── agents.md

---

# **DATABASE SCHEMA (Create in Supabase before Phase 1\)**

\-- Enable pgvector for re-audit memory  
CREATE EXTENSION IF NOT EXISTS vector;

\-- Organizations (multi-tenant root)  
CREATE TABLE organizations (  
  id          UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
  name        TEXT NOT NULL,  
  plan        TEXT DEFAULT 'solo' CHECK (plan IN ('solo','team','agency')),  
  white\_label\_config JSONB DEFAULT '{}',  
  created\_at  TIMESTAMPTZ DEFAULT NOW()  
);

\-- Users (maps to Supabase auth.users)  
CREATE TABLE users (  
  id      UUID PRIMARY KEY REFERENCES auth.users(id),  
  org\_id  UUID REFERENCES organizations(id) ON DELETE CASCADE,  
  role    TEXT DEFAULT 'owner' CHECK (role IN ('owner','admin','analyst','viewer')),  
  email   TEXT NOT NULL,  
  created\_at TIMESTAMPTZ DEFAULT NOW()  
);

\-- Audits  
CREATE TABLE audits (  
  id                    UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
  org\_id               UUID REFERENCES organizations(id) ON DELETE CASCADE,  
  created\_by           UUID REFERENCES users(id),  
  url                  TEXT NOT NULL,  
  site\_type            TEXT,  
  framework\_applied    TEXT\[\],  
  status               TEXT DEFAULT 'queued' CHECK (status IN ('queued','running','complete','failed')),  
  cro\_score            INTEGER CHECK (cro\_score BETWEEN 0 AND 100),  
  previous\_score       INTEGER,  
  revenue\_leak\_monthly NUMERIC,  
  revenue\_leak\_confidence TEXT CHECK (revenue\_leak\_confidence IN ('High','Medium','Estimated')),  
  pages\_audited        JSONB DEFAULT '\[\]',  
  agent\_outputs        JSONB DEFAULT '{}',  
  audit\_duration\_seconds INTEGER,  
  created\_at           TIMESTAMPTZ DEFAULT NOW(),  
  completed\_at         TIMESTAMPTZ  
);

\-- Issues  
CREATE TABLE issues (  
  id                      UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
  audit\_id               UUID REFERENCES audits(id) ON DELETE CASCADE,  
  org\_id                 UUID REFERENCES organizations(id) ON DELETE CASCADE,  
  agent                  TEXT CHECK (agent IN ('ux','copy','performance','seo','github')),  
  severity               TEXT CHECK (severity IN ('critical','high','medium','low')),  
  category               TEXT,  
  title                  TEXT NOT NULL,  
  description            TEXT,  
  recommendation         TEXT,  
  affected\_element       TEXT,  
  screenshot\_url         TEXT,  
  ice\_score              NUMERIC,  
  impact\_score           INTEGER CHECK (impact\_score BETWEEN 1 AND 10),  
  confidence\_score       INTEGER CHECK (confidence\_score BETWEEN 1 AND 10),  
  effort\_score           INTEGER CHECK (effort\_score BETWEEN 1 AND 10),  
  revenue\_impact\_monthly NUMERIC,  
  ab\_variants            JSONB DEFAULT '\[\]',  
  status                 TEXT DEFAULT 'open' CHECK (status IN ('open','in\_progress','resolved','dismissed')),  
  created\_at             TIMESTAMPTZ DEFAULT NOW()  
);

\-- Reports  
CREATE TABLE reports (  
  id              UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
  audit\_id       UUID REFERENCES audits(id) ON DELETE CASCADE,  
  org\_id         UUID REFERENCES organizations(id) ON DELETE CASCADE,  
  pdf\_url        TEXT,  
  excel\_url      TEXT,  
  screenshots\_zip\_url TEXT,  
  white\_labeled  BOOLEAN DEFAULT FALSE,  
  generated\_at   TIMESTAMPTZ DEFAULT NOW(),  
  expires\_at     TIMESTAMPTZ DEFAULT (NOW() \+ INTERVAL '90 days')  
);

\-- Integrations (OAuth tokens, encrypted)  
CREATE TABLE integrations (  
  id                    UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
  org\_id               UUID REFERENCES organizations(id) ON DELETE CASCADE,  
  type                 TEXT CHECK (type IN ('ga4','gsc','github')),  
  access\_token\_encrypted TEXT,  
  refresh\_token\_encrypted TEXT,  
  scope                TEXT,  
  metadata             JSONB DEFAULT '{}',  
  connected\_at         TIMESTAMPTZ DEFAULT NOW(),  
  last\_used\_at         TIMESTAMPTZ,  
  UNIQUE(org\_id, type)  
);

\-- Pull Requests (GitHub Agent)  
CREATE TABLE pull\_requests (  
  id                    UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
  audit\_id             UUID REFERENCES audits(id) ON DELETE CASCADE,  
  org\_id               UUID REFERENCES organizations(id) ON DELETE CASCADE,  
  github\_pr\_url        TEXT,  
  github\_pr\_number     INTEGER,  
  repo\_name            TEXT,  
  status               TEXT DEFAULT 'draft' CHECK (status IN ('draft','pending\_approval','approved','merged','rejected')),  
  diff\_summary         JSONB DEFAULT '{}',  
  files\_changed        TEXT\[\],  
  projected\_lift\_percent NUMERIC,  
  safety\_checklist     JSONB DEFAULT '\[\]',  
  created\_at           TIMESTAMPTZ DEFAULT NOW(),  
  approved\_at          TIMESTAMPTZ,  
  approved\_by          UUID REFERENCES users(id)  
);

\-- rrweb events (heatmap \+ session data)  
CREATE TABLE events (  
  id          UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
  org\_id      UUID REFERENCES organizations(id) ON DELETE CASCADE,  
  audit\_id    UUID REFERENCES audits(id) ON DELETE SET NULL,  
  page\_url    TEXT NOT NULL,  
  event\_type  TEXT CHECK (event\_type IN ('click','scroll','move')),  
  x           FLOAT,  
  y           FLOAT,  
  viewport\_w  INTEGER,  
  viewport\_h  INTEGER,  
  session\_id  TEXT NOT NULL,  
  created\_at  TIMESTAMPTZ DEFAULT NOW()  
);

\-- Session recordings  
CREATE TABLE session\_recordings (  
  id              UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
  org\_id         UUID REFERENCES organizations(id) ON DELETE CASCADE,  
  page\_url       TEXT NOT NULL,  
  events\_json    JSONB NOT NULL,  
  duration\_seconds INTEGER,  
  session\_id     TEXT NOT NULL,  
  created\_at     TIMESTAMPTZ DEFAULT NOW()  
);

\-- Audit embeddings (pgvector — for re-audit memory)  
CREATE TABLE audit\_embeddings (  
  id          UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
  audit\_id    UUID REFERENCES audits(id) ON DELETE CASCADE,  
  org\_id      UUID REFERENCES organizations(id) ON DELETE CASCADE,  
  content     TEXT NOT NULL,  
  embedding   vector(1536),  
  created\_at  TIMESTAMPTZ DEFAULT NOW()  
);

\-- Row Level Security (RLS) — CRITICAL — org isolation  
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;  
ALTER TABLE users ENABLE ROW LEVEL SECURITY;  
ALTER TABLE audits ENABLE ROW LEVEL SECURITY;  
ALTER TABLE issues ENABLE ROW LEVEL SECURITY;  
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;  
ALTER TABLE integrations ENABLE ROW LEVEL SECURITY;  
ALTER TABLE pull\_requests ENABLE ROW LEVEL SECURITY;  
ALTER TABLE events ENABLE ROW LEVEL SECURITY;  
ALTER TABLE session\_recordings ENABLE ROW LEVEL SECURITY;  
ALTER TABLE audit\_embeddings ENABLE ROW LEVEL SECURITY;

\-- RLS policies (org isolation on every table)  
CREATE POLICY "org\_isolation\_audits" ON audits  
  USING (org\_id IN (  
    SELECT org\_id FROM users WHERE id \= auth.uid()  
  ));  
\-- Apply same pattern to ALL tables above

\-- Indexes for performance  
CREATE INDEX idx\_audits\_org\_id ON audits(org\_id);  
CREATE INDEX idx\_audits\_status ON audits(status);  
CREATE INDEX idx\_issues\_audit\_id ON issues(audit\_id);  
CREATE INDEX idx\_events\_org\_audit ON events(org\_id, audit\_id);  
CREATE INDEX idx\_events\_created ON events(created\_at);  
CREATE INDEX idx\_sessions\_org ON session\_recordings(org\_id);  
CREATE INDEX idx\_embeddings ON audit\_embeddings USING ivfflat (embedding vector\_cosine\_ops);

\-- Auto-purge rrweb data after 30 days (session recordings)  
\-- Run this as a Supabase cron job or Celery beat task daily  
\-- DELETE FROM session\_recordings WHERE created\_at \< NOW() \- INTERVAL '30 days';  
\-- DELETE FROM events WHERE created\_at \< NOW() \- INTERVAL '90 days';

---

# **AGENT ARCHITECTURE (LangGraph — reference for all phases)**

\# Shared state object — passed between all agents  
class AuditState(TypedDict):  
    \# Input  
    audit\_id: str  
    org\_id: str  
    url: str  
    pages: list\[str\]  
    ga4\_connected: bool  
    gsc\_connected: bool  
    github\_connected: bool

    \# Context (set by Site Intelligence agent)  
    site\_type: str       \# ecommerce|saas|landing|corporate|webapp  
    framework: list\[str\] \# \['AIDA', 'Baymard', etc.\]  
    primary\_kpi: str

    \# Raw data  
    screenshots: dict\[str, str\]  \# page\_url \-\> base64 screenshot  
    dom\_content: dict\[str, str\]  \# page\_url \-\> HTML  
    ga4\_data: dict | None  
    gsc\_data: dict | None

    \# Agent outputs  
    ux\_issues: list\[dict\]  
    copy\_issues: list\[dict\]  
    performance\_data: dict  
    seo\_issues: list\[dict\]  
    github\_findings: list\[dict\]

    \# Final  
    cro\_score: int  
    revenue\_leak\_monthly: float  
    revenue\_leak\_confidence: str  \# High|Medium|Estimated  
    issues: list\[dict\]  
    pr\_data: dict | None

\# Graph execution order:  
\# orchestrator\_init  
\#   → site\_intelligence (parallel batch start)  
\#     → ux\_vision, copy\_content, data\_performance (all parallel)  
\#       → github\_agent (sequential, if connected)  
\#         → orchestrator\_synthesis  
\#           → report\_agent

\# Timeout: 45s per agent, 120s total audit  
\# On timeout: mark agent output as partial, continue

---

# **AGENT BEHAVIOR CONTRACTS**

## **Site Intelligence Agent**

Site types: `ecommerce | saas | landing_page | corporate | webapp` Framework mapping:

* ecommerce → Baymard \+ PIE scoring  
* saas → JTBD \+ LIFT model  
* landing\_page → AIDA \+ PAS framework  
* corporate → ResearchXL \+ trust signals  
* webapp → Cognitive load \+ WCAG 2.2

If confidence \< 70%: flag report as "Site type estimated — review recommended" Output context object before other agents start — they all depend on it.

## **UX/Vision Agent**

Input: Playwright screenshots (desktop 1440px \+ mobile 375px) \+ DOM Tools: vision analysis via Claude, axe-core for accessibility Output: issues with severity (critical/high/medium/low), annotated screenshot coordinates, WCAG score, mobile score

## **Copy/Content Agent**

Input: crawled text, CTAs, headlines, meta descriptions, GSC keywords (if connected) Output: persuasion score per section, rewrite suggestions, 2 A/B variants per CTA, readability score (Flesch-Kincaid), emotional trigger map

## **Data/Performance Agent**

Input: Lighthouse CI results, PageSpeed API, GA4 API, GSC API, CWV Output: performance scores, GA4 funnel leak map WITH $ amounts, SEO issues

Revenue leak formula (GA4 connected): leak \= sessions\_at\_step × dropoff\_rate × avg\_order\_value × 0.15

Revenue leak formula (no GA4): Use industry benchmarks by site type ALWAYS label as "Benchmark estimate — connect GA4 for real figures" NEVER present estimate as real data

## **GitHub Agent**

HARD LIMITS (enforce pre-generation, not post):

* NEVER touch: /api/*, /auth/*, /payment/\*, \*.env, \*.sql migration files  
* NEVER delete files  
* NEVER auto-merge — draft PR only, human approval required  
* MAX 200 lines changed per PR  
* ONE PR per audit with batched changes

Output: Draft PR with before/after diff, test plan, rollback steps, projected lift

## **Report Agent (always runs last)**

Input: all agent outputs \+ CRO score from orchestrator Output: dashboard JSON, PDF (WeasyPrint, max 40 pages), Excel (openpyxl), screenshots ZIP (Pillow annotations)

CRO Score calculation: UX & Friction: 25% (Agent 3\) Copy & Persuasion: 20% (Agent 4\) Performance & CWV: 20% (Agent 5\) SEO: 15% (Agent 5\) Conversion Psychology: 10% (Agent 3+4) Accessibility: 10% (Agent 3\)

Score bands: 80–100 Optimized | 60–79 Needs Work | 40–59 High Risk | 0–39 Critical Reproducibility target: same URL \+ same data \= ±3 points across runs

---

# **CRO SCORE COLOR CODING**

80–100 → \#22D3A0 (green) 60–79 → \#F59E0B (amber) 40–59 → \#FF5401 (orange/accent) 0–39 → \#FF4D6A (red/critical)

---

# **API DESIGN (FastAPI — all routes)**

POST   /audits                     Create \+ queue new audit (Celery)  
GET    /audits                     List audits (org-scoped via RLS)  
GET    /audits/{id}                Get audit \+ all agent outputs  
GET    /audits/{id}/status         SSE streaming status updates  
POST   /audits/{id}/rerun          Re-queue same audit  
DELETE /audits/{id}                Delete audit \+ all assets

GET    /audits/{id}/issues         All issues for audit  
PATCH  /issues/{id}                Update status (resolve/dismiss/in\_progress)

GET    /audits/{id}/report         Report URLs (PDF/Excel/ZIP)  
POST   /audits/{id}/report/regen   Regenerate report

GET    /audits/{id}/pr             PR details \+ diff  
POST   /audits/{id}/pr/approve     Approve PR → GitHub API  
POST   /audits/{id}/pr/reject      Reject \+ close PR

POST   /track                      Ingest rrweb events → Supabase  
GET    /heatmap/{audit\_id}         Aggregated heatmap coordinates for h337

GET    /integrations               List connected integrations  
POST   /integrations/ga4/connect   Start GA4 OAuth flow  
POST   /integrations/gsc/connect   Start GSC OAuth flow  
POST   /integrations/github/connect Start GitHub App install  
DELETE /integrations/{type}        Disconnect \+ purge tokens (60s SLA)

GET    /workspace                  Org details \+ plan  
POST   /workspace/members/invite   Invite team member by email  
PATCH  /workspace/members/{id}     Update role

GET    /auth/callback/google       Google OAuth callback  
GET    /auth/callback/github       GitHub App callback

SSE format for /audits/{id}/status:

event: agent\_start  
data: {"agent": "site\_intelligence", "progress": 10}

event: agent\_complete  
data: {"agent": "site\_intelligence", "status": "done", "progress": 25}

event: audit\_complete  
data: {"cro\_score": 67, "issues\_found": 43, "report\_ready": true}

event: audit\_partial  
data: {"agent": "ux\_vision", "reason": "timeout", "progress": 45}

---

# **KILL SWITCHES (via environment variables, no redeploy needed)**

KILL\_GITHUB\_AGENT=false        \# Set to true to disable GitHub agent globally  
KILL\_REVENUE\_FIGURES=false     \# Set to true to show benchmark only  
KILL\_AUDIT\_QUEUE=false         \# Set to true to halt new audits  
KILL\_HEATMAP\_INGEST=false      \# Set to true if Supabase events table is overloaded

Check these at the start of each relevant function. Log the kill switch state.

---

# **PHASE-BY-PHASE BUILD INSTRUCTIONS**

---

## **═══════════════════════════════════════════════════**

## **PHASE 1 — AUDIT CORE (Weeks 1–6)**

## **Target: First end-to-end audit running**

## **═══════════════════════════════════════════════════**

**Goal:** User submits URL → agents run → CRO score → PDF delivered. No integrations, no heatmaps, no GitHub. Just the audit engine.

### **Step 1.1 — Project Scaffold**

Create the full repository structure defined above.  
Install all dependencies.  
Set up Vite \+ React \+ TypeScript with strict mode.  
Set up FastAPI with uvicorn.  
Configure Tailwind \+ shadcn/ui with the Optilens design system.  
Import Space Grotesk, Inter, JetBrains Mono from Google Fonts.  
Apply brand colors as CSS custom properties in globals.css.  
Set up .env.example with all variables listed.  
Validate ALL env vars at FastAPI startup — throw if missing.

### **Step 1.2 — Supabase Setup**

Run the full schema SQL above in Supabase.  
Enable RLS on all tables.  
Create RLS policies for org isolation.  
Set up Supabase client in both frontend and backend.  
Set up Supabase Auth (email \+ Google OAuth).  
Create the Supabase storage buckets:  
  \- reports (PDFs, Excel)  
  \- screenshots (annotated screenshots)  
  \- exports (ZIP files)  
All buckets: private, served via signed URLs only.

### **Step 1.3 — Authentication Flow**

Build signup/login pages using Supabase Auth.  
Email \+ password \+ Google OAuth.  
On first signup:  
  1\. Create organization record  
  2\. Create user record linked to org  
  3\. Assign 'owner' role  
  4\. Redirect to onboarding

Onboarding flow (3 steps, target \< 3 min total):  
  Step 1: Workspace name  
  Step 2: Site type selection (for first audit context)  
  Step 3: Enter URL \+ Run first audit (redirect immediately)

Protect all /dashboard/\* routes with auth middleware.

### **Step 1.4 — Celery \+ Redis Setup**

Configure Celery with Upstash Redis as broker.  
Create audit\_tasks.py with:  
  \- run\_audit(audit\_id: str) → main audit task  
  \- Each agent called as subtask  
  \- State persisted to Supabase after each agent completes  
  \- Retry policy: 3 attempts with 10s backoff  
  \- Timeout: 120 seconds total, 45 seconds per agent

Task state machine:  
  queued → running → complete | failed | partial

On failure: mark audit as failed, store error message,  
notify user by email (Resend), never silently fail.

### **Step 1.5 — Playwright Crawler Service**

Build crawler.py service:  
  Input: url, pages\_to\_crawl (list of URLs)  
  Output: {  
    screenshots: {url: base64\_image},  
    dom\_content: {url: html\_string},  
    page\_metadata: {url: {title, meta\_desc, h1s, links}}  
  }

Desktop viewport: 1440x900  
Mobile viewport: 375x812  
Max DOM extraction: 5,000 nodes (cap at this, add partial flag)  
Timeout per page: 30 seconds  
On screenshot failure: mark as partial, continue with DOM-only

Handle these gracefully (don't crash audit):  
  \- 404 pages  
  \- Redirect chains (follow up to 3 redirects)  
  \- Sites behind auth (audit public pages only, add notice)  
  \- Very slow sites (timeout after 30s)  
  \- JavaScript-heavy SPAs (wait for networkidle)

### **Step 1.6 — LangGraph Agent Pipeline**

Build the full StateGraph with all 7 agent nodes.  
For Phase 1, implement 4 agents (GitHub agent and full report in later phases):

Agent 1 — Orchestrator/Supervisor:  
  \- Initialize AuditState  
  \- Dispatch agents in correct order  
  \- Calculate weighted CRO score from agent outputs  
  \- Generate revenue projections (benchmark only in Phase 1\)  
  \- Synthesize final narrative

Agent 2 — Site Intelligence:  
  \- Detect site type from DOM \+ copy \+ URL structure  
  \- Map to framework (Baymard/JTBD/AIDA/LIFT/ResearchXL)  
  \- Output context object — all other agents wait for this  
  \- Log confidence score — flag if \< 70%

Agent 3 — UX/Vision:  
  \- Analyze screenshots with Claude vision  
  \- Check visual hierarchy, CTA placement, form friction  
  \- WCAG 2.2 violations (use axe-core via Playwright)  
  \- Mobile responsiveness assessment  
  \- Output: issues list with severity \+ annotated callout coordinates

Agent 4 — Copy/Content:  
  \- Analyze page copy, headlines, CTAs  
  \- Score persuasion using detected framework  
  \- Generate 2 A/B variants per critical CTA  
  \- Readability scoring  
  \- Output: copy issues \+ rewrite suggestions

Phase 1 simplified Data/Performance Agent:  
  \- Lighthouse CI (run headless via Playwright)  
  \- PageSpeed Insights API  
  \- Core Web Vitals  
  \- Basic SEO (title, meta, h1, schema check)  
  \- Revenue leak: benchmark only (label as Estimated)

Langfuse tracing: wrap every agent call.  
Track: agent name, tokens in/out, cost, latency, audit\_id.  
Alert via Langfuse if single audit exceeds $0.50.

### **Step 1.7 — Screenshot Annotation (Pillow)**

Build annotator.py:  
  Input: screenshot (base64), issues (list with coordinates)  
  Output: annotated screenshot (base64) with:  
    \- Red/amber/blue boxes around issue areas  
    \- Arrow callouts with issue number  
    \- Severity color coding matching brand colors

Generate annotations for all critical \+ high severity issues.  
Save annotated screenshots to Supabase Storage.  
Return signed URLs valid for 90 days.

### **Step 1.8 — PDF Generation (WeasyPrint)**

Build pdf.py service:  
  Input: audit\_state (all agent outputs), org\_id, white\_label\_config  
  Output: PDF file (max 40 pages)

PDF structure:  
  Cover page: Optilens logo, URL audited, date, CRO score gauge  
  Executive Summary: 3-5 sentences, AI-generated  
  CRO Score Breakdown: weighted bar chart per category  
  Critical Issues (top 5): annotated screenshot \+ recommendation  
  UX & Visual Analysis: full issue list with screenshots  
  Copy & Content Analysis: rewrites \+ A/B variants  
  Performance & SEO: CWV table, Lighthouse scores  
  Revenue Impact: funnel visualization \+ projections  
  Prioritized Backlog: ICE-scored issue list  
  Appendix: methodology, benchmark sources

Apply brand colors (\#1C1C1C, \#F6F6F6, \#FF5401).  
Use Google Fonts: Space Grotesk (headings), Inter (body).  
White-label ready: if white\_label\_config has logo/colors, apply them.  
Upload to Supabase Storage (reports bucket).  
Return signed URL valid for 90 days.

### **Step 1.9 — React Dashboard (Phase 1 — Overview only)**

Build these screens for Phase 1 only:

1\. Home Dashboard:  
   \- CRO Score gauge (animated SVG, 0–100, colored by band)  
   \- Revenue leak card ($ figure, Estimated label)  
   \- Top 3 critical fixes list  
   \- Recent audits grid (thumbnail, score, date, status)  
   \- "Run New Audit" CTA (prominent, accent color)

2\. New Audit Modal:  
   \- URL input (validate it's a real URL)  
   \- Page selection (auto-suggest from URL structure)  
   \- "Start Audit" button  
   \- Redirect to audit status view immediately

3\. Audit Status View (real-time):  
   \- Progress bar (driven by SSE from /audits/{id}/status)  
   \- Live agent status: "Site Intelligence ✓ → UX Analysis running..."  
   \- Animated spinner while running  
   \- Auto-redirect to report when complete

4\. Audit Report — Overview Tab only (Phase 1):  
   \- CRO score gauge (large, animated)  
   \- Score delta badge (vs previous audit if exists)  
   \- Revenue leak card with confidence level  
   \- Executive summary paragraph  
   \- Top 5 issues list (severity badge, title, revenue impact)  
   \- Download PDF button (signed URL from Supabase)  
   \- Tab bar (show all 6 tabs but mark Phase 2+ as "Coming Soon")

5\. Audits Library:  
   \- Table with: URL, site type, score, issues count, date, status  
   \- Filter by status  
   \- Re-run button per audit

Design requirements:  
   \- Light background (\#F6F6F6)  
   \- White cards with subtle shadow  
   \- Accent color (\#FF5401) for CTAs only  
   \- Space Grotesk headings, Inter body  
   \- Fully responsive (mobile \+ desktop)  
   \- Loading skeletons for all data-dependent UI  
   \- Empty states with clear CTAs

### **Phase 1 Completion Checklist**

□ Repository structure matches spec exactly  
□ .env.example has all variables  
□ Supabase schema applied with RLS policies  
□ Auth flow works (signup → onboarding → dashboard)  
□ URL submission queues Celery task  
□ All 4 agents (Site Intelligence, UX, Copy, Data) run end-to-end  
□ CRO score calculated correctly  
□ PDF generated and accessible via signed URL  
□ Annotated screenshots generated for critical/high issues  
□ Real-time SSE status updates work in dashboard  
□ Audit report Overview tab shows real data  
□ Langfuse shows agent traces  
□ Sentry captures errors in both frontend and backend  
□ No hardcoded secrets anywhere in codebase  
□ All env vars validated at startup  
□ First end-to-end audit completes in \< 2 minutes

---

## **═══════════════════════════════════════════════════**

## **PHASE 2 — DATA LAYER (Weeks 7–10)**

## **Target: Real $ revenue numbers from GA4**

## **═══════════════════════════════════════════════════**

**Goal:** Connect GA4 \+ GSC → real revenue leak calculations → all 6 dashboard tabs working.

### **Step 2.1 — GA4 OAuth Integration**

Build Google OAuth flow (Google Cloud Console app already created):  
  1\. /integrations/ga4/connect → redirect to Google OAuth  
  2\. Google OAuth → /auth/callback/google (with code)  
  3\. Exchange code for access\_token \+ refresh\_token  
  4\. Encrypt BOTH tokens with AES-256 (ENCRYPTION\_KEY env var)  
  5\. Store encrypted in integrations table  
  6\. Return to dashboard with success toast

Scopes required: analytics.readonly ONLY  
Never request write access.

GA4 data pulled on each audit (never cached \> 24h):  
  \- Sessions by page (last 30 days, configurable 7/30/90)  
  \- Conversion funnel: each step \+ drop-off %  
  \- Revenue per session (if e-commerce tracking enabled)  
  \- Device breakdown (desktop/mobile/tablet)  
  \- Traffic sources  
  \- Bounce rate, engagement rate

Disconnect flow:  
  1\. DELETE /integrations/ga4  
  2\. Cryptographically wipe tokens from DB (not soft-delete)  
  3\. Set KV flag: ga4\_connected \= false for org  
  4\. Confirm in \< 60 seconds

### **Step 2.2 — Revenue Leak Engine**

Build revenue\_calculator.py:

IF ga4\_data available (real calculation):  
  For each funnel step:  
    sessions\_at\_step \= ga4.sessions\[step\]  
    dropoff\_rate \= 1 \- ga4.conversion\_rate\[step\]  
    avg\_order\_value \= ga4.revenue / ga4.transactions (if available)  
                   OR industry benchmark for site type (labeled)  
    monthly\_leak \= sessions\_at\_step × dropoff\_rate × avg\_order\_value × 0.15

IF ga4\_data not available (benchmark):  
  Use industry benchmarks by site\_type:  
    ecommerce: avg cart abandonment 70%, avg AOV $85  
    saas: avg trial-to-paid 4%, avg MRR $120/customer  
    landing\_page: avg conversion 2.5%  
    corporate: avg lead rate 1.8%  
  ALWAYS label: "Benchmark estimate — connect GA4 for real figures"  
  ALWAYS set revenue\_leak\_confidence \= 'Estimated'

Every $ figure MUST have:  
  \- calculation\_basis: 'ga4\_real' | 'benchmark\_estimate'  
  \- confidence: 'High' | 'Medium' | 'Estimated'  
  \- assumptions: dict of values used

NEVER show unlabeled revenue figures. This is a hard constraint.  
If you cannot determine the label, do not show the figure.

### **Step 2.3 — GSC Integration**

Same OAuth pattern as GA4.  
Scope: webmasters.readonly ONLY.

GSC data used by:  
  \- Copy Agent: keyword alignment (are CTAs using high-volume queries?)  
  \- Data Agent: indexing issues, page coverage, click-through rates

Data pulled:  
  \- Top 50 queries by impressions (last 28 days)  
  \- Page indexing status  
  \- Mobile usability issues  
  \- Core Web Vitals from GSC (compare with Lighthouse)

### **Step 2.4 — Complete All 6 Dashboard Tabs**

Complete the Audit Report tabbed interface:

Tab 1 — Overview (extend Phase 1):  
  \- Add real GA4 revenue figures (replace benchmark)  
  \- Add integration status badges

Tab 2 — UX & Visuals:  
  \- Annotated screenshot viewer (desktop/mobile toggle)  
  \- Issue list filtered to UX/visual category  
  \- WCAG violation table  
  \- Note: Heatmap toggle shows "Coming in Phase 3"

Tab 3 — Copy & Content:  
  \- Page-by-page copy scores  
  \- Headline \+ CTA rewrite suggestions (expandable)  
  \- A/B variant previews (current vs suggested, side by side)  
  \- Persuasion framework compliance bar  
  \- Emotional trigger map (what's present / what's missing)  
  \- GSC keyword alignment (if connected)

Tab 4 — Performance & SEO:  
  \- Lighthouse score cards (4 metrics, colored by score)  
  \- CWV table: LCP / INP / CLS with pass/fail  
  \- Speed-to-revenue impact calculation  
  \- SEO issues list (sorted by impact)  
  \- GSC data panel (if connected): top queries, CTR gaps

Tab 5 — GitHub (placeholder — Phase 4):  
  \- Show "Connect GitHub to unlock code fixes"  
  \- CTA to Connections page

Tab 6 — Revenue Impact:  
  \- GA4 funnel visualization (Recharts Sankey or step chart)  
  \- Revenue leak per step (with confidence labels)  
  \- ROI calculator (editable inputs: AOV, traffic, effort)  
  \- Monthly vs annual projection toggle  
  \- "Connect GA4 for real figures" CTA if not connected

### **Step 2.5 — Excel Export (openpyxl)**

Build excel.py:  
  Sheet 1: Issue Backlog  
    Columns: severity, category, title, recommendation,  
             ice\_score, impact, confidence, effort, revenue\_impact\_monthly, status  
    Sorted by: ice\_score descending

  Sheet 2: CWV \+ Performance  
    Lighthouse scores, CWV metrics, raw numbers

  Sheet 3: GA4 Funnel Data  
    Step name, sessions, drop-off rate, drop-off count, revenue leak $

  Sheet 4: ROI Calculator  
    Editable yellow cells: AOV, monthly sessions, avg effort (days)  
    Calculated cells: projected lift, monthly revenue gain, annual gain  
    Formula-based (not hardcoded)

Apply Optilens brand colors to headers (\#1C1C1C background, white text).  
Upload to Supabase Storage. Return signed URL.

### **Phase 2 Completion Checklist**

□ GA4 OAuth connects and disconnects cleanly  
□ GSC OAuth connects and disconnects cleanly  
□ Tokens encrypted at rest (verify with db query — should be unreadable)  
□ Revenue figures show "GA4-powered" when connected  
□ Revenue figures show "Benchmark estimate" when not connected — always labeled  
□ All 6 dashboard tabs have real data  
□ Excel export works with all 4 sheets  
□ Funnel visualization renders in Revenue Impact tab  
□ GSC data appears in Copy \+ Performance tabs when connected  
□ Disconnect purges tokens within 60 seconds  
□ Integration status badges update in real time

---

## **═══════════════════════════════════════════════════**

## **PHASE 3 — VISUAL LAYER (Weeks 11–14)**

## **Target: Real heatmaps \+ session replay**

## **═══════════════════════════════════════════════════**

**Goal:** rrweb snippet → Supabase events → h337 heatmap rendering.

### **Step 3.1 — rrweb Tracking Snippet**

Build the /track endpoint (POST):  
  Input: rrweb event batch (click, scroll, move events)  
  Processing:  
    1\. Extract org\_id from API key in Authorization header  
    2\. Hash visitor IP (SHA-256) — never store raw IP  
    3\. Parse x, y coordinates, viewport dimensions, event type  
    4\. Validate session\_id is present  
    5\. Insert to events table in Supabase  
    6\. For session replay events: append to session\_recordings table  
  Rate limit: 1000 requests/minute per org

Generate the rrweb snippet code for users to copy:  
\`\`\`javascript  
(function(o){  
  var s=document.createElement('script');  
  s.src='https://cdn.jsdelivr.net/npm/rrweb@latest/dist/rrweb.min.js';  
  s.onload=function(){  
    rrweb.record({  
      emit:function(e){  
        fetch('https://app.optilens.ai/track',{  
          method:'POST',  
          headers:{'Content-Type':'application/json','Authorization':'Bearer '+o},  
          body:JSON.stringify({events:\[e\],session\_id:window.\_olSid})  
        })  
      },  
      maskAllInputs:true,      // MANDATORY privacy protection  
      maskInputOptions:{password:true,email:true,tel:true}  
    });  
  };  
  window.\_olSid=Math.random().toString(36).slice(2);  
  document.head.appendChild(s);  
})('ORG\_API\_KEY\_HERE');

This snippet auto-generates with org's API key in Connections page.

\#\#\# Step 3.2 — Heatmap Rendering (h337)

Build HeatmapViewer React component:

Props:

* screenshotUrl: string (base64 or signed URL)  
* auditId: string  
* pageUrl: string  
* mode: 'simulated' | 'real'

Simulated mode (no snippet needed):

* Use GA4 scroll depth data to generate synthetic coordinates  
* Generate click probability map from above-fold \+ CTA positions  
* Render via h337 on screenshot canvas  
* Show label: "GA4-simulated — install snippet for real click data"

Real mode (snippet installed):

* Fetch aggregated coordinates from GET /heatmap/{audit\_id}  
* Filter by pageUrl  
* Feed coordinate array to h337.create()  
* Render overlay on screenshot image  
* Show label: "Live data — last 30 days"

h337 config: container: screenshot div element radius: 35 maxOpacity: 0.8 minOpacity: 0 blur: 0.85

Toggle switch between desktop/mobile views. Toggle between click heatmap / scroll heatmap / movement heatmap.

\#\#\# Step 3.3 — Session Replay Player

Build SessionReplayPlayer React component using rrweb-player.

Show in UX & Visuals tab:

* Session list: date, duration, pages visited, device type  
* Click to play: rrweb-player renders full replay  
* Timeline scrubber  
* Speed control: 0.5x, 1x, 2x, 4x

Data limits:

* Cap at 1,000 sessions per org per month  
* Sessions auto-purged after 30 days (Celery beat task)  
* Show usage indicator: "483 / 1,000 sessions this month"

Privacy:

* Form inputs masked (rrweb maskAllInputs: true)  
* Confirm masking is working with test recording before showing to users

\#\#\# Step 3.4 — UX Tab Enhancement

Complete the UX & Visuals tab with:

* Screenshot viewer: desktop/mobile toggle  
* Heatmap overlay toggle (off by default, click to enable)  
* Heatmap type selector: click | scroll | movement  
* Session replay section (if snippet installed)  
* Real issue annotations on screenshots (arrows \+ callouts)  
* WCAG violation details with ARIA fix suggestions  
* Friction score gauge per page section

\#\#\# Step 3.5 — Annotated Screenshots ZIP Export

Extend annotator.py:

* Generate annotated screenshot for every critical \+ high issue  
* Arrow callout pointing to specific element  
* Issue number badge (matches backlog numbering)  
* Severity color border (red for critical, orange for high)  
* Caption text below each screenshot: "Issue \#3 — CTA below fold (−$2,100/mo)"

Package all annotated screenshots as ZIP. Upload to Supabase Storage. Add ZIP download button to report Overview tab.

\#\#\# Phase 3 Completion Checklist

□ rrweb snippet generates correctly with org API key □ /track endpoint receives and stores events (verify in Supabase) □ IP addresses are hashed — verify raw IPs not stored □ h337 heatmap renders on screenshot in UX tab □ Simulated heatmap shows GA4-simulated label □ Real heatmap shows when events exist □ Session replay player works (test with your own device) □ 30-day auto-purge task runs via Celery beat □ Session count shows usage \+ cap □ Annotated screenshots ZIP downloads correctly □ Form inputs confirmed masked in session replay

\---

\#\# ═══════════════════════════════════════════════════  
\#\# PHASE 4 — GITHUB AGENT (Weeks 15–18)  
\#\# Target: Code review → PR generation → human approval  
\#\# ═══════════════════════════════════════════════════

\*\*Goal:\*\* Connect GitHub repo → AI reviews code → creates draft PR → user approves.

\#\#\# Step 4.1 — GitHub App OAuth

GitHub App already registered (in progress at build start). Required scopes: contents:read, pull\_requests:write, metadata:read, checks:read

Build GitHub OAuth flow:

1. /integrations/github/connect → GitHub App install page  
2. User installs app on their repo  
3. GitHub → /auth/callback/github (with installation\_id \+ code)  
4. Exchange for installation access token  
5. Encrypt token \+ store installation\_id in integrations table  
6. Display connected repo name in Connections page

Build /webhooks/github endpoint:

* Verify webhook signature (X-Hub-Signature-256)  
* Handle PR events: opened, closed, merged  
* Update pull\_requests table status on merge/close

\#\#\# Step 4.2 — GitHub Code Review Agent

Build github\_agent.py (Agent 6):

Input: audit findings from Agents 3–5, site\_type, GitHub installation token

Step 1 — Discover relevant files:

* List repo files via GitHub API  
* Filter to frontend files only: .html, .css, .js, .jsx, .tsx, .vue, .svelte  
* Exclude HARD LIMITS: api/, auth/, payment/, \*.env, migrations/  
* Never include server-side or database files

Step 2 — Map findings to code:

* For each UX/copy/performance issue, find the relevant file  
* E.g., "CTA below fold" → find the component containing that CTA  
* E.g., "LCP image not optimized" → find the img tag or Image component

Step 3 — Generate code changes:

* For each mapped issue, generate before/after code diff  
* Changes must be minimal, targeted, surgical  
* Include inline comments explaining why the change improves conversion  
* NEVER change logic, only: CSS, copy text, HTML structure, meta tags, image attributes

Step 4 — Create PR via GitHub API: PR title: "\[Optilens\] CRO improvements — {score\_delta} projected lift" PR body template: \#\# Optilens CRO Audit — Code Improvements **Audit score:** {current\_score}/100 → **Projected:** {projected\_score}/100 **Projected monthly revenue lift:** ${projected\_lift}

\#\#\# Changes included:  
{list of issues addressed with ICE score}

\#\#\# Safety checklist:  
\- \[ \] Reviewed all changes manually  
\- \[ \] Tested in staging environment  
\- \[ \] Confirmed no functional regressions  
\- \[ \] Checked mobile rendering

\#\#\# Rollback:  
Revert this PR to undo all changes atomically.

\---  
\*Generated by Optilens — review all changes before merging\*

Status: DRAFT — never ready-for-review automatically

Hard limit enforcement (check BEFORE generating, not after): forbidden\_paths \= \['/api/', '/auth/', '/payment/', '.env', 'migrations', 'schema'\] if any file\_path starts with forbidden → skip that file entirely max\_lines\_changed \= 200 → if exceeds, split to highest ICE score items only

\#\#\# Step 4.3 — GitHub Tab in Dashboard

Build GitHub tab in Audit Report:

Layout:

* Connected repo name \+ branch  
* PR status badge (Draft / Pending Approval / Approved / Merged / Rejected)  
* Projected conversion lift estimate

Code Issues section:

* List of code-level findings (mapped to specific files)  
* File path \+ line number for each issue  
* Severity badge

PR Diff Viewer:

* Syntax-highlighted before/after diff (react-diff-viewer or similar)  
* File tree showing changed files  
* Line-by-line diff with context

Safety Checklist (user must check each before approving):

* \[ \] I have reviewed all changes in this PR  
* \[ \] I have tested this in a non-production environment  
* \[ \] I confirm no security-sensitive files are modified  
* \[ \] I accept responsibility for merging this code

Approve PR button:

* Only active when all checklist items checked  
* Confirmation modal: "This will mark PR \#42 as ready for review on GitHub. Your team can then merge it. Optilens does not auto-merge."  
* On confirm: call /audits/{id}/pr/approve → GitHub API sets PR to ready  
* Success: PR status badge updates to "Pending Merge"

Reject PR button:

* Confirmation: "This will close PR \#42 on GitHub."  
* On confirm: call /audits/{id}/pr/reject → GitHub API closes PR

\#\#\# Step 4.4 — Fix Verification

Build fix\_verifier.py: After a PR is merged (webhook: pull\_request.closed \+ merged=true):

1. Re-crawl the specific pages affected by the PR  
2. Re-run only the agents relevant to the changed issues  
3. Compare scores: before vs after  
4. Update issue statuses to 'resolved' if scores improved  
5. Send email: "PR merged\! Your CRO score improved from 67 → 74."  
6. Update progress tracking dashboard with verified lift

\#\#\# Phase 4 Completion Checklist

□ GitHub App OAuth connects and disconnects cleanly □ Connected repo name shows in Connections page □ GitHub Agent runs after parallel agents complete □ PR created as DRAFT (never auto-ready) □ Forbidden paths verified: test that /api files are NEVER touched □ PR max 200 lines — test with a site that has many issues □ Diff viewer renders correctly in GitHub tab □ Safety checklist must be fully checked before Approve button activates □ Approve → PR status changes on GitHub (verify in GitHub) □ Reject → PR closed on GitHub (verify in GitHub) □ Fix verification runs after merge (check Celery logs) □ Webhook endpoint validates signature (test with invalid signature → 401\)

\---

\#\# ═══════════════════════════════════════════════════  
\#\# PHASE 5 — RETENTION LAYER (Weeks 19–22)  
\#\# Target: Monthly re-audits \+ progress tracking \+ notifications  
\#\# ═══════════════════════════════════════════════════

\*\*Goal:\*\* Keep users coming back. Prove value over time.

\#\#\# Step 5.1 — Monthly Re-Audit Engine

Build Celery beat task: reaudit\_tasks.py

Schedule: Run daily at 03:00 UTC Logic:

* Query audits table: WHERE status='complete' AND reaudit\_enabled=true AND last\_reaudit\_at \< NOW() \- INTERVAL '30 days'  
* For each: create new audit job with same settings  
* Use pgvector to retrieve previous audit embeddings as context (so agents can compare: "last month LCP was 4.2s, now 3.8s")  
* After completion: calculate score delta, send email notification

Email on re-audit complete (send via Resend): Subject: "Your Optilens re-audit is ready — score changed from 61 → 74" Body: score comparison, top new issues, improvements made

If score drops \> 10 points: Subject: "⚠️ CRO score dropped on \[domain\] — review needed" Trigger Slack webhook if configured

User controls in Settings:

* Enable/disable re-audits  
* Frequency: monthly | quarterly | manual only

\#\#\# Step 5.2 — Progress Tracking Dashboard

Build Progress page at /dashboard/progress:

Charts (all using Recharts):

1. CRO Score Over Time (LineChart)

   * One data point per completed audit  
   * Color line by score band (green/amber/orange/red)  
   * Hover: show audit date \+ score \+ delta  
2. Revenue Leak Over Time (AreaChart)

   * Monthly leak estimate trending down (hopefully)  
   * "GA4-powered" or "Estimated" label  
3. Issues Resolved vs Opened (BarChart grouped)

   * Per month: resolved (green), opened (red), dismissed (grey)  
4. Category Score History (LineChart with 6 lines)

   * One line per CRO score category  
   * Toggle lines on/off

Wins Feed:

* Timeline of resolved issues  
* Format: "✓ Fixed: CTA below fold | Score \+8 | −$1,200/mo saved | March 2026"  
* Sorted: most recent first

\#\#\# Step 5.3 — Email \+ Slack Notifications

Build notification\_service.py:

Email (via Resend API): Triggers: \- Audit complete \- Re-audit complete (with score delta) \- Score drops \> 10 points (urgent) \- PR merged \+ fix verified \- Team member invited

Template design: \- Minimal, brand-consistent (\#1C1C1C text, \#FF5401 CTAs) \- Mobile-responsive \- Clear CTA button to view report \- Unsubscribe link in every email

Slack webhook (optional, user configures in Settings):

* POST to user's Slack webhook URL  
* Format: Slack Block Kit message  
* Triggers: audit complete, score drop \> 10 points, PR merged  
* Test webhook button in Settings

\#\#\# Step 5.4 — A/B Hypothesis Generator

Build ab\_generator.py:

For every High or Critical issue, generate: { test\_name: "CTA copy — benefit-led vs action-led", control: "Sign Up Free", variant: "Get Your Free CRO Audit", primary\_metric: "Trial signup rate", estimated\_traffic\_needed: 2400, estimated\_duration\_days: 14, statistical\_power: 0.8, suggested\_tool: "VWO | Google Optimize | Optimizely" }

Show in Copy & Content tab under each copy issue. Export all hypotheses as CSV from issue backlog.

\#\#\# Step 5.5 — Audit History Diff View

Add diff view to Audit Report:

* "Compare with previous audit" toggle  
* Side-by-side: current vs previous score per category  
* Color-coded: improved (green), declined (red), same (grey)  
* "New issues" vs "Resolved since last audit" sections  
* Net change in revenue leak

\#\#\# Phase 5 Completion Checklist

□ Monthly re-audit Celery beat task runs on schedule □ pgvector embeddings created for each completed audit □ Previous audit context passed to agents on re-audit □ Email sent on audit completion (check inbox) □ Email sent on re-audit with score delta □ Slack webhook sends correctly (test with RequestBin) □ Progress tracking page shows real historical data □ All 4 charts render with correct data □ Wins feed shows resolved issues chronologically □ A/B hypotheses generated for high/critical issues □ Audit history diff view shows correct comparisons □ Settings page: re-audit frequency control works

\---

\#\# ═══════════════════════════════════════════════════  
\#\# PHASE 6 — AGENCY & PLATFORM (Weeks 23–26)  
\#\# Target: White-label \+ billing \+ agency workspaces  
\#\# ═══════════════════════════════════════════════════

\*\*Goal:\*\* Agency-ready platform with billing and multi-client workspaces.

\#\#\# Step 6.1 — White-Label PDF Mode

Extend pdf.py with white\_label\_config support: { logo\_url: string, // Agency logo (Supabase Storage URL) brand\_color: string, // Agency primary color hex company\_name: string, // Agency name remove\_optilens\_branding: boolean }

If remove\_optilens\_branding \= true:

* Remove "Powered by Optilens" from all pages  
* Replace with agency company\_name  
* Apply agency logo to cover page  
* Apply agency brand\_color to headers, CTAs, score gauges

If false: show "Powered by Optilens" in footer.

White-label settings in Settings page (Agency plan only):

* Logo upload (PNG/SVG, max 500KB)  
* Brand color picker  
* Preview PDF button  
* Shareable report domain (custom CNAME — Phase 6 stretch goal)

\#\#\# Step 6.2 — Team Workspace \+ Roles (Supabase RLS)

Roles: owner | admin | analyst | viewer

RLS policies per role: owner: Full access to all org data admin: All features except billing and org deletion analyst: Run audits, view reports, export — no team management viewer: Read-only — view reports only, no run/export

Build team management UI in Settings:

* Members list with role badges  
* Invite by email (send invite email via Resend)  
* Change role dropdown (owner/admin only)  
* Remove member button (owner/admin only)  
* Pending invites list

Invite flow:

1. Owner/admin enters email \+ selects role  
2. Optilens sends invite email with magic link  
3. Recipient clicks link → creates account → auto-joins org  
4. Joins with specified role

\#\#\# Step 6.3 — Agency Client Workspaces

Agency plan: one master agency workspace \+ unlimited client workspaces.

Data model:

* Add parent\_org\_id to organizations table  
* Client workspaces: parent\_org\_id \= agency org id

Agency workspace UI:

* "Clients" section in sidebar (Agency plan only)  
* Create client workspace: name, URL, plan context  
* Switch between client workspaces  
* Run audit for client → stored in their workspace  
* Download PDF with client branding

Client workspace isolation:

* Full RLS isolation (clients cannot see other clients)  
* Agency can access all their client workspaces  
* Clients cannot access agency workspace (unless invited)

\#\#\# Step 6.4 — Billing (LemonSqueezy \+ Xflow)

LemonSqueezy integration:

* Create products: Solo ($99/mo), Team ($299/mo), Agency ($699/mo)  
* Create variants: monthly and annual (20% discount)  
* Webhook endpoint: /billing/webhook (verify signature)  
* Handle events: subscription\_created, subscription\_updated, subscription\_cancelled, payment\_failed

Plan enforcement: Solo: 5 audits/mo — enforce in audit queue Team: 20 audits/mo — enforce in audit queue Agency: Unlimited

Add-ons: Extra audits: $15 each (LemonSqueezy one-time purchase) Extra GA4 properties: $29/mo (LemonSqueezy subscription add-on)

Billing UI in Settings:

* Current plan \+ usage (X/Y audits used)  
* Upgrade/downgrade button (→ LemonSqueezy hosted checkout)  
* Billing history  
* Cancel subscription

Usage tracking:

* audit\_count per org per billing period in organizations table  
* Block new audits when limit reached (show upgrade prompt)  
* Never silently drop queued audits

Xflow setup (cross-border settlement):

* This is Riverra Labs LLP's own account for receiving payments  
* Not customer-facing — set up separately via xflowpay.com  
* LemonSqueezy handles customer checkout, Xflow handles INR settlement

\#\#\# Step 6.5 — Railway → Hetzner Migration (when bill \> $200/mo)

When Railway monthly bill exceeds $200:

1. Create Hetzner CX53 (8 vCPU, 32GB RAM, 240GB NVMe, Germany DC)

2. Server setup (run these commands): apt update && apt upgrade \-y apt install \-y docker.io docker-compose nginx certbot python3-certbot-nginx systemctl enable docker

3. Create docker-compose.yml with services:

   * fastapi (uvicorn)  
   * celery-worker  
   * celery-beat  
   * redis (local, or keep Upstash)  
   * langfuse (docker image)  
   * playwright (chromium)  
4. Nginx config for app.optilens.ai → port 8000

5. SSL: certbot \--nginx \-d app.optilens.ai

6. GitHub Actions deploy workflow:

   * On push to main: SSH to Hetzner, git pull, docker-compose up \-d  
7. DNS: update Cloudflare A record for api.optilens.ai

8. Railway: keep running until Hetzner is confirmed stable (7 days) Then cancel Railway.

\#\#\# Phase 6 Completion Checklist

□ White-label PDF generates with agency logo \+ colors □ Optilens branding removed when remove\_optilens\_branding \= true □ Team invite flow works end-to-end (invite → email → join → role) □ RLS prevents viewer from running audits (test in Supabase) □ Client workspaces isolated from each other (test cross-access) □ Agency can switch between client workspaces □ LemonSqueezy checkout works for Solo plan (test transaction) □ Plan limits enforced: 5 audits for Solo, blocked on 6th □ Upgrade prompt shown when limit reached □ Billing history shows in Settings □ Webhook handles subscription\_cancelled correctly □ Annual discount applied (20% off)

\---

\# TESTING REQUIREMENTS (All phases)

Backend (pytest):

* Unit tests for every service function  
* Integration tests for all API endpoints  
* Test revenue calculation with GA4 data (assert labels always present)  
* Test GitHub Agent forbidden paths (assert /api/ files never modified)  
* Test RLS: user from org A cannot access org B data

Frontend (Vitest \+ React Testing Library):

* Component tests for all dashboard components  
* Test loading states and empty states  
* Test error states

End-to-end (Playwright):

* Full audit flow: signup → submit URL → audit complete → view report  
* GA4 connect → disconnect → verify tokens purged  
* GitHub PR: connect → approve → verify status change  
* Test on both desktop and mobile viewports

Run tests before each phase completion. Target: no phase ships with failing tests.

\---

\# SECURITY CHECKLIST (Verify before each phase ships)

□ No API keys or secrets in codebase (search: grep \-r "sk-ant" . ) □ All env vars validated at startup □ OAuth tokens encrypted in DB (verify: SELECT access\_token FROM integrations — should be unreadable) □ RLS policies active (verify in Supabase: test as different org user) □ Rate limiting on audit endpoint (10/hr per org) □ GitHub webhook signature verified □ Supabase Storage buckets are private (signed URLs only) □ Sentry PII scrubbing enabled □ HTTPS enforced everywhere □ CORS configured correctly (only allow app.optilens.ai)

\---

\# COMMON FAILURE MODES — HANDLE THESE EXPLICITLY

1. GA4 API returns 0 sessions for a page → Do not divide by zero in revenue calc → Show "Insufficient data — minimum 100 sessions required"

2. Playwright timeout on JavaScript-heavy SPA → Wait for networkidle event, max 30s → If timeout: mark screenshots as partial, continue with DOM

3. Claude API rate limit / 529 error → Exponential backoff: 1s, 2s, 4s, 8s → After 3 retries: mark agent as partial, continue audit

4. Supabase RLS policy error (user accesses wrong org) → Return 403, log to Sentry with org\_id context → Never expose other org's data

5. rrweb snippet sends malformed events → Validate event schema before insert → Drop malformed events, log count to Sentry

6. GitHub PR creation fails (branch conflict) → Mark PR as failed, show error in GitHub tab → Suggest user pulls latest main branch

7. PDF generation OOM (very large audit) → Set WeasyPrint memory limit → If fails: generate simplified PDF (text only, no images)

8. Celery worker dies mid-audit → All agent outputs persisted after each agent completes → On retry: skip completed agents, continue from last checkpoint

9. User submits same URL twice within 1 hour → Show warning with timestamp of recent audit → Allow override with confirmation

10. All agents timeout simultaneously (server overload) → KILL\_AUDIT\_QUEUE=true (env var kill switch) → Email affected users → Do not silently drop queued jobs

\---

\# DEPLOY COMMANDS (Reference)

\`\`\`bash  
\# Vercel (frontend) — automatic on push to main

\# Railway (backend) — automatic on push to main via GitHub integration

\# Celery worker (Railway separate service)  
celery \-A backend.celery\_worker worker \--loglevel=info \--concurrency=4

\# Celery beat (Railway separate service)  
celery \-A backend.celery\_worker beat \--loglevel=info

\# Local development  
cd frontend && npm run dev          \# React on :5173  
cd backend && uvicorn app.main:app \--reload  \# FastAPI on :8000  
cd backend && celery \-A celery\_worker worker  \# Celery worker

---

# **START OF EACH PHASE — PROMPT PREFIX**

When starting a new phase in Claude Code, prepend this to your request:

We are building Optilens — the AI CRO platform for Riverra Labs LLP.  
Full context is in CLAUDE.md at the project root.  
Current phase: \[PHASE NUMBER\] — \[PHASE NAME\]  
Brand colors: \#1C1C1C (primary), \#F6F6F6 (background), \#FF5401 (accent)  
Stack: React+Vite (TypeScript) / FastAPI / LangGraph / Claude claude-sonnet-4-5 / Supabase / Railway

Task: \[SPECIFIC TASK FROM PHASE\]

Rules:  
\- Never write placeholder code  
\- Always handle errors  
\- Always use environment variables for secrets  
\- Brand colors and fonts as specified in CLAUDE.md  
\- Production-ready code only

---

# **END OF CLAUDE.md**

# **Riverra Labs LLP — Optilens — optilens.ai**

# **March 2026 — Version 1.0**

Done. Here's the cleaned-up final version:  
---

**Starter — $99/mo** ($79/mo annual)

* 1 site, 5 audits/mo  
* All 7 AI agents, CRO score, prioritized fixes  
* GA4 \+ GSC integration  
* Heatmaps \+ session replay (500 sessions/mo)  
* Branded PDF \+ Excel report  
* Email support (48hr)  
* ❌ GitHub Agent, ❌ White-label

---

**Growth — $299/mo** ($249/mo annual)

* 3 sites, 20 audits/mo  
* Everything in Starter, plus:  
* ✅ GitHub Agent  
* Session replay (2,000 sessions/mo)  
* Progress tracking \+ monthly re-audits  
* Priority email support (24hr)  
* ❌ White-label

---

**Agency — $699/mo** ($579/mo annual)

* 10 sites, 75 audits/mo  
* Everything in Growth, plus:  
* ✅ Full white-label  
* ✅ Client workspaces \+ shareable report links  
* Session replay (10,000 sessions/mo)  
* SLA (99.5% uptime)

---

**Enterprise — Custom** (from $2,000/mo)

**Add-ons:** Extra audits $15 (Starter/Growth) / $12 (Agency) · Extra sites $49/site/mo · Extra GA4 properties $29/mo

	

\# robots.txt check — runs BEFORE any page crawl  
def check\_robots\_permission(url: str) \-\> dict:  
    parsed \= urlparse(url)  
    base \= f"{parsed.scheme}://{parsed.netloc}"  
    rp \= RobotFileParser()  
    rp.set\_url(f"{base}/robots.txt")  
    try:  
        rp.read()  
        return {  
            "allowed": rp.can\_fetch("Optilensbot/1.0", url),  
            "crawl\_delay": rp.crawl\_delay("Optilensbot/1.0") or 1  
        }  
    except:  
        return {"allowed": True, "crawl\_delay": 1}  
\`\`\`

\*\*Audit submission flow update:\*\*  
\- Check robots.txt on URL submit  
\- If blocked → show: \*"This site restricts automated access. Do you own this site or have permission to audit it?"\*  
\- Checkbox: \`\[ \] I own this site or have explicit permission to audit it\`  
\- If checked → proceed with audit, log \`owner\_override: true\` in audit record  
\- If not checked → block audit, explain why

\*\*New page to build:\*\* \`optilens.ai/bot\` explaining Optilensbot and how to allow it:  
\`\`\`  
User-agent: Optilensbot  
Allow: /  
\`\`\`

\*\*Phase 2 addition — Ownership Verification:\*\*  
\- User adds \`\<meta name="optilens-site-verification" content="\[token\]"\>\` to their site  
\- Optilens checks for it during crawl  
\- Verified owners: all restrictions bypassed permanently  
\- Adds trust signal badge in dashboard: \*"Verified owner"\*

\*\*Update CLAUDE.md\*\* — add to Phase 1 Step 1.5 checklist:  
\`\`\`  
□ robots.txt check runs before every crawl  
□ Owner override checkbox on audit submission  
□ owner\_override field added to audits table  
□ /bot page live at optilens.ai/bot  
□ Crawl delay respected from robots.txt directive

