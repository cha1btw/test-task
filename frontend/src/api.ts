import type { ProjectsResponse } from './types'

const API_BASE_URL = 'http://localhost:8000'

export async function fetchProjects(): Promise<ProjectsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/projects`)

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`
    try {
      const body = await response.json()
      if (body?.detail) detail = body.detail
    } catch {
      // ignore JSON parse errors, use default message
    }
    throw new Error(detail)
  }

  return response.json()
}
