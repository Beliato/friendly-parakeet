import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useApi } from '~/composables/useApi'
import { useAuthStore } from '~/stores/auth'

interface OpcionesFetch {
  baseURL: string
  onRequest: (ctx: { options: { headers: Headers } }) => void
  onResponseError: (ctx: { response: { status: number } }) => void
}

const { createMock } = vi.hoisted(() => ({
  createMock: vi.fn((_opciones: unknown) => vi.fn()),
}))
vi.stubGlobal('$fetch', { create: createMock })

/** Opciones con las que useApi construyó su instancia de $fetch. */
function interceptores(): OpcionesFetch {
  const ultima = createMock.mock.calls.at(-1)
  if (!ultima) throw new Error('useApi no llamó a $fetch.create')
  return ultima[0] as OpcionesFetch
}

describe('useApi', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    createMock.mockClear()
  })

  it('apunta al apiBase del runtime config', () => {
    useApi()
    expect(interceptores().baseURL).toBe(useRuntimeConfig().public.apiBase)
  })

  it('agrega el header Authorization cuando hay sesión', () => {
    const auth = useAuthStore()
    auth.token = 'tok-abc'
    useApi()

    const headers = new Headers()
    interceptores().onRequest({ options: { headers } })

    expect(headers.get('Authorization')).toBe('Bearer tok-abc')
  })

  it('no agrega Authorization si no hay token', () => {
    useApi()
    const headers = new Headers()
    interceptores().onRequest({ options: { headers } })
    expect(headers.get('Authorization')).toBeNull()
  })

  it('un 401 cierra la sesión', () => {
    const auth = useAuthStore()
    auth.token = 'tok-vencido'
    useApi()

    interceptores().onResponseError({ response: { status: 401 } })

    expect(auth.token).toBeNull()
  })

  it('otros errores no cierran la sesión', () => {
    const auth = useAuthStore()
    auth.token = 'tok-ok'
    useApi()

    interceptores().onResponseError({ response: { status: 500 } })

    expect(auth.token).toBe('tok-ok')
  })
})
