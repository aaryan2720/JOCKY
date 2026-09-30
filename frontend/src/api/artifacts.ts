import { apiClient } from './client'
import { Artifact, ArtifactListResponse } from '../types'

export interface ArtifactFilters {
  jobId?: string
  agentId?: string
  type?: string
  limit?: number
  offset?: number
}

export async function fetchArtifacts(filters: ArtifactFilters = {}): Promise<ArtifactListResponse> {
  const params = new URLSearchParams()
  if (filters.jobId) params.append('job_id', filters.jobId)
  if (filters.agentId) params.append('agent_id', filters.agentId)
  if (filters.type) params.append('type', filters.type)
  if (filters.limit !== undefined) params.append('limit', String(filters.limit))
  if (filters.offset !== undefined) params.append('offset', String(filters.offset))

  const query = params.toString() ? `?${params.toString()}` : ''
  return apiClient<ArtifactListResponse>(`/api/v1/artifacts${query}`)
}

export async function fetchArtifact(artifactId: string): Promise<Artifact> {
  return apiClient<Artifact>(`/api/v1/artifacts/${encodeURIComponent(artifactId)}`)
}
