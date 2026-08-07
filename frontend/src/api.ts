const apiBase = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

async function errorMessage(response: Response) {
  const body = await response.json().catch(() => ({}))
  const detail = body.detail
  return Array.isArray(detail) ? detail.map(item => `${item.loc.at(-1)}: ${item.msg}`).join(', ') : detail || '요청에 실패했습니다.'
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, { headers: { 'Content-Type': 'application/json' }, ...options })
  if (!response.ok) throw new Error(await errorMessage(response))
  return response.status === 204 ? undefined as T : response.json()
}

export const scheduleApi = {
  generate: (config: unknown) => request('/schedule/generate', { method: 'POST', body: JSON.stringify(config) }),
  exportExcel: async (schedule: unknown[]) => {
    const response = await fetch(`${apiBase}/schedule/export-excel`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(schedule),
    })
    if (!response.ok) throw new Error(await errorMessage(response))
    return response.blob()
  },
}
