/** Reservas hechas desde este navegador.
 *
 * Como los invitados no tienen cuenta, el `token_deshacer` que devuelve la
 * API al reservar es la única credencial para liberar esa reserva. Se guarda
 * en localStorage por item para poder ofrecer "deshacer" al volver a entrar.
 */

const STORAGE_KEY = 'julia_reservas'

type ReservasLocales = Record<number, string>

function leer(): ReservasLocales {
  if (!import.meta.client) return {}
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
  } catch {
    return {}
  }
}

export function useReservasLocales() {
  const reservas = useState<ReservasLocales>('reservas-locales', () => ({}))

  function cargar() {
    reservas.value = leer()
  }

  function guardar(itemId: number, token: string) {
    reservas.value = { ...reservas.value, [itemId]: token }
    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(reservas.value))
    }
  }

  function olvidar(itemId: number) {
    const copia = { ...reservas.value }
    delete copia[itemId]
    reservas.value = copia
    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(copia))
    }
  }

  return { reservas, cargar, guardar, olvidar }
}
