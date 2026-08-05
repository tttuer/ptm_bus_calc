import type { Estimate, Route, RouteInput, Stop } from './types'

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
  drivingDistance: (origin: Stop, destination: Stop) => request<{ distance_m: number }>('/routes/driving-distance', {
    method: 'POST', body: JSON.stringify({
      origin_latitude: origin.latitude, origin_longitude: origin.longitude,
      destination_latitude: destination.latitude, destination_longitude: destination.longitude,
    }),
  }),
}
