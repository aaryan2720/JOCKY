import { apiClient } from './client'
import { HealthStatus } from '../types'

export async function fetchHealth(): Promise<HealthStatus> {
  return apiClient<HealthStatus>('/health')
}
