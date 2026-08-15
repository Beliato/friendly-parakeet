import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '~/stores/auth'

const { fetchMock } = vi.hoisted(() => ({ fetchMock: vi.fn() }))
vi.stubGlobal('$fetch', fetchMock)

describe('store auth', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    fetchMock.mockReset()
  })

  it('arranca sin sesión', () => {
    const auth = useAuthStore()
    expect(auth.token).toBeNull()
    expect(auth.autenticado).toBe(false)
  })

  it('login guarda el token y consulta /auth/me', async () => {
    fetchMock.mockImplementation(async (url: string) =>
      url === '/auth/login'
        ? { access_token: 'tok-123' }
        : { id: 1, email: 'admin@test.com' },
    )

    const auth = useAuthStore()
    await auth.login('admin@test.com', 'clave')

    expect(auth.token).toBe('tok-123')
    expect(auth.autenticado).toBe(true)
    expect(auth.admin?.email).toBe('admin@test.com')
    expect(localStorage.getItem('julia_token')).toBe('tok-123')
  })

  it('init recupera la sesión persistida', () => {
    localStorage.setItem('julia_token', 'tok-guardado')
    const auth = useAuthStore()
    auth.init()
    expect(auth.autenticado).toBe(true)
  })

  it('logout limpia estado y localStorage', () => {
    localStorage.setItem('julia_token', 'tok')
    const auth = useAuthStore()
    auth.init()
    auth.logout()
    expect(auth.token).toBeNull()
    expect(auth.admin).toBeNull()
    expect(localStorage.getItem('julia_token')).toBeNull()
  })

  it('un /auth/me fallido cierra la sesión', async () => {
    fetchMock.mockRejectedValue(new Error('401'))
    const auth = useAuthStore()
    auth.token = 'tok-vencido'
    await auth.fetchMe()
    expect(auth.token).toBeNull()
  })
})
