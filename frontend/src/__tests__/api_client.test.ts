import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient, ApiError } from '../api/client'
import { fetchAgents, fetchJobs, createJob, validateScript } from '../api'

describe('Frontend API Client & Error Handling', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('constructs ApiError correctly with status, text, and detail', () => {
    const err = new ApiError(404, 'Not Found', 'Agent with ID agent-99 not found')
    expect(err.status).toBe(404)
    expect(err.statusText).toBe('Not Found')
    expect(err.detail).toBe('Agent with ID agent-99 not found')
    expect(err.message).toBe('Agent with ID agent-99 not found')
  })

  it('handles successful API responses', async () => {
    const mockData = { total: 1, items: [{ id: 'agent-1', hostname: 'SRV-01', os: 'windows' }] }
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockData,
    } as any)

    const res = await apiClient<{ total: number; items: any[] }>('/api/v1/agents')
    expect(res.total).toBe(1)
    expect(res.items[0].hostname).toBe('SRV-01')
  })

  it('throws ApiError with detail on HTTP 400/500 responses', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      json: async () => ({ detail: 'Invalid JOCKY DSL syntax' }),
    } as any)

    await expect(apiClient('/api/v1/scripts/validate')).rejects.toThrow(ApiError)
  })

  it('handles network disconnection gracefully', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Failed to fetch'))

    await expect(apiClient('/health')).rejects.toThrow('Failed to connect to backend management server')
  })

  it('encodes query parameters properly in fetchAgents and fetchJobs', async () => {
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ total: 0, items: [] }),
    } as any)
    global.fetch = fetchSpy

    await fetchAgents('online')
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/agents?status=online'),
      expect.any(Object)
    )

    fetchSpy.mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    } as any)

    await fetchJobs('agent-win-1', 'running')
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/jobs?agent_id=agent-win-1&status=running'),
      expect.any(Object)
    )
  })

  it('submits JOCKY script validation and job dispatch payloads properly', async () => {
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        valid: true,
        ast_summary: { statements: 2 },
        estimated_artifacts: ['processes'],
        errors: [],
      }),
    } as any)
    global.fetch = fetchSpy

    const valResult = await validateScript('COLLECT processes;')
    expect(valResult.valid).toBe(true)
    expect(valResult.estimated_artifacts).toContain('processes')

    fetchSpy.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        job_id: 'job-test-123',
        status: 'queued',
        agent_count: 1,
        created_at: '2026-09-30T10:00:00Z',
      }),
    } as any)

    const jobResult = await createJob({
      script_body: 'COLLECT processes;',
      target_agent_ids: ['agent-1'],
    })
    expect(jobResult.job_id).toBe('job-test-123')
    expect(jobResult.status).toBe('queued')
  })
})
