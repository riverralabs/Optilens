import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '@/lib/supabase'
import { useAuthStore } from '@/store/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import type { SiteType } from '@/types'
import {
  ShoppingCart,
  Laptop,
  FileText,
  Building2,
  AppWindow,
  ArrowRight,
  ArrowLeft,
  Rocket,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const SITE_TYPES: { value: SiteType; label: string; description: string; icon: typeof ShoppingCart }[] = [
  { value: 'ecommerce', label: 'E-commerce', description: 'Online store or marketplace', icon: ShoppingCart },
  { value: 'saas', label: 'SaaS', description: 'Software as a service', icon: Laptop },
  { value: 'landing_page', label: 'Landing Page', description: 'Marketing or product page', icon: FileText },
  { value: 'corporate', label: 'Corporate', description: 'Company or brand website', icon: Building2 },
  { value: 'webapp', label: 'Web App', description: 'Interactive application', icon: AppWindow },
]

export default function Onboarding() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const [step, setStep] = useState(1)
  const [workspaceName, setWorkspaceName] = useState('')
  const [siteType, setSiteType] = useState<SiteType | null>(null)
  const [auditUrl, setAuditUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleComplete() {
    if (!user) {
      setError('Not authenticated. Please log in again.')
      return
    }

    if (!workspaceName.trim()) {
      setError('Workspace name is required')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // 1. Create organization
      const { data: org, error: orgError } = await supabase
        .from('organizations')
        .insert({ name: workspaceName.trim() })
        .select('id')
        .single()

      if (orgError) {
        throw new Error(orgError.message)
      }

      // 2. Create user record linked to org with 'owner' role
      const { error: userError } = await supabase
        .from('users')
        .insert({
          id: user.id,
          org_id: org.id,
          role: 'owner',
          email: user.email ?? '',
        })

      if (userError) {
        throw new Error(userError.message)
      }

      // 3. If URL provided, create the first audit and redirect to progress
      if (auditUrl.trim()) {
        const { data: audit, error: auditError } = await supabase
          .from('audits')
          .insert({
            org_id: org.id,
            created_by: user.id,
            url: auditUrl.trim(),
            site_type: siteType,
            status: 'queued',
          })
          .select('id')
          .single()

        if (auditError) {
          throw new Error(auditError.message)
        }

        navigate(`/dashboard/audits/${audit.id}`, { replace: true })
      } else {
        navigate('/dashboard', { replace: true })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Setup failed')
    } finally {
      setLoading(false)
    }
  }

  function isValidUrl(url: string): boolean {
    try {
      const parsed = new URL(url.startsWith('http') ? url : `https://${url}`)
      return Boolean(parsed.hostname.includes('.'))
    } catch {
      return false
    }
  }

  function canProceed(): boolean {
    if (step === 1) return workspaceName.trim().length > 0
    if (step === 2) return siteType !== null
    if (step === 3) return auditUrl.trim() === '' || isValidUrl(auditUrl)
    return false
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-lg space-y-6">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2">
          <div className="w-10 h-10 rounded-md bg-accent flex items-center justify-center">
            <span className="text-white font-heading font-bold text-lg">O</span>
          </div>
          <span className="font-heading font-bold text-2xl text-foreground">Optilens</span>
        </div>

        {/* Progress indicator */}
        <div className="flex items-center justify-center gap-2">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={cn(
                'h-2 rounded-full transition-all',
                s === step ? 'w-8 bg-accent' : s < step ? 'w-8 bg-accent/40' : 'w-8 bg-border',
              )}
            />
          ))}
        </div>

        <Card>
          {/* Step 1: Workspace name */}
          {step === 1 && (
            <>
              <CardHeader className="text-center">
                <CardTitle className="text-xl">Name your workspace</CardTitle>
                <CardDescription>This is usually your company or project name</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  placeholder="e.g. Acme Corp"
                  value={workspaceName}
                  onChange={(e) => setWorkspaceName(e.target.value)}
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && canProceed()) setStep(2)
                  }}
                />
                <Button
                  className="w-full"
                  onClick={() => setStep(2)}
                  disabled={!canProceed()}
                >
                  Continue <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </CardContent>
            </>
          )}

          {/* Step 2: Site type selection */}
          {step === 2 && (
            <>
              <CardHeader className="text-center">
                <CardTitle className="text-xl">What type of site?</CardTitle>
                <CardDescription>This helps our AI agents pick the right frameworks</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3">
                  {SITE_TYPES.map((type) => (
                    <button
                      key={type.value}
                      onClick={() => setSiteType(type.value)}
                      className={cn(
                        'flex items-center gap-3 p-3 rounded-button border text-left transition-all',
                        siteType === type.value
                          ? 'border-accent bg-accent/5 ring-1 ring-accent'
                          : 'border-border hover:border-accent/40',
                      )}
                    >
                      <type.icon
                        className={cn(
                          'w-5 h-5 flex-shrink-0',
                          siteType === type.value ? 'text-accent' : 'text-text3',
                        )}
                      />
                      <div>
                        <p className="text-sm font-medium text-foreground">{type.label}</p>
                        <p className="text-xs text-text3">{type.description}</p>
                      </div>
                    </button>
                  ))}
                </div>

                <div className="flex gap-3">
                  <Button variant="outline" onClick={() => setStep(1)}>
                    <ArrowLeft className="w-4 h-4 mr-2" /> Back
                  </Button>
                  <Button
                    className="flex-1"
                    onClick={() => setStep(3)}
                    disabled={!canProceed()}
                  >
                    Continue <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </CardContent>
            </>
          )}

          {/* Step 3: Enter URL + run first audit */}
          {step === 3 && (
            <>
              <CardHeader className="text-center">
                <CardTitle className="text-xl">Run your first audit</CardTitle>
                <CardDescription>Enter your website URL to get started</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  type="url"
                  placeholder="https://yoursite.com"
                  value={auditUrl}
                  onChange={(e) => setAuditUrl(e.target.value)}
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && canProceed() && !loading) handleComplete()
                  }}
                />
                {auditUrl && !isValidUrl(auditUrl) && (
                  <p className="text-xs text-critical">Please enter a valid URL</p>
                )}

                {error && (
                  <p className="text-sm text-critical">{error}</p>
                )}

                <div className="flex gap-3">
                  <Button variant="outline" onClick={() => setStep(2)}>
                    <ArrowLeft className="w-4 h-4 mr-2" /> Back
                  </Button>
                  <Button
                    className="flex-1"
                    onClick={handleComplete}
                    disabled={!canProceed() || loading}
                  >
                    {loading ? (
                      'Setting up...'
                    ) : auditUrl.trim() ? (
                      <>
                        <Rocket className="w-4 h-4 mr-2" /> Launch Audit
                      </>
                    ) : (
                      'Skip to Dashboard'
                    )}
                  </Button>
                </div>
              </CardContent>
            </>
          )}
        </Card>
      </div>
    </div>
  )
}
