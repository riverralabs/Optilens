import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import CroScoreGauge, { getScoreBand } from '@/components/audit/CroScoreGauge'
import { useAuditStatus } from '@/hooks/useAuditStatus'
import { api } from '@/lib/api'
import type { AuditData, IssueData } from '@/lib/api'
import { Download, RefreshCw, ArrowLeft, CheckCircle, XCircle, Clock } from 'lucide-react'

const AGENT_LABELS: Record<string, string> = {
  site_intelligence: 'Site Intelligence',
  ux_vision: 'UX Analysis',
  copy_content: 'Copy Analysis',
  data_performance: 'Performance & SEO',
  synthesis: 'Synthesis',
}

const TAB_LABELS = [
  { key: 'overview', label: 'Overview' },
  { key: 'ux', label: 'UX & Visual', comingSoon: true },
  { key: 'copy', label: 'Copy', comingSoon: true },
  { key: 'performance', label: 'Performance', comingSoon: true },
  { key: 'github', label: 'GitHub', comingSoon: true },
  { key: 'heatmap', label: 'Heatmap', comingSoon: true },
]

export default function AuditReport() {
  const { auditId } = useParams<{ auditId: string }>()
  const navigate = useNavigate()

  const { data: audit, isLoading, refetch } = useQuery({
    queryKey: ['audit', auditId],
    queryFn: () => api.audits.get(auditId!),
    enabled: Boolean(auditId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'queued' || status === 'running' ? 3000 : false
    },
  })

  const { data: issues } = useQuery({
    queryKey: ['issues', auditId],
    queryFn: () => api.issues.list(auditId!),
    enabled: Boolean(auditId) && audit?.status === 'complete',
  })

  // SSE for real-time progress when running
  const isRunning = audit?.status === 'queued' || audit?.status === 'running'
  const sseStatus = useAuditStatus(isRunning ? auditId! : null)

  if (isLoading) return <AuditReportSkeleton />

  if (!audit) {
    return (
      <div className="text-center py-16">
        <p className="text-text2">Audit not found</p>
        <Button variant="link" onClick={() => navigate('/dashboard')}>
          Back to dashboard
        </Button>
      </div>
    )
  }

  // Show progress view if still running
  if (isRunning) {
    return <AuditProgress audit={audit} sseStatus={sseStatus} />
  }

  // Show failed state
  if (audit.status === 'failed') {
    return <AuditFailed audit={audit} onRetry={() => refetch()} />
  }

  // Complete — show report
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate('/dashboard')}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-xl font-heading font-bold">
              {audit.url.replace(/^https?:\/\//, '')}
            </h1>
            <p className="text-xs text-text3">
              Audited {new Date(audit.created_at).toLocaleDateString()} | {audit.site_type ?? 'Unknown type'}
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm">
          <Download className="w-4 h-4 mr-2" /> Download PDF
        </Button>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-border">
        {TAB_LABELS.map((tab) => (
          <button
            key={tab.key}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 ${
              tab.key === 'overview'
                ? 'border-accent text-accent'
                : 'border-transparent text-text3 hover:text-foreground'
            }`}
            disabled={tab.comingSoon}
          >
            {tab.label}
            {tab.comingSoon && (
              <span className="ml-1 text-[10px] text-text3">Soon</span>
            )}
          </button>
        ))}
      </div>

      {/* Overview tab content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* CRO Score */}
        <Card className="lg:col-span-1">
          <CardContent className="flex flex-col items-center justify-center py-8">
            <div className="relative">
              <CroScoreGauge score={audit.cro_score ?? 0} size="lg" />
            </div>
            {audit.previous_score != null && (
              <Badge
                variant={(audit.cro_score ?? 0) >= audit.previous_score ? 'success' : 'critical'}
                className="mt-3"
              >
                {(audit.cro_score ?? 0) > audit.previous_score ? '+' : ''}
                {(audit.cro_score ?? 0) - audit.previous_score} pts vs previous
              </Badge>
            )}
          </CardContent>
        </Card>

        {/* Revenue Leak + Summary */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm text-text2">Executive Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-6">
              <div className="bg-accent/5 rounded-card p-4 text-center">
                <p className="text-2xl font-heading font-bold text-accent">
                  ${(audit.revenue_leak_monthly ?? 0).toLocaleString()}
                </p>
                <p className="text-xs text-text3">monthly leak</p>
                <Badge variant="secondary" className="mt-1 text-[10px]">
                  {audit.revenue_leak_confidence ?? 'Estimated'}
                </Badge>
              </div>
              <div className="flex-1">
                <p className="text-sm text-text2 leading-relaxed">
                  This {audit.site_type ?? 'website'} scored{' '}
                  <strong>{audit.cro_score}/100</strong> ({getScoreBand(audit.cro_score ?? 0)}),
                  with {issues?.length ?? 0} issue{(issues?.length ?? 0) !== 1 ? 's' : ''} identified
                  across UX, copy, and performance.
                  {audit.framework_applied?.length
                    ? ` Analysis used the ${audit.framework_applied.join(' + ')} framework${audit.framework_applied.length > 1 ? 's' : ''}.`
                    : ''}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top 5 Issues */}
      <Card>
        <CardHeader>
          <CardTitle>Top Issues</CardTitle>
        </CardHeader>
        <CardContent>
          {issues && issues.length > 0 ? (
            <div className="space-y-3">
              {issues.slice(0, 5).map((issue) => (
                <IssueRow key={issue.id} issue={issue} />
              ))}
              {issues.length > 5 && (
                <p className="text-xs text-text3 pt-2">
                  + {issues.length - 5} more issues
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-text3">No issues found.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function IssueRow({ issue }: { issue: IssueData }) {
  const severityVariant: Record<string, 'critical' | 'warning' | 'info' | 'default'> = {
    critical: 'critical',
    high: 'warning',
    medium: 'info',
    low: 'default',
  }
  const variant = severityVariant[issue.severity ?? 'medium'] ?? 'default'

  return (
    <div className="flex items-start gap-3 p-3 rounded-button border border-border hover:bg-muted/50 transition-colors">
      <Badge variant={variant} className="mt-0.5 flex-shrink-0">
        {issue.severity}
      </Badge>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground">{issue.title}</p>
        {issue.recommendation && (
          <p className="text-xs text-text2 mt-1 line-clamp-2">{issue.recommendation}</p>
        )}
      </div>
      <div className="text-right flex-shrink-0">
        <p className="text-xs text-text3">{issue.agent}</p>
        {issue.ice_score != null && (
          <p className="text-xs font-medium text-accent">ICE {issue.ice_score}</p>
        )}
      </div>
    </div>
  )
}

function AuditProgress({
  audit,
  sseStatus,
}: {
  audit: AuditData
  sseStatus: ReturnType<typeof useAuditStatus>
}) {
  const progress = sseStatus.progress || (audit.status === 'queued' ? 0 : 5)
  const currentAgent = sseStatus.currentAgent

  const agents = ['site_intelligence', 'ux_vision', 'copy_content', 'data_performance', 'synthesis']

  // Also treat agents as completed if progress has moved past them
  const agentProgressThresholds: Record<string, number> = {
    site_intelligence: 25,
    ux_vision: 50,
    copy_content: 60,
    data_performance: 70,
    synthesis: 95,
  }

  const isAgentCompleted = (agent: string) => {
    if (sseStatus.completedAgents.includes(agent)) return true
    const threshold = agentProgressThresholds[agent]
    return threshold != null && progress >= threshold
  }

  return (
    <div className="max-w-lg mx-auto py-16 space-y-8">
      <div className="text-center">
        {sseStatus.isStalled ? (
          <XCircle className="w-12 h-12 text-warning mx-auto mb-4" />
        ) : (
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-accent border-t-transparent mx-auto mb-4" />
        )}
        <h2 className="text-xl font-heading font-bold">
          {sseStatus.isStalled ? 'Audit is taking longer than expected' : 'Analyzing your site'}
        </h2>
        <p className="text-sm text-text2 mt-1">
          {audit.url.replace(/^https?:\/\//, '')}
        </p>
        {sseStatus.isStalled && (
          <p className="text-xs text-warning mt-2">
            The audit may still be running. You can wait or try again later.
          </p>
        )}
        {sseStatus.error && !sseStatus.isStalled && (
          <p className="text-xs text-text3 mt-2">{sseStatus.error}</p>
        )}
      </div>

      {/* Progress bar */}
      <div>
        <div className="flex justify-between text-xs text-text3 mb-1">
          <span>Progress</span>
          <span>{progress}%</span>
        </div>
        <div className="h-2 bg-border rounded-full overflow-hidden">
          <div
            className="h-full bg-accent rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Agent status list */}
      <div className="space-y-2">
        {agents.map((agent) => {
          const completed = isAgentCompleted(agent)
          const isCurrent = currentAgent === agent && !completed
          const label = AGENT_LABELS[agent] ?? agent

          return (
            <div key={agent} className="flex items-center gap-3 py-2">
              {completed ? (
                <CheckCircle className="w-5 h-5 text-success flex-shrink-0" />
              ) : isCurrent ? (
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-accent border-t-transparent flex-shrink-0" />
              ) : (
                <Clock className="w-5 h-5 text-text3 flex-shrink-0" />
              )}
              <span
                className={`text-sm ${
                  completed
                    ? 'text-text2'
                    : isCurrent
                      ? 'text-foreground font-medium'
                      : 'text-text3'
                }`}
              >
                {label}
                {isCurrent && ' ...'}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function AuditFailed({ audit, onRetry }: { audit: AuditData; onRetry: () => void }) {
  const errorMsg = (audit.agent_outputs as Record<string, unknown>)?.error as string | undefined

  return (
    <div className="max-w-md mx-auto py-16 text-center space-y-4">
      <XCircle className="w-12 h-12 text-critical mx-auto" />
      <h2 className="text-xl font-heading font-bold">Audit Failed</h2>
      <p className="text-sm text-text2">
        {errorMsg ?? 'Something went wrong during the audit. Please try again.'}
      </p>
      <Button onClick={onRetry} variant="outline">
        <RefreshCw className="w-4 h-4 mr-2" /> Retry Audit
      </Button>
    </div>
  )
}

function AuditReportSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-64" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Skeleton className="h-48" />
        <Skeleton className="h-48 lg:col-span-2" />
      </div>
      <Skeleton className="h-64" />
    </div>
  )
}
