import { create } from 'zustand'
import type { User as SupabaseUser, Session } from '@supabase/supabase-js'

interface OrgInfo {
  id: string
  name: string
  plan: 'solo' | 'team' | 'agency'
}

interface AuthState {
  user: SupabaseUser | null
  session: Session | null
  loading: boolean
  orgInfo: OrgInfo | null
  userRole: string | null
  onboardingComplete: boolean | null
  setUser: (user: SupabaseUser | null) => void
  setSession: (session: Session | null) => void
  setLoading: (loading: boolean) => void
  setOrgInfo: (org: OrgInfo | null) => void
  setUserRole: (role: string | null) => void
  setOnboardingComplete: (complete: boolean | null) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  session: null,
  loading: true,
  orgInfo: null,
  userRole: null,
  onboardingComplete: null,
  setUser: (user) => set({ user }),
  setSession: (session) => set({ session }),
  setLoading: (loading) => set({ loading }),
  setOrgInfo: (orgInfo) => set({ orgInfo }),
  setUserRole: (userRole) => set({ userRole }),
  setOnboardingComplete: (onboardingComplete) => set({ onboardingComplete }),
}))
