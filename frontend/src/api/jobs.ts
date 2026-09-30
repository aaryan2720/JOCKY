import { apiClient } from './client'
import { Job, JobCreatePayload, JobCreateResponse } from '../types'

export async function fetchJobs(agentId?: string, status?: string): Promise<Job[]> {
  const params = new URLSearchParams()
  if (agentId) params.append('agent_id', agentId)
  if (status) params.append('status', status)
  const query = params.toString() ? `?${params.toString()}` : ''
  return apiClient<Job[]>(`/api/v1/jobs${query}`)
}

export async function fetchJob(jobId: string): Promise<Job> {
  return apiClient<Job>(`/api/v1/jobs/${encodeURIComponent(jobId)}`)
}

export async function createJob(payload: JobCreatePayload): Promise<JobCreateResponse> {
  return apiClient<JobCreateResponse>('/api/v1/jobs', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
