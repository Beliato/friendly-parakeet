import { beforeEach, describe, expect, it } from 'vitest'

import { useReservasLocales } from '~/composables/useReservasLocales'

describe('reservas locales del invitado', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('guarda el token de deshacer por item', () => {
    const { reservas, guardar } = useReservasLocales()
    guardar(7, 'token-abc')
    expect(reservas.value[7]).toBe('token-abc')
    expect(JSON.parse(localStorage.getItem('julia_reservas')!)).toEqual({
      7: 'token-abc',
    })
  })

  it('cargar recupera lo guardado en una visita anterior', () => {
    localStorage.setItem('julia_reservas', JSON.stringify({ 3: 'tok-3' }))
    const { reservas, cargar } = useReservasLocales()
    cargar()
    expect(reservas.value[3]).toBe('tok-3')
  })

  it('olvidar elimina solo esa reserva', () => {
    const { reservas, guardar, olvidar } = useReservasLocales()
    guardar(1, 'tok-1')
    guardar(2, 'tok-2')
    olvidar(1)
    expect(reservas.value[1]).toBeUndefined()
    expect(reservas.value[2]).toBe('tok-2')
  })

  it('tolera localStorage corrupto sin romper', () => {
    localStorage.setItem('julia_reservas', 'no-es-json')
    const { reservas, cargar } = useReservasLocales()
    cargar()
    expect(reservas.value).toEqual({})
  })
})
