import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import CroScoreGauge from '@/components/audit/CroScoreGauge'
import NewAuditDialog from '@/components/audit/NewAuditDialog'
import { api } from '@/lib/api'
import type { AuditData } from '@/lib/api'
import { Plus, DollarSign, AlertTriangle, ArrowRight } from 'lucide-react'

const statusVariant: Record<string, 'default' | 'success' | 'warning' | 'info'> = {
  queued: 'info',
  running: 'warning',
  complete: 'success',
  failed: 'critical' as 'warning',
}

export default function Dashboard() {
  const [showNewAudit, setShowNewAudit] = useState(false)

  const { data: audits, isLoading } = useQuery({
    queryKey: ['audits'],
    queryFn: () => api.audits.list(),
  })

  const recentAudits = audits?.slice(0, 6) ?? []

  // Get top 3 critical issues from the latest complete audit
  const latestComplete = audits?.find((a) => a.status === 'complete')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-heading font-bold">Dashboard</h1>
        <Button onClick={() => setShowNewAudit(true)}>
          <Plus className="w-4 h-4 mr-2" /> Run New Audit
        </Button>
      </div>

      {isLoading ? (
        <DashboardSkeleton />
      ) : !audits || audits.length === 0 ? (
        <EmptyState onStartAudit={() => setShowNewAudit(true)} />
      ) : (
        <>
          {/* Top row — score + revenue + top fixes */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* CRO Score */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm text-text2 font-medium">CRO Score</CardTitle>
              </CardHeader>
              <CardContent className="flex justify-center">
                {latestComplete?.cro_score != null ? (
                  <div className="relative">
                    <CroScoreGauge score={latestComplete.cro_score} size="lg" />
                    {latestComplete.previous_score != null && (
                      <div className="text-center mt-2">
                        <Badge variant={latestComplete.cro_score > latestComplete.previous_score ? 'success' : 'critical'}>
                          {latestComplete.cro_score > latestComplete.previous_score ? '+' : ''}
                          {latestComplete.cro_score - latestComplete.previous_score} pts
                        </Badge>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center text-text3 py-8">
                    <p className="text-sm">No completed audit yet</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Revenue Leak */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm text-text2 font-medium flex items-center gap-2">
                  <DollarSign className="w-4 h-4" /> Revenue Leak
                </CardTitle>
              </CardHeader>
              <CardContent>
                {latestComplete?.revenue_leak_monthly != null ? (
                  <div className="text-center py-4">
                    <p className="text-3xl font-heading font-bold text-accent">
                      ${latestComplete.revenue_leak_monthly.toLocaleString()}
                    </p>
                    <p className="text-xs text-text3 mt-1">estimated monthly</p>
                    <Badge variant="secondary" className="mt-2">
                      {latestComplete.revenue_leak_confidence ?? 'Estimated'}
                    </Badge>
                  </div>
                ) : (
                  <div className="text-center text-text3 py-8">
                    <p className="text-sm">Run an audit to see estimates</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Top 3 Fixes */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm text-text2 font-medium flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" /> Top Fixes
                </CardTitle>
              </CardHeader>
              <CardContent>
                {latestComplete ? (
                  <div className="space-y-3">
                    {/* We show issues from agent_outputs since we don't fetch issues separately here */}
                    {(latestComplete.agent_outputs as Record<string, unknown>)?.issues
                      ? ((latestComplete.agent_outputs as Record<string, unknown>).issues as Array<Record<string, unknown>>)
                          .slice(0, 3)
                          .map((issue, i) => (
                            <div key={i} className="flex items-start gap-2">
                              <SeverityDot severity={issue.severity as string} />
                              <p className="text-sm text-foreground line-clamp-2">
                                {issue.title as string}
                              </p>
                            </div>
                          ))
                      : <p className="text-sm text-text3">No issues data available</p>
                    }
                    {latestComplete && (
                      <Link
                        to={`/dashboard/audits/${latestComplete.id}`}
                        className="text-xs text-accent hover:underline flex items-center gap-1"
                      >
                        View all issues <ArrowRight className="w-3 h-3" />
                      </Link>
                    )}
                  </div>
                ) : (
                  <div className="text-center text-text3 py-8">
                    <p className="text-sm">No issues found yet</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recent Audits */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-heading font-semibold">Recent Audits</h2>
              <Link
                to="/dashboard/audits"
                className="text-sm text-accent hover:underline flex items-center gap-1"
              >
                View all <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recentAudits.map((audit) => (
                <AuditCard key={audit.id} audit={audit} />
              ))}
            </div>
          </div>
        </>
      )}

      <NewAuditDialog open={showNewAudit} onClose={() => setShowNewAudit(false)} />
    </div>
  )
}

function AuditCard({ audit }: { audit: AuditData }) {
  const variant = statusVariant[audit.status] ?? 'default'

  return (
    <Link to={`/dashboard/audits/${audit.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-foreground truncate max-w-[200px]">
              {audit.url.replace(/^https?:\/\//, '')}
            </p>
            <Badge variant={variant}>{audit.status}</Badge>
          </div>
          <div className="flex items-center justify-between">
            {audit.cro_score != null ? (
              <div className="relative">
                <CroScoreGauge score={audit.cro_score} size="sm" showBand={false} />
              </div>
            ) : (
              <div className="w-[80px] h-[80px] flex items-center justify-center">
                {audit.status === 'running' ? (
                  <div className="animate-spin rounded-full h-6 w-6 border-2 border-accent border-t-transparent" />
                ) : (
                  <span className="text-text3 text-xs">—</span>
                )}
              </div>
            )}
            <div className="text-right">
              <p className="text-xs text-text3">
                {new Date(audit.created_at).toLocaleDateString()}
              </p>
              {audit.site_type && (
                <p className="text-xs text-text3 mt-1">{audit.site_type}</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}

function SeverityDot({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: 'bg-critical',
    high: 'bg-accent',
    medium: 'bg-[#F59E0B]',
    low: 'bg-info',
  }
  return <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${colors[severity] ?? 'bg-text3'}`} />
}

function EmptyState({ onStartAudit }: { onStartAudit: () => void }) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-16">
        <div className="w-16 h-16 rounded-full bg-accent/10 flex items-center justify-center mb-4">
          <Plus className="w-8 h-8 text-accent" />
        </div>
        <h2 className="text-lg font-heading font-semibold mb-2">Run your first audit</h2>
        <p className="text-sm text-text2 mb-6 text-center max-w-md">
          Enter a URL to get an AI-powered CRO analysis with actionable insights,
          revenue leak estimates, and a prioritized backlog.
        </p>
        <Button onClick={onStartAudit}>
          <Plus className="w-4 h-4 mr-2" /> Run New Audit
        </Button>
      </CardContent>
    </Card>
  )
}

function DashboardSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {[1, 2, 3].map((i) => (
        <Card key={i}>
          <CardHeader>
            <Skeleton className="h-4 w-24" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-32 w-full" />
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
