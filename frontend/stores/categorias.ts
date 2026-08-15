import { defineStore } from 'pinia'
import type { Categoria } from '~/types/api'

export const useCategoriasStore = defineStore('categorias', {
  state: () => ({
    categorias: [] as Categoria[],
  }),
  actions: {
    async fetchAll() {
      const api = useApi()
      this.categorias = await api<Categoria[]>('/categorias')
    },
    async crear(nombre: string) {
      const api = useApi()
      const categoria = await api<Categoria>('/categorias', {
        method: 'POST',
        body: { nombre },
      })
      this.categorias.push(categoria)
      this.categorias.sort((a, b) => a.nombre.localeCompare(b.nombre))
      return categoria
    },
  },
})
