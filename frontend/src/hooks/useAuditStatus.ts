import { useEffect, useState, useCallback } from 'react'
import type { AgentStatusEvent, AuditCompleteEvent } from '@/types'

const API_URL = import.meta.env.VITE_API_URL as string || 'http://localhost:8000'

interface UseAuditStatusReturn {
  progress: number
  currentAgent: string | null
  completedAgents: string[]
  isComplete: boolean
  isFailed: boolean
  result: AuditCompleteEvent | null
  error: string | null
}

/**
 * Hook to subscribe to real-time audit status via SSE.
 * Connects to /audits/{auditId}/status endpoint.
 */
export function useAuditStatus(auditId: string | null): UseAuditStatusReturn {
  const [progress, setProgress] = useState(0)
  const [currentAgent, setCurrentAgent] = useState<string | null>(null)
  const [completedAgents, setCompletedAgents] = useState<string[]>([])
  const [isComplete, setIsComplete] = useState(false)
  const [isFailed, setIsFailed] = useState(false)
  const [result, setResult] = useState<AuditCompleteEvent | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!auditId) return

    const eventSource = new EventSource(`${API_URL}/audits/${auditId}/status`)

    eventSource.addEventListener('agent_progress', (event) => {
      const data = JSON.parse(event.data) as AgentStatusEvent
      setProgress(data.progress)
      setCurrentAgent(data.agent)
      setCompletedAgents(data.completed_agents)
    })

    eventSource.addEventListener('audit_complete', (event) => {
      const data = JSON.parse(event.data) as AuditCompleteEvent
      setIsComplete(true)
      setProgress(100)
      setResult(data)
      eventSource.close()
    })

    eventSource.addEventListener('audit_failed', (event) => {
      const data = JSON.parse(event.data) as { message: string }
      setIsFailed(true)
      setError(data.message)
      eventSource.close()
    })

    eventSource.onerror = () => {
      setError('Connection lost. Retrying...')
    }

    return () => {
      eventSource.close()
    }
  }, [auditId])

  return { progress, currentAgent, completedAgents, isComplete, isFailed, result, error }
}
