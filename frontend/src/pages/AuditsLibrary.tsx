import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import CroScoreGauge from '@/components/audit/CroScoreGauge'
import NewAuditDialog from '@/components/audit/NewAuditDialog'
import { api } from '@/lib/api'
import type { AuditData } from '@/lib/api'
import { Plus, RefreshCw, ExternalLink } from 'lucide-react'

type StatusFilter = 'all' | 'queued' | 'running' | 'complete' | 'failed'

const statusFilters: { value: StatusFilter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'complete', label: 'Complete' },
  { value: 'running', label: 'Running' },
  { value: 'queued', label: 'Queued' },
  { value: 'failed', label: 'Failed' },
]

const statusVariant: Record<string, 'default' | 'success' | 'warning' | 'info' | 'critical'> = {
  queued: 'info',
  running: 'warning',
  complete: 'success',
  failed: 'critical',
}

export default function AuditsLibrary() {
  const [showNewAudit, setShowNewAudit] = useState(false)
  const [filter, setFilter] = useState<StatusFilter>('all')

  const { data: audits, isLoading } = useQuery({
    queryKey: ['audits'],
    queryFn: () => api.audits.list(),
  })

  const filtered = audits?.filter((a) => filter === 'all' || a.status === filter) ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-heading font-bold">Audits Library</h1>
        <Button onClick={() => setShowNewAudit(true)}>
          <Plus className="w-4 h-4 mr-2" /> New Audit
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {statusFilters.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-3 py-1.5 rounded-button text-sm font-medium transition-colors ${
              filter === f.value
                ? 'bg-accent text-white'
                : 'bg-surface text-text2 border border-border hover:bg-muted'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-text3">
              {filter === 'all' ? 'No audits yet. Run your first audit.' : `No ${filter} audits.`}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {/* Table header */}
          <div className="grid grid-cols-12 gap-4 px-4 py-2 text-xs font-medium text-text3 uppercase tracking-wider">
            <div className="col-span-4">URL</div>
            <div className="col-span-2">Site Type</div>
            <div className="col-span-1 text-center">Score</div>
            <div className="col-span-1 text-center">Issues</div>
            <div className="col-span-2">Date</div>
            <div className="col-span-1">Status</div>
            <div className="col-span-1"></div>
          </div>

          {filtered.map((audit) => (
            <AuditRow key={audit.id} audit={audit} />
          ))}
        </div>
      )}

      <NewAuditDialog open={showNewAudit} onClose={() => setShowNewAudit(false)} />
    </div>
  )
}

function AuditRow({ audit }: { audit: AuditData }) {
  const variant = statusVariant[audit.status] ?? 'default'
  const agentOutputs = audit.agent_outputs as Record<string, unknown> | null
  const issuesCount = agentOutputs?.issues
    ? (agentOutputs.issues as unknown[]).length
    : null

  return (
    <Link to={`/dashboard/audits/${audit.id}`}>
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="py-3 px-4">
          <div className="grid grid-cols-12 gap-4 items-center">
            {/* URL */}
            <div className="col-span-4 flex items-center gap-2 min-w-0">
              <ExternalLink className="w-3.5 h-3.5 text-text3 flex-shrink-0" />
              <span className="text-sm font-medium truncate">
                {audit.url.replace(/^https?:\/\//, '')}
              </span>
            </div>

            {/* Site type */}
            <div className="col-span-2">
              <span className="text-sm text-text2">{audit.site_type ?? '—'}</span>
            </div>

            {/* Score */}
            <div className="col-span-1 flex justify-center">
              {audit.cro_score != null ? (
                <div className="relative">
                  <CroScoreGauge score={audit.cro_score} size="sm" showBand={false} />
                </div>
              ) : (
                <span className="text-sm text-text3">—</span>
              )}
            </div>

            {/* Issues count */}
            <div className="col-span-1 text-center">
              <span className="text-sm text-text2">{issuesCount ?? '—'}</span>
            </div>

            {/* Date */}
            <div className="col-span-2">
              <span className="text-sm text-text3">
                {new Date(audit.created_at).toLocaleDateString()}
              </span>
            </div>

            {/* Status */}
            <div className="col-span-1">
              <Badge variant={variant} className="text-[10px]">
                {audit.status}
              </Badge>
            </div>

            {/* Re-run */}
            <div className="col-span-1 flex justify-end">
              {audit.status === 'complete' && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    api.audits.rerun(audit.id)
                  }}
                  title="Re-run audit"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
