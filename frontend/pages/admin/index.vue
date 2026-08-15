<script setup lang="ts">
import type { Etapa, Item, ItemBusqueda } from '~/types/api'
import {
  ETAPAS,
  ETAPA_LABEL,
  PRIORIDAD_LABEL,
  RANGO_PRECIO_LABEL,
} from '~/types/api'

definePageMeta({ middleware: 'auth' })

const auth = useAuthStore()
const items = useItemsStore()
const router = useRouter()
const toast = useToast()

const modalForm = ref(false)
const itemEditando = ref<Item | null>(null)
const itemAdquirir = ref<Item | null>(null)
const itemReservas = ref<Item | null>(null)
const itemCaja = ref<Item | null>(null)
const itemEliminar = ref<Item | null>(null)
const filtro = ref<'TODOS' | 'NECESITADO' | 'RESERVADO' | 'ADQUIRIDO'>('TODOS')
const filtroEtapa = ref<Etapa | 'TODAS'>('TODAS')
const modalRegistrar = ref(false)

const busqueda = ref('')
const resultados = ref<ItemBusqueda[] | null>(null)
const buscando = ref(false)

onMounted(async () => {
  auth.fetchMe()
  await Promise.all([items.fetchAll(), items.fetchPendientes()])
})

watchDebounced(
  busqueda,
  async (q: string) => {
    if (!q.trim()) {
      resultados.value = null
      return
    }
    buscando.value = true
    try {
      resultados.value = await items.buscar(q.trim())
    } finally {
      buscando.value = false
    }
  },
  { debounce: 300 },
)

const itemsFiltrados = computed(() =>
  items.items.filter(
    (i) =>
      (filtro.value === 'TODOS' || i.estado === filtro.value) &&
      (filtroEtapa.value === 'TODAS' || i.etapa === filtroEtapa.value),
  ),
)

const badge = {
  NECESITADO: { color: 'gray' as const, label: 'Por comprar' },
  RESERVADO: { color: 'amber' as const, label: 'Reservado 🎁' },
  ADQUIRIDO: { color: 'green' as const, label: 'Lo tenemos' },
}

function acciones(item: Item) {
  const editar = {
    label: 'Editar',
    icon: 'i-heroicons-pencil',
    click: () => {
      itemEditando.value = item
      modalForm.value = true
    },
  }
  const grupos = [[editar]]

  const segundo = []
  // El panel de reservas aparece siempre que haya unidades reservadas,
  // aunque al item todavía le queden otras disponibles.
  if (item.reservas_activas > 0) {
    segundo.push({
      label: `Regalos en camino (${item.reservas_activas})`,
      icon: 'i-heroicons-gift',
      click: () => (itemReservas.value = item),
    })
  }
  if (item.estado !== 'ADQUIRIDO' && item.reservas_activas === 0) {
    segundo.push({
      label: 'Marcar adquirido',
      icon: 'i-heroicons-check-circle',
      click: () => (itemAdquirir.value = item),
    })
  }
  if (segundo.length > 0) grupos.push(segundo)

  if (item.estado === 'ADQUIRIDO') {
    grupos.push([
      {
        label: item.caja ? 'Cambiar caja' : 'Asignar caja',
        icon: 'i-heroicons-archive-box',
        click: () => (itemCaja.value = item),
      },
    ])
  }

  // Con unidades reservadas no se puede eliminar: hay que resolverlas.
  if (item.reservas_activas === 0) {
    grupos.push([
      {
        label: 'Eliminar',
        icon: 'i-heroicons-trash',
        click: () => (itemEliminar.value = item),
      },
    ])
  }

  return grupos
}

async function confirmarEliminar() {
  if (!itemEliminar.value) return
  try {
    await items.eliminar(itemEliminar.value.id)
    toast.add({ title: 'Item eliminado', color: 'green' })
  } catch {
    toast.add({ title: 'No se pudo eliminar', color: 'red' })
  } finally {
    itemEliminar.value = null
  }
}

function salir() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div class="flex items-center gap-3">
        <h2 class="text-xl font-medium text-pink-700 dark:text-pink-200">
          Catálogo
        </h2>
        <UBadge v-if="items.pendientes > 0" color="amber" variant="subtle">
          {{ items.pendientes }} regalo{{ items.pendientes > 1 ? 's' : '' }} en camino
        </UBadge>
      </div>
      <div class="flex items-center gap-2">
        <UButton icon="i-heroicons-gift" @click="modalRegistrar = true">
          Registrar regalo
        </UButton>
        <UButton
          variant="outline"
          icon="i-heroicons-plus"
          @click="itemEditando = null; modalForm = true"
        >
          Nuevo item
        </UButton>
        <UButton
          variant="ghost"
          color="gray"
          icon="i-heroicons-heart"
          to="/admin/regalos"
          aria-label="Ver regalos recibidos"
        />
        <UButton
          variant="ghost"
          color="gray"
          icon="i-heroicons-cog-6-tooth"
          to="/admin/ajustes"
          aria-label="Ajustes"
        />
        <UButton
          variant="ghost"
          color="gray"
          icon="i-heroicons-arrow-right-on-rectangle"
          aria-label="Salir"
          @click="salir"
        />
      </div>
    </div>

    <UInput
      v-model="busqueda"
      icon="i-heroicons-magnifying-glass"
      placeholder="Buscar algo y ver en qué caja está…"
      :loading="buscando"
      aria-label="Buscar items"
    />

    <UCard v-if="resultados !== null">
      <template #header>
        <h3 class="text-sm font-medium">
          {{ resultados.length }} resultado{{ resultados.length === 1 ? '' : 's' }}
        </h3>
      </template>
      <p v-if="resultados.length === 0" class="text-sm text-gray-500 dark:text-gray-400">
        No encontramos nada con «{{ busqueda }}».
      </p>
      <ul v-else class="divide-y divide-pink-100 dark:divide-neutral-800">
        <li
          v-for="r in resultados"
          :key="r.id"
          class="flex flex-wrap items-center justify-between gap-2 py-2"
        >
          <span class="text-sm font-medium">{{ r.nombre }}</span>
          <UBadge color="gray" variant="subtle">
            {{ ETAPA_LABEL[r.etapa] }}
          </UBadge>
          <UBadge
            v-if="r.personas.length > 0"
            color="pink"
            variant="subtle"
          >
            🎁 {{ r.personas.join(', ') }}
          </UBadge>
          <UBadge v-if="r.caja" color="gray" variant="subtle">
            📦 {{ r.caja.etiqueta }}
            <span v-if="r.caja.descripcion" class="ml-1 opacity-75">
              — {{ r.caja.descripcion }}
            </span>
          </UBadge>
          <span v-else class="text-xs text-gray-500 dark:text-gray-400">
            Sin caja asignada
          </span>
        </li>
      </ul>
    </UCard>

    <div class="flex flex-wrap gap-2">
      <UButton
        v-for="f in (['TODOS', 'NECESITADO', 'RESERVADO', 'ADQUIRIDO'] as const)"
        :key="f"
        size="xs"
        :variant="filtro === f ? 'solid' : 'outline'"
        @click="filtro = f"
      >
        {{ f === 'TODOS' ? 'Todos' : badge[f].label }}
      </UButton>
      <USelect
        v-model="filtroEtapa"
        size="xs"
        class="ml-auto w-44"
        aria-label="Filtrar por etapa"
        :options="[
          { value: 'TODAS', label: 'Todas las etapas' },
          ...ETAPAS.map((e) => ({ value: e, label: ETAPA_LABEL[e] })),
        ]"
      />
    </div>

    <div v-if="items.cargando" class="py-10 text-center">
      <UIcon name="i-heroicons-heart" class="h-8 w-8 animate-pulse text-pink-400" />
    </div>

    <UCard v-else-if="itemsFiltrados.length === 0">
      <p class="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
        No hay items aquí todavía. ¡Agregá el primero con "Nuevo item"!
      </p>
    </UCard>

    <div v-else class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <UCard v-for="item in itemsFiltrados" :key="item.id">
        <div class="flex items-start justify-between gap-2">
          <div class="min-w-0">
            <p class="truncate font-medium">{{ item.nombre }}</p>
            <p
              v-if="item.descripcion"
              class="mt-0.5 line-clamp-2 text-sm text-gray-500 dark:text-gray-400"
            >
              {{ item.descripcion }}
            </p>
          </div>
          <UDropdown :items="acciones(item)">
            <UButton
              variant="ghost"
              color="gray"
              icon="i-heroicons-ellipsis-vertical"
              :aria-label="`Acciones para ${item.nombre}`"
            />
          </UDropdown>
        </div>

        <img
          v-if="item.fotos.length > 0"
          :src="item.fotos[0]!.url"
          alt=""
          class="mt-2 h-32 w-full rounded-lg object-cover"
        >

        <div class="mt-3 flex flex-wrap items-center gap-2">
          <UBadge :color="badge[item.estado].color" variant="subtle">
            {{ badge[item.estado].label }}
          </UBadge>
          <UBadge v-if="item.cantidad > 1" color="blue" variant="subtle">
            {{ item.cantidad_recibida }}/{{ item.cantidad }} recibidos
          </UBadge>
          <UBadge v-if="item.prioridad === 'URGENTE'" color="red" variant="subtle">
            {{ PRIORIDAD_LABEL.URGENTE }}
          </UBadge>
          <UBadge v-if="item.rango_precio" color="gray" variant="subtle">
            {{ RANGO_PRECIO_LABEL[item.rango_precio] }}
          </UBadge>
          <UBadge v-if="item.categoria" color="gray" variant="subtle">
            {{ item.categoria.nombre }}
          </UBadge>
          <UBadge v-if="item.etapa !== 'CUALQUIERA'" color="gray" variant="subtle">
            {{ ETAPA_LABEL[item.etapa] }}
          </UBadge>
          <UBadge v-if="item.personas.length > 0" color="pink" variant="subtle">
            🎁 {{ item.personas.join(', ') }}
          </UBadge>
          <UBadge v-if="item.caja" color="gray" variant="subtle">
            📦 {{ item.caja.etiqueta }}
          </UBadge>
          <ULink
            v-if="item.amazon_link"
            :to="item.amazon_link"
            target="_blank"
            class="text-xs text-pink-600 underline dark:text-pink-300"
          >
            Ver en tienda
          </ULink>
        </div>
      </UCard>
    </div>

    <RegistrarRegaloModal
      v-if="modalRegistrar"
      @close="modalRegistrar = false"
      @done="items.fetchAll()"
    />
    <ItemFormModal v-if="modalForm" :item="itemEditando" @close="modalForm = false" />
    <AdquirirModal
      v-if="itemAdquirir"
      :item="itemAdquirir"
      @close="itemAdquirir = null"
    />
    <ReservasModal
      v-if="itemReservas"
      :item="itemReservas"
      @close="itemReservas = null"
    />
    <CajaModal v-if="itemCaja" :item="itemCaja" @close="itemCaja = null" />
    <ConfirmModal
      v-if="itemEliminar"
      titulo="Eliminar item"
      :descripcion="`Se eliminará «${itemEliminar.nombre}» y sus fotos. Esta acción no se puede deshacer.`"
      confirm-label="Eliminar"
      @close="itemEliminar = null"
      @confirm="confirmarEliminar"
    />
  </div>
</template>
