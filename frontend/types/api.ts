export type EstadoItem = 'NECESITADO' | 'RESERVADO' | 'ADQUIRIDO'
export type OrigenAdquisicion = 'NOSOTROS' | 'REGALO'
export type Prioridad = 'URGENTE' | 'NORMAL' | 'PUEDE_ESPERAR'
export type RangoPrecio = 'BAJO' | 'MEDIO' | 'ALTO'
export type OrigenRegalo = 'REGALO' | 'NOSOTROS'
export type Etapa =
  | 'CUALQUIERA'
  | 'RECIEN_NACIDO'
  | 'M0_3'
  | 'M3_6'
  | 'M6_12'
  | 'A1_2'
  | 'A2_MAS'

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
  etapa: Etapa
  estado: EstadoItem
  origen_adquisicion: OrigenAdquisicion | null
  personas: string[]
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
  etapa: Etapa
  personas: string[]
  caja: Caja | null
}

export interface FotoRegalo {
  id: number
  url: string
  orden: number
}

/** El hecho: recibimos este objeto de parte de esta persona. */
export interface Regalo {
  id: number
  item: { id: number; nombre: string; etapa: Etapa; fotos: FotoItem[] }
  persona: string
  origen: OrigenRegalo
  cantidad: number
  fecha: string
  nota: string | null
  agradecido: boolean
  fotos: FotoRegalo[]
}

export interface RegalosDePersona {
  persona: string
  total_regalos: number
  pendientes_de_agradecer: number
  regalos: Regalo[]
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

export const ETAPA_LABEL: Record<Etapa, string> = {
  CUALQUIERA: 'Cualquier etapa',
  RECIEN_NACIDO: 'Recién nacido',
  M0_3: '0-3 meses',
  M3_6: '3-6 meses',
  M6_12: '6-12 meses',
  A1_2: '1-2 años',
  A2_MAS: 'Más de 2 años',
}

export const ETAPAS: Etapa[] = [
  'CUALQUIERA',
  'RECIEN_NACIDO',
  'M0_3',
  'M3_6',
  'M6_12',
  'A1_2',
  'A2_MAS',
]
