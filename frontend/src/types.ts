export type Stop = {
  name: string
  distance_from_previous_m: number
  latitude: number | null
  longitude: number | null
}

export type StopResult = Stop & { segment_seconds: number; cumulative_seconds: number }

export type RouteInput = { name: string; average_speed_kmh: number; stops: Stop[] }

export type Route = Omit<RouteInput, 'stops'> & {
  id: string
  stops: StopResult[]
  total_distance_m: number
  total_seconds: number
}

export type Estimate = Pick<Route, 'stops' | 'total_distance_m' | 'total_seconds'>
