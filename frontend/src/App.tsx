import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import * as Sentry from '@sentry/react'
import { supabase } from '@/lib/supabase'
import { useAuthStore } from '@/store/auth'
import DashboardLayout from '@/components/layout/DashboardLayout'
import ProtectedRoute from '@/components/layout/ProtectedRoute'
import Dashboard from '@/pages/Dashboard'
import AuditReport from '@/pages/AuditReport'
import AuditsLibrary from '@/pages/AuditsLibrary'
import Connections from '@/pages/Connections'
import Progress from '@/pages/Progress'
import Settings from '@/pages/Settings'

// Initialize Sentry
const sentryDsn = import.meta.env.VITE_SENTRY_DSN as string | undefined
if (sentryDsn) {
  Sentry.init({
    dsn: sentryDsn,
    integrations: [
      Sentry.browserTracingIntegration(),
    ],
    tracesSampleRate: import.meta.env.DEV ? 1.0 : 0.2,
  })
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 2,
    },
  },
})

export default function App() {
  const { setUser, setSession, setLoading } = useAuthStore()

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session)
        setUser(session?.user ?? null)
        setLoading(false)
      },
    )

    return () => subscription.unsubscribe()
  }, [setUser, setSession, setLoading])

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public routes — auth pages built in Step 1.3 */}
          <Route path="/login" element={<div>Login page — Step 1.3</div>} />
          <Route path="/signup" element={<div>Signup page — Step 1.3</div>} />

          {/* Protected dashboard routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="audits" element={<AuditsLibrary />} />
            <Route path="audits/:auditId" element={<AuditReport />} />
            <Route path="library" element={<AuditsLibrary />} />
            <Route path="connections" element={<Connections />} />
            <Route path="progress" element={<Progress />} />
            <Route path="settings" element={<Settings />} />
          </Route>

          {/* Root redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
