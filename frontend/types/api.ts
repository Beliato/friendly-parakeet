export type EstadoItem = 'NECESITADO' | 'RESERVADO' | 'ADQUIRIDO'
export type OrigenAdquisicion = 'NOSOTROS' | 'REGALO'
export type Prioridad = 'URGENTE' | 'NORMAL' | 'PUEDE_ESPERAR'
export type RangoPrecio = 'BAJO' | 'MEDIO' | 'ALTO'

export interface FotoItem {
  id: number
  url: string
  orden: number
}

export interface Caja {
  id: number
  etiqueta: string
  descripcion: string | null
}

export interface Categoria {
  id: number
  nombre: string
}

export interface Item {
  id: number
  nombre: string
  descripcion: string | null
  amazon_link: string | null
  cantidad: number
  cantidad_recibida: number
  reservas_activas: number
  prioridad: Prioridad
  rango_precio: RangoPrecio | null
  categoria: Categoria | null
  estado: EstadoItem
  origen_adquisicion: OrigenAdquisicion | null
  gifter_name: string | null
  caja: Caja | null
  fotos: FotoItem[]
  created_at: string
  updated_at: string
}

/** Reserva vista por el admin: sin nombre ni mensaje hasta recibirla. */
export interface ReservaAdmin {
  id: number
  unidad: number
  dias_desde_reserva: number
}

/** Solo se obtiene al marcar la unidad como recibida. */
export interface ReservaRevelada {
  nombre: string
  mensaje: string | null
  item: Item
}

export interface ItemBusqueda {
  id: number
  nombre: string
  descripcion: string | null
  estado: EstadoItem
  caja: Caja | null
}

export interface ItemPublico {
  id: number
  nombre: string
  descripcion: string | null
  amazon_link: string | null
  cantidad: number
  disponibles: number
  prioridad: Prioridad
  rango_precio: RangoPrecio | null
  categoria: string | null
  fotos: FotoItem[]
}

export interface WishlistPublica {
  nombre_app: string
  items: ItemPublico[]
}

export const PRIORIDAD_LABEL: Record<Prioridad, string> = {
  URGENTE: 'Urgente',
  NORMAL: 'Normal',
  PUEDE_ESPERAR: 'Puede esperar',
}

export const RANGO_PRECIO_LABEL: Record<RangoPrecio, string> = {
  BAJO: '$',
  MEDIO: '$$',
  ALTO: '$$$',
}
