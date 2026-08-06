import type { Schedule, ScheduleInput } from './types'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, { headers: { 'Content-Type': 'application/json' }, ...options })
  if (!response.ok) throw new Error((await response.json()).detail ?? '요청에 실패했습니다.')
  return response.status === 204 ? undefined as T : response.json()
}

export const api = {
  listSchedules: () => request<Schedule[]>('/schedules'),
  createSchedule: (schedule: ScheduleInput) => request<Schedule>('/schedules', { method: 'POST', body: JSON.stringify(schedule) }),
  updateSchedule: (id: string, schedule: ScheduleInput) => request<Schedule>(`/schedules/${id}`, { method: 'PUT', body: JSON.stringify(schedule) }),
  deleteSchedule: (id: string) => request<void>(`/schedules/${id}`, { method: 'DELETE' }),
}
