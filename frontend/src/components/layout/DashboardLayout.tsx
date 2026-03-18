import { useEffect, useState } from 'react'
import { Outlet, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import { supabase } from '@/lib/supabase'
import Sidebar from './Sidebar'

export default function DashboardLayout() {
  const { session, setOrgInfo, setUserRole, setOnboardingComplete } = useAuthStore()
  const [checking, setChecking] = useState(true)
  const [onboarded, setOnboarded] = useState<boolean | null>(null)

  useEffect(() => {
    async function checkOnboarding() {
      if (!session?.user) {
        setChecking(false)
        return
      }

      const { data: userRow } = await supabase
        .from('users')
        .select('org_id, role')
        .eq('id', session.user.id)
        .maybeSingle()

      if (!userRow?.org_id) {
        setOnboardingComplete(false)
        setOnboarded(false)
        setChecking(false)
        return
      }

      // Fetch org info
      const { data: org } = await supabase
        .from('organizations')
        .select('id, name, plan')
        .eq('id', userRow.org_id)
        .single()

      if (org) {
        setOrgInfo({ id: org.id, name: org.name, plan: org.plan })
      }
      setUserRole(userRow.role)
      setOnboardingComplete(true)
      setOnboarded(true)
      setChecking(false)
    }

    checkOnboarding()
  }, [session, setOrgInfo, setUserRole, setOnboardingComplete])

  if (checking) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-accent border-t-transparent" />
      </div>
    )
  }

  if (onboarded === false) {
    return <Navigate to="/onboarding" replace />
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 bg-background p-4 pt-16 lg:p-8 lg:pt-8 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
