export type EstadoItem = 'NECESITADO' | 'RESERVADO' | 'ADQUIRIDO'
export type OrigenAdquisicion = 'NOSOTROS' | 'REGALO'

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

export interface Item {
  id: number
  nombre: string
  descripcion: string | null
  amazon_link: string | null
  estado: EstadoItem
  origen_adquisicion: OrigenAdquisicion | null
  gifter_name: string | null
  caja: Caja | null
  fotos: FotoItem[]
  created_at: string
  updated_at: string
}

export interface ItemPublico {
  id: number
  nombre: string
  descripcion: string | null
  amazon_link: string | null
  fotos: FotoItem[]
}

export interface WishlistPublica {
  nombre_app: string
  items: ItemPublico[]
}
