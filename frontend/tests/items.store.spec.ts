import { mockNuxtImport } from '@nuxt/test-utils/runtime'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useItemsStore } from '~/stores/items'
import type { Item } from '~/types/api'

const { apiMock } = vi.hoisted(() => ({ apiMock: vi.fn() }))
mockNuxtImport('useApi', () => () => apiMock)

function item(over: Partial<Item> = {}): Item {
  return {
    id: 1,
    nombre: 'Cuna',
    descripcion: null,
    amazon_link: null,
    estado: 'NECESITADO',
    origen_adquisicion: null,
    gifter_name: null,
    caja: null,
    fotos: [],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...over,
  }
}

describe('store items', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    apiMock.mockReset()
  })

  it('fetchAll carga el listado', async () => {
    apiMock.mockResolvedValue([item()])
    const store = useItemsStore()
    await store.fetchAll()
    expect(store.items).toHaveLength(1)
    expect(store.cargando).toBe(false)
  })

  it('crear agrega el item al principio', async () => {
    const store = useItemsStore()
    store.items = [item({ id: 1, nombre: 'Viejo' })]
    apiMock.mockResolvedValue(item({ id: 2, nombre: 'Nuevo' }))
    await store.crear({ nombre: 'Nuevo' })
    expect(store.items[0]!.nombre).toBe('Nuevo')
    expect(store.items).toHaveLength(2)
  })

  it('editar reemplaza el item en el listado', async () => {
    const store = useItemsStore()
    store.items = [item({ id: 1, nombre: 'Antes' })]
    apiMock.mockResolvedValue(item({ id: 1, nombre: 'Después' }))
    await store.editar(1, { nombre: 'Después' })
    expect(store.items[0]!.nombre).toBe('Después')
  })

  it('adquirir actualiza estado y refresca el contador', async () => {
    const store = useItemsStore()
    store.items = [item({ id: 1, estado: 'RESERVADO' })]
    apiMock
      .mockResolvedValueOnce(
        item({
          id: 1,
          estado: 'ADQUIRIDO',
          origen_adquisicion: 'REGALO',
          gifter_name: 'Abuela Marta',
        }),
      )
      .mockResolvedValueOnce({ pendientes: 0 })

    await store.adquirir(1, 'REGALO')

    expect(store.items[0]!.estado).toBe('ADQUIRIDO')
    expect(store.items[0]!.gifter_name).toBe('Abuela Marta')
    expect(store.pendientes).toBe(0)
  })

  it('liberarReserva devuelve el item a necesitado sin nombre', async () => {
    const store = useItemsStore()
    store.items = [item({ id: 1, estado: 'RESERVADO' })]
    apiMock
      .mockResolvedValueOnce(item({ id: 1, estado: 'NECESITADO' }))
      .mockResolvedValueOnce({ pendientes: 0 })

    await store.liberarReserva(1)

    expect(store.items[0]!.estado).toBe('NECESITADO')
    expect(store.items[0]!.gifter_name).toBeNull()
  })

  it('eliminar saca el item del listado', async () => {
    const store = useItemsStore()
    store.items = [item({ id: 1 }), item({ id: 2 })]
    apiMock.mockResolvedValue(undefined)
    await store.eliminar(1)
    expect(store.items.map((i) => i.id)).toEqual([2])
  })

  it('fetchPendientes guarda el contador', async () => {
    apiMock.mockResolvedValue({ pendientes: 3 })
    const store = useItemsStore()
    await store.fetchPendientes()
    expect(store.pendientes).toBe(3)
  })

  it('asignarCaja actualiza la caja del item', async () => {
    const store = useItemsStore()
    store.items = [item({ id: 1, estado: 'ADQUIRIDO' })]
    apiMock.mockResolvedValue(
      item({
        id: 1,
        estado: 'ADQUIRIDO',
        caja: { id: 5, etiqueta: 'Caja A', descripcion: null },
      }),
    )
    await store.asignarCaja(1, 5)
    expect(store.items[0]!.caja?.etiqueta).toBe('Caja A')
  })
})
