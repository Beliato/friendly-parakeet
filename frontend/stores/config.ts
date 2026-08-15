import { defineStore } from 'pinia'

const NOMBRE_DEFAULT = 'Julia en Camino'

export const useConfigStore = defineStore('config', {
  state: () => ({
    nombreApp: NOMBRE_DEFAULT,
    cargado: false,
  }),
  actions: {
    async fetch() {
      if (this.cargado) return
      try {
        const config = useRuntimeConfig()
        const data = await $fetch<{ nombre_app: string }>('/config', {
          baseURL: config.public.apiBase,
        })
        this.nombreApp = data.nombre_app
        this.cargado = true
      } catch {
        // Sin backend disponible se mantiene el default — la UI no se rompe.
      }
    },
    setNombre(nombre: string) {
      this.nombreApp = nombre
    },
  },
})
