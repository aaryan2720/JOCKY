import { apiClient } from './client'
import { JockyScript, ScriptValidateResponse } from '../types'

export async function fetchScripts(): Promise<JockyScript[]> {
  return apiClient<JockyScript[]>('/api/v1/scripts')
}

export async function validateScript(body: string): Promise<ScriptValidateResponse> {
  return apiClient<ScriptValidateResponse>('/api/v1/scripts/validate', {
    method: 'POST',
    body: JSON.stringify({ body }),
  })
}
