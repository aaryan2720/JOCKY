import { apiClient } from './client'
import { Detection, DetectionListResponse } from '../types'

export interface DetectionFilters {
  agentId?: string
  jobId?: string
  severity?: string
  status?: string
  ruleId?: string
  limit?: number
  offset?: number
}

export async function fetchDetections(filters: DetectionFilters = {}): Promise<DetectionListResponse> {
  const params = new URLSearchParams()
  if (filters.agentId) params.append('agent_id', filters.agentId)
  if (filters.jobId) params.append('job_id', filters.jobId)
  if (filters.severity) params.append('severity', filters.severity)
  if (filters.status) params.append('status', filters.status)
  if (filters.ruleId) params.append('rule_id', filters.ruleId)
  if (filters.limit !== undefined) params.append('limit', String(filters.limit))
  if (filters.offset !== undefined) params.append('offset', String(filters.offset))

  const query = params.toString() ? `?${params.toString()}` : ''
  return apiClient<DetectionListResponse>(`/api/v1/detections${query}`)
}

export async function fetchDetection(detectionId: string): Promise<Detection> {
  return apiClient<Detection>(`/api/v1/detections/${encodeURIComponent(detectionId)}`)
}
