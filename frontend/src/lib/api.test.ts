import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock supabase before importing api
vi.mock('./supabase', () => ({
  supabase: {
    auth: {
      getSession: vi.fn(),
    },
  },
}))

import { api } from './api'
import { supabase } from './supabase'

const mockFetch = vi.fn()
global.fetch = mockFetch

function mockSession(token = 'test-token') {
  vi.mocked(supabase.auth.getSession).mockResolvedValue({
    data: { session: { access_token: token } },
    error: null,
  } as never)
}

describe('api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('throws when not authenticated', async () => {
    vi.mocked(supabase.auth.getSession).mockResolvedValue({
      data: { session: null },
      error: null,
    } as never)

    await expect(api.audits.list()).rejects.toThrow('Not authenticated')
  })

  it('lists audits with auth header', async () => {
    mockSession()
    const audits = [{ id: '1', url: 'https://example.com', status: 'complete' }]
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(audits),
    })

    const result = await api.audits.list()
    expect(result).toEqual(audits)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/audits'),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
        }),
      }),
    )
  })

  it('creates an audit', async () => {
    mockSession()
    const audit = { id: '1', url: 'https://example.com', status: 'queued' }
    mockFetch.mockResolvedValue({
      ok: true,
      status: 201,
      json: () => Promise.resolve(audit),
    })

    const result = await api.audits.create({ url: 'https://example.com' })
    expect(result).toEqual(audit)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/audits'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ url: 'https://example.com' }),
      }),
    )
  })

  it('handles API errors', async () => {
    mockSession()
    mockFetch.mockResolvedValue({
      ok: false,
      status: 403,
      json: () => Promise.resolve({ detail: 'Forbidden' }),
    })

    await expect(api.audits.list()).rejects.toThrow('Forbidden')
  })

  it('handles 204 No Content for delete', async () => {
    mockSession()
    mockFetch.mockResolvedValue({
      ok: true,
      status: 204,
      json: () => Promise.resolve(undefined),
    })

    const result = await api.audits.delete('audit-id')
    expect(result).toBeUndefined()
  })

  it('updates issue status', async () => {
    mockSession()
    const issue = { id: 'issue-1', status: 'resolved' }
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(issue),
    })

    const result = await api.issues.update('issue-1', 'resolved')
    expect(result).toEqual(issue)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/issues/issue-1'),
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({ status: 'resolved' }),
      }),
    )
  })
})
