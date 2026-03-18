import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { api } from '@/lib/api'
import { Rocket, X } from 'lucide-react'

interface NewAuditDialogProps {
  open: boolean
  onClose: () => void
}

export default function NewAuditDialog({ open, onClose }: NewAuditDialogProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [url, setUrl] = useState('')
  const [error, setError] = useState<string | null>(null)

  const createAudit = useMutation({
    mutationFn: (auditUrl: string) => api.audits.create({ url: auditUrl }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['audits'] })
      onClose()
      setUrl('')
      navigate(`/dashboard/audits/${data.id}`)
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : 'Failed to create audit')
    },
  })

  function isValidUrl(input: string): boolean {
    try {
      const parsed = new URL(input.startsWith('http') ? input : `https://${input}`)
      return Boolean(parsed.hostname.includes('.'))
    } catch {
      return false
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    const fullUrl = url.startsWith('http') ? url : `https://${url}`
    if (!isValidUrl(fullUrl)) {
      setError('Please enter a valid URL')
      return
    }
    createAudit.mutate(fullUrl)
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <Card className="w-full max-w-md mx-4">
        <CardHeader className="relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-text3 hover:text-foreground transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
          <CardTitle>Run New Audit</CardTitle>
          <CardDescription>Enter a URL to analyze for CRO improvements</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              type="text"
              placeholder="https://yoursite.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              autoFocus
            />
            {error && <p className="text-sm text-critical">{error}</p>}
            <Button
              type="submit"
              className="w-full"
              disabled={!url.trim() || createAudit.isPending}
            >
              {createAudit.isPending ? (
                'Starting audit...'
              ) : (
                <>
                  <Rocket className="w-4 h-4 mr-2" /> Start Audit
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
