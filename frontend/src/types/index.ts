export interface Organization {
  id: string
  name: string
  plan: 'solo' | 'team' | 'agency'
  white_label_config: Record<string, unknown>
  created_at: string
}

export interface User {
  id: string
  org_id: string
  role: 'owner' | 'admin' | 'analyst' | 'viewer'
  email: string
  created_at: string
}

export interface Audit {
  id: string
  org_id: string
  created_by: string | null
  url: string
  site_type: string | null
  framework_applied: string[] | null
  status: 'queued' | 'running' | 'complete' | 'failed'
  cro_score: number | null
  previous_score: number | null
  revenue_leak_monthly: number | null
  revenue_leak_confidence: 'High' | 'Medium' | 'Estimated' | null
  pages_audited: string[] | null
  agent_outputs: Record<string, unknown> | null
  audit_duration_seconds: number | null
  created_at: string
  completed_at: string | null
}

export interface Issue {
  id: string
  audit_id: string
  org_id: string
  agent: 'ux' | 'copy' | 'performance' | 'seo' | 'github' | null
  severity: 'critical' | 'high' | 'medium' | 'low' | null
  category: string | null
  title: string
  description: string | null
  recommendation: string | null
  affected_element: string | null
  screenshot_url: string | null
  ice_score: number | null
  impact_score: number | null
  confidence_score: number | null
  effort_score: number | null
  revenue_impact_monthly: number | null
  ab_variants: unknown[] | null
  status: 'open' | 'in_progress' | 'resolved' | 'dismissed'
  created_at: string
}

export interface Report {
  id: string
  audit_id: string
  pdf_url: string | null
  excel_url: string | null
  screenshots_zip_url: string | null
  white_labeled: boolean
  generated_at: string
  expires_at: string
}

export type SiteType = 'ecommerce' | 'saas' | 'landing_page' | 'corporate' | 'webapp'

export type ScoreBand = 'Optimized' | 'Needs Work' | 'High Risk' | 'Critical'

export interface AgentStatusEvent {
  agent: string | null
  progress: number
  completed_agents: string[]
}

export interface AuditCompleteEvent {
  cro_score: number
  issues_found: number
  report_ready: boolean
}
