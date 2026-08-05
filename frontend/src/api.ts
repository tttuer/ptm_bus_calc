import type { Estimate, Route, RouteInput } from './types'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, { headers: { 'Content-Type': 'application/json' }, ...options })
  if (!response.ok) throw new Error((await response.json()).detail ?? '요청에 실패했습니다.')
  return response.status === 204 ? undefined as T : response.json()
}

export const api = {
  listRoutes: () => request<Route[]>('/routes'),
  createRoute: (route: RouteInput) => request<Route>('/routes', { method: 'POST', body: JSON.stringify(route) }),
  updateRoute: (id: string, route: RouteInput) => request<Route>(`/routes/${id}`, { method: 'PUT', body: JSON.stringify(route) }),
  deleteRoute: (id: string) => request<void>(`/routes/${id}`, { method: 'DELETE' }),
  estimate: (route: RouteInput) => request<Estimate>('/routes/estimate', { method: 'POST', body: JSON.stringify(route) }),
}
