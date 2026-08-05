import { defineStore } from 'pinia'
import { api } from '../api'
import type { Route } from '../types'

export const useRoutesStore = defineStore('routes', {
  state: () => ({ routes: [] as Route[], loading: false }),
  actions: {
    async load() {
      this.loading = true
      try { this.routes = await api.listRoutes() } finally { this.loading = false }
    },
  },
})
