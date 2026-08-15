import { defineStore } from 'pinia'
import type { Item, OrigenAdquisicion } from '~/types/api'

export const useItemsStore = defineStore('items', {
  state: () => ({
    items: [] as Item[],
    pendientes: 0,
    cargando: false,
  }),
  actions: {
    _reemplazar(item: Item) {
      const idx = this.items.findIndex((i) => i.id === item.id)
      if (idx >= 0) this.items[idx] = item
    },
    async fetchAll() {
      const api = useApi()
      this.cargando = true
      try {
        this.items = await api<Item[]>('/items')
      } finally {
        this.cargando = false
      }
    },
    async fetchPendientes() {
      const api = useApi()
      const data = await api<{ pendientes: number }>(
        '/reservas/pendientes/count',
      )
      this.pendientes = data.pendientes
    },
    async crear(body: {
      nombre: string
      descripcion?: string | null
      amazon_link?: string | null
    }) {
      const api = useApi()
      const item = await api<Item>('/items', { method: 'POST', body })
      this.items.unshift(item)
      return item
    },
    async editar(
      id: number,
      body: {
        nombre?: string
        descripcion?: string | null
        amazon_link?: string | null
      },
    ) {
      const api = useApi()
      const item = await api<Item>(`/items/${id}`, { method: 'PATCH', body })
      this._reemplazar(item)
      return item
    },
    async adquirir(
      id: number,
      origen: OrigenAdquisicion,
      gifterName?: string | null,
    ) {
      const api = useApi()
      const item = await api<Item>(`/items/${id}/adquirir`, {
        method: 'PATCH',
        body: { origen, gifter_name: gifterName ?? null },
      })
      this._reemplazar(item)
      await this.fetchPendientes()
      return item
    },
    async eliminar(id: number) {
      const api = useApi()
      await api(`/items/${id}`, { method: 'DELETE' })
      this.items = this.items.filter((i) => i.id !== id)
    },
    async liberarReserva(id: number) {
      const api = useApi()
      const item = await api<Item>(`/items/${id}/liberar-reserva`, {
        method: 'POST',
      })
      this._reemplazar(item)
      await this.fetchPendientes()
      return item
    },
    async asignarCaja(id: number, cajaId: number | null) {
      const api = useApi()
      const item = await api<Item>(`/items/${id}/caja`, {
        method: 'PATCH',
        body: { caja_id: cajaId },
      })
      this._reemplazar(item)
      return item
    },
    async subirFoto(itemId: number, file: File) {
      const api = useApi()
      const presign = await api<{ upload_url: string; key: string }>(
        `/items/${itemId}/fotos/presign`,
        {
          method: 'POST',
          body: { content_type: file.type, size_bytes: file.size },
        },
      )
      await $fetch(presign.upload_url, {
        method: 'PUT',
        body: file,
        headers: { 'Content-Type': file.type },
      })
      const foto = await api(`/items/${itemId}/fotos`, {
        method: 'POST',
        body: { key: presign.key, orden: 0 },
      })
      const item = this.items.find((i) => i.id === itemId)
      if (item) item.fotos.push(foto as never)
      return foto
    },
    async eliminarFoto(itemId: number, fotoId: number) {
      const api = useApi()
      await api(`/items/${itemId}/fotos/${fotoId}`, { method: 'DELETE' })
      const item = this.items.find((i) => i.id === itemId)
      if (item) item.fotos = item.fotos.filter((f) => f.id !== fotoId)
    },
  },
})
