import { apiClient } from './client'
import { Agent, AgentListResponse } from '../types'

export async function fetchAgents(status?: string): Promise<AgentListResponse> {
  const query = status ? `?status=${encodeURIComponent(status)}` : ''
  return apiClient<AgentListResponse>(`/api/v1/agents${query}`)
}

export async function fetchAgent(id: string): Promise<Agent> {
  return apiClient<Agent>(`/api/v1/agents/${encodeURIComponent(id)}`)
}
