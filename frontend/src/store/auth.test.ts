import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from './auth'

describe('useAuthStore', () => {
  beforeEach(() => {
    // Reset store between tests
    useAuthStore.setState({
      user: null,
      session: null,
      loading: true,
      orgInfo: null,
      userRole: null,
      onboardingComplete: null,
    })
  })

  it('starts with loading=true and null values', () => {
    const state = useAuthStore.getState()
    expect(state.loading).toBe(true)
    expect(state.user).toBeNull()
    expect(state.session).toBeNull()
    expect(state.orgInfo).toBeNull()
  })

  it('sets loading state', () => {
    useAuthStore.getState().setLoading(false)
    expect(useAuthStore.getState().loading).toBe(false)
  })

  it('sets user role', () => {
    useAuthStore.getState().setUserRole('admin')
    expect(useAuthStore.getState().userRole).toBe('admin')
  })

  it('sets org info', () => {
    const org = { id: 'org-1', name: 'Test Org', plan: 'team' as const }
    useAuthStore.getState().setOrgInfo(org)
    expect(useAuthStore.getState().orgInfo).toEqual(org)
  })

  it('sets onboarding complete', () => {
    useAuthStore.getState().setOnboardingComplete(true)
    expect(useAuthStore.getState().onboardingComplete).toBe(true)
  })

  it('clears user on logout', () => {
    useAuthStore.getState().setUserRole('owner')
    useAuthStore.getState().setUser(null)
    useAuthStore.getState().setSession(null)
    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.session).toBeNull()
    // Role persists until explicitly cleared
    expect(state.userRole).toBe('owner')
  })
})
