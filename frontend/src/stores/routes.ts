import { defineStore } from 'pinia'
import { api } from '../api'
import type { Schedule } from '../types'

export const useSchedulesStore = defineStore('schedules', {
  state: () => ({ schedules: [] as Schedule[], loading: false }),
  actions: {
    async load() { this.loading = true; try { this.schedules = await api.listSchedules() } finally { this.loading = false } },
  },
})
