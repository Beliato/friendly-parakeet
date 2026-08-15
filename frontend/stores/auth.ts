import { defineStore } from 'pinia'

interface AdminOut {
  id: number
  email: string
}

const TOKEN_KEY = 'julia_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null as string | null,
    admin: null as AdminOut | null,
  }),
  getters: {
    autenticado: (state) => !!state.token,
  },
  actions: {
    init() {
      if (import.meta.client) {
        this.token = localStorage.getItem(TOKEN_KEY)
      }
    },
    async login(email: string, password: string) {
      const config = useRuntimeConfig()
      const data = await $fetch<{ access_token: string }>('/auth/login', {
        method: 'POST',
        baseURL: config.public.apiBase,
        body: { email, password },
      })
      this.token = data.access_token
      if (import.meta.client) {
        localStorage.setItem(TOKEN_KEY, this.token)
      }
      await this.fetchMe()
    },
    async fetchMe() {
      if (!this.token) return
      const config = useRuntimeConfig()
      try {
        this.admin = await $fetch<AdminOut>('/auth/me', {
          baseURL: config.public.apiBase,
          headers: { Authorization: `Bearer ${this.token}` },
        })
      } catch {
        this.logout()
      }
    },
    logout() {
      this.token = null
      this.admin = null
      if (import.meta.client) {
        localStorage.removeItem(TOKEN_KEY)
      }
    },
  },
})
