import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '@/lib/supabase'

export default function AuthCallback() {
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function handleCallback() {
      try {
        const { data: { session }, error: authError } = await supabase.auth.getSession()

        if (authError) {
          setError(authError.message)
          return
        }

        if (!session) {
          // No session yet — Supabase may still be processing the OAuth callback
          // The onAuthStateChange listener in App.tsx will pick it up
          return
        }

        // Check if user already has an org (returning user vs new signup)
        const { data: userRow } = await supabase
          .from('users')
          .select('org_id')
          .eq('id', session.user.id)
          .maybeSingle()

        if (userRow?.org_id) {
          // Existing user — go to dashboard
          navigate('/dashboard', { replace: true })
        } else {
          // New user — needs onboarding
          navigate('/onboarding', { replace: true })
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Authentication failed')
      }
    }

    handleCallback()
  }, [navigate])

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-critical text-sm">{error}</p>
          <a href="/login" className="text-accent hover:underline text-sm">
            Back to login
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-accent border-t-transparent" />
    </div>
  )
}
