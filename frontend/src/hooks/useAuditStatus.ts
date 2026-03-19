import { useEffect, useRef, useState } from 'react'
import type { AgentStatusEvent, AuditCompleteEvent } from '@/types'

const API_URL = import.meta.env.VITE_API_URL as string || 'http://localhost:8000'

/** How long (ms) without any progress event before we consider it stalled */
const STALL_TIMEOUT_MS = 120_000

interface UseAuditStatusReturn {
  progress: number
  currentAgent: string | null
  completedAgents: string[]
  isComplete: boolean
  isFailed: boolean
  isStalled: boolean
  result: AuditCompleteEvent | null
  error: string | null
}

/**
 * Hook to subscribe to real-time audit status via SSE.
 * Connects to /audits/{auditId}/status endpoint.
 * Detects stalled audits (no progress for 2 minutes).
 */
export function useAuditStatus(auditId: string | null): UseAuditStatusReturn {
  const [progress, setProgress] = useState(0)
  const [currentAgent, setCurrentAgent] = useState<string | null>(null)
  const [completedAgents, setCompletedAgents] = useState<string[]>([])
  const [isComplete, setIsComplete] = useState(false)
  const [isFailed, setIsFailed] = useState(false)
  const [isStalled, setIsStalled] = useState(false)
  const [result, setResult] = useState<AuditCompleteEvent | null>(null)
  const [error, setError] = useState<string | null>(null)
  const lastEventTime = useRef(Date.now())

  useEffect(() => {
    if (!auditId) return

    lastEventTime.current = Date.now()
    setIsStalled(false)

    const eventSource = new EventSource(`${API_URL}/audits/${auditId}/status`)

    eventSource.addEventListener('agent_progress', (event) => {
      lastEventTime.current = Date.now()
      setIsStalled(false)
      setError(null)
      const data = JSON.parse(event.data) as AgentStatusEvent
      setProgress(data.progress)
      setCurrentAgent(data.agent)
      setCompletedAgents(data.completed_agents ?? [])
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

    // Stall detection — check every 10s if we've received any event recently
    const stallCheck = setInterval(() => {
      if (Date.now() - lastEventTime.current > STALL_TIMEOUT_MS) {
        setIsStalled(true)
      }
    }, 10_000)

    return () => {
      eventSource.close()
      clearInterval(stallCheck)
    }
  }, [auditId])

  return { progress, currentAgent, completedAgents, isComplete, isFailed, isStalled, result, error }
}
