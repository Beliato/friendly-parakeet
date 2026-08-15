import { defineStore } from 'pinia'
import type {
  Etapa,
  OrigenRegalo,
  Prioridad,
  RangoPrecio,
  Regalo,
  RegalosDePersona,
} from '~/types/api'

export interface RegistrarRegaloPayload {
  item_id?: number
  item_nuevo?: {
    nombre: string
    descripcion?: string | null
    categoria_id?: number | null
    etapa?: Etapa
    prioridad?: Prioridad
    rango_precio?: RangoPrecio | null
  }
  persona?: string
  origen?: OrigenRegalo
  cantidad?: number
  fecha?: string | null
  nota?: string | null
}

interface Filtros {
  persona?: string
  agradecido?: boolean
}

export const useRegalosStore = defineStore('regalos', {
  state: () => ({
    regalos: [] as Regalo[],
    porPersona: [] as RegalosDePersona[],
    personas: [] as string[],
    cargando: false,
  }),
  getters: {
    pendientesDeAgradecer: (state) =>
      state.regalos.filter((r) => !r.agradecido && r.persona).length,
  },
  actions: {
    _reemplazar(regalo: Regalo) {
      const idx = this.regalos.findIndex((r) => r.id === regalo.id)
      if (idx >= 0) this.regalos[idx] = regalo
    },
    async fetchAll(filtros: Filtros = {}) {
      const api = useApi()
      this.cargando = true
      try {
        this.regalos = await api<Regalo[]>('/regalos', { query: filtros })
      } finally {
        this.cargando = false
      }
    },
    async fetchPorPersona() {
      const api = useApi()
      this.porPersona = await api<RegalosDePersona[]>('/regalos/por-persona')
    },
    async fetchPersonas(q?: string) {
      const api = useApi()
      this.personas = await api<string[]>('/regalos/personas', {
        query: q ? { q } : undefined,
      })
      return this.personas
    },
    async registrar(body: RegistrarRegaloPayload) {
      const api = useApi()
      const regalo = await api<Regalo>('/regalos', { method: 'POST', body })
      this.regalos.unshift(regalo)
      return regalo
    },
    async editar(
      id: number,
      body: {
        persona?: string
        cantidad?: number
        fecha?: string
        nota?: string | null
        agradecido?: boolean
      },
    ) {
      const api = useApi()
      const regalo = await api<Regalo>(`/regalos/${id}`, {
        method: 'PATCH',
        body,
      })
      this._reemplazar(regalo)
      return regalo
    },
    async marcarAgradecido(id: number, agradecido: boolean) {
      return await this.editar(id, { agradecido })
    },
    async eliminar(id: number) {
      const api = useApi()
      await api(`/regalos/${id}`, { method: 'DELETE' })
      this.regalos = this.regalos.filter((r) => r.id !== id)
    },
    async subirFoto(regaloId: number, file: File) {
      const api = useApi()
      const presign = await api<{ upload_url: string; key: string }>(
        `/regalos/${regaloId}/fotos/presign`,
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
      const foto = await api(`/regalos/${regaloId}/fotos`, {
        method: 'POST',
        body: { key: presign.key, orden: 0 },
      })
      const regalo = this.regalos.find((r) => r.id === regaloId)
      if (regalo) regalo.fotos.push(foto as never)
      return foto
    },
    async eliminarFoto(regaloId: number, fotoId: number) {
      const api = useApi()
      await api(`/regalos/${regaloId}/fotos/${fotoId}`, { method: 'DELETE' })
      const regalo = this.regalos.find((r) => r.id === regaloId)
      if (regalo) regalo.fotos = regalo.fotos.filter((f) => f.id !== fotoId)
    },
  },
})
