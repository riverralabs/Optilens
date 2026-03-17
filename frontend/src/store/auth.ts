import { create } from 'zustand'
import type { User as SupabaseUser, Session } from '@supabase/supabase-js'

interface AuthState {
  user: SupabaseUser | null
  session: Session | null
  loading: boolean
  setUser: (user: SupabaseUser | null) => void
  setSession: (session: Session | null) => void
  setLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  session: null,
  loading: true,
  setUser: (user) => set({ user }),
  setSession: (session) => set({ session }),
  setLoading: (loading) => set({ loading }),
}))
