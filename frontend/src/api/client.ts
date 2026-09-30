export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
export const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws')

export class ApiError extends Error {
  status: number
  statusText: string
  detail?: string

  constructor(status: number, statusText: string, detail?: string) {
    super(detail || `API Error ${status}: ${statusText}`)
    this.name = 'ApiError'
    this.status = status
    this.statusText = statusText
    this.detail = detail
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  let response: Response

  try {
    response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })
  } catch (err: any) {
    throw new ApiError(
      0,
      'Network Error',
      `Failed to connect to backend management server: ${err.message}`
    )
  }

  if (!response.ok) {
    let errorDetail = response.statusText
    try {
      const errJson = await response.json()
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail)
      }
    } catch {
      // Ignore if body is not JSON
    }
    throw new ApiError(response.status, response.statusText, errorDetail)
  }

  return response.json()
}
