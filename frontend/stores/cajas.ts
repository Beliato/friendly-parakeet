import { defineStore } from 'pinia'
import type { Caja } from '~/types/api'

export const useCajasStore = defineStore('cajas', {
  state: () => ({
    cajas: [] as Caja[],
  }),
  actions: {
    async fetchAll() {
      const api = useApi()
      this.cajas = await api<Caja[]>('/cajas')
    },
    async crear(etiqueta: string, descripcion?: string | null) {
      const api = useApi()
      const caja = await api<Caja>('/cajas', {
        method: 'POST',
        body: { etiqueta, descripcion: descripcion ?? null },
      })
      this.cajas.push(caja)
      this.cajas.sort((a, b) => a.etiqueta.localeCompare(b.etiqueta))
      return caja
    },
  },
})
