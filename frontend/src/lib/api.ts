import { supabase } from './supabase'

const API_URL = import.meta.env.VITE_API_URL as string || 'http://localhost:8000'

/**
 * Make an authenticated API request to the FastAPI backend.
 * Automatically attaches the Supabase session token.
 */
async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error('Not authenticated')
  }

  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${session.access_token}`,
        ...options.headers,
      },
    })
  } catch {
    throw new Error('Unable to reach the API server. Please try again later.')
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `API error: ${response.status}`)
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

// --- Audit API ---

export interface AuditCreatePayload {
  url: string
}

export interface AuditData {
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
  revenue_leak_confidence: string | null
  pages_audited: string[] | null
  agent_outputs: Record<string, unknown> | null
  audit_duration_seconds: number | null
  created_at: string
  completed_at: string | null
}

export interface IssueData {
  id: string
  audit_id: string
  org_id: string
  agent: string | null
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

export interface ReportData {
  id: string
  audit_id: string
  pdf: string | null
  excel: string | null
  screenshots_zip: string | null
  generated_at: string
  expires_at: string
}

export const api = {
  audits: {
    create: (payload: AuditCreatePayload) =>
      apiRequest<AuditData>('/audits', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    list: () => apiRequest<AuditData[]>('/audits'),
    get: (id: string) => apiRequest<AuditData>(`/audits/${id}`),
    rerun: (id: string) =>
      apiRequest<AuditData>(`/audits/${id}/rerun`, { method: 'POST' }),
    delete: (id: string) =>
      apiRequest<void>(`/audits/${id}`, { method: 'DELETE' }),
  },
  issues: {
    list: (auditId: string) => apiRequest<IssueData[]>(`/audits/${auditId}/issues`),
    update: (id: string, status: string) =>
      apiRequest<IssueData>(`/issues/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      }),
  },
  reports: {
    get: (auditId: string) => apiRequest<ReportData>(`/audits/${auditId}/report`),
    regenerate: (auditId: string) =>
      apiRequest<{ status: string }>(`/audits/${auditId}/report/regen`, {
        method: 'POST',
      }),
  },
}
