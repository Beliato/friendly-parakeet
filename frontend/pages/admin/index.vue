<script setup lang="ts">
import type { Item } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const auth = useAuthStore()
const items = useItemsStore()
const router = useRouter()
const toast = useToast()

const modalForm = ref(false)
const itemEditando = ref<Item | null>(null)
const itemAdquirir = ref<Item | null>(null)
const itemCaja = ref<Item | null>(null)
const itemEliminar = ref<Item | null>(null)
const itemLiberar = ref<Item | null>(null)
const filtro = ref<'TODOS' | 'NECESITADO' | 'RESERVADO' | 'ADQUIRIDO'>('TODOS')

onMounted(async () => {
  auth.fetchMe()
  await Promise.all([items.fetchAll(), items.fetchPendientes()])
})

const itemsFiltrados = computed(() =>
  filtro.value === 'TODOS'
    ? items.items
    : items.items.filter((i) => i.estado === filtro.value),
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
  const eliminar = {
    label: 'Eliminar',
    icon: 'i-heroicons-trash',
    click: () => (itemEliminar.value = item),
  }
  if (item.estado === 'NECESITADO') {
    return [
      [editar],
      [
        {
          label: 'Marcar adquirido',
          icon: 'i-heroicons-check-circle',
          click: () => (itemAdquirir.value = item),
        },
      ],
      [eliminar],
    ]
  }
  if (item.estado === 'RESERVADO') {
    return [
      [editar],
      [
        {
          label: 'Regalo recibido',
          icon: 'i-heroicons-gift',
          click: () => (itemAdquirir.value = item),
        },
        {
          label: 'Liberar reserva',
          icon: 'i-heroicons-arrow-uturn-left',
          click: () => (itemLiberar.value = item),
        },
      ],
    ]
  }
  return [
    [editar],
    [
      {
        label: item.caja ? 'Cambiar caja' : 'Asignar caja',
        icon: 'i-heroicons-archive-box',
        click: () => (itemCaja.value = item),
      },
    ],
    [eliminar],
  ]
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

async function confirmarLiberar() {
  if (!itemLiberar.value) return
  try {
    await items.liberarReserva(itemLiberar.value.id)
    toast.add({ title: 'Reserva liberada — el item vuelve a la lista', color: 'green' })
  } catch {
    toast.add({ title: 'No se pudo liberar la reserva', color: 'red' })
  } finally {
    itemLiberar.value = null
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
        <UButton
          icon="i-heroicons-plus"
          @click="itemEditando = null; modalForm = true"
        >
          Nuevo item
        </UButton>
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
    </div>

    <div v-if="items.cargando" class="py-10 text-center">
      <UIcon name="i-heroicons-heart" class="h-8 w-8 animate-pulse text-pink-400" />
    </div>

    <UCard v-else-if="itemsFiltrados.length === 0">
      <p class="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
        No hay items aquí todavía. ¡Agrega el primero con "Nuevo item"!
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
          <UBadge
            v-if="item.estado === 'ADQUIRIDO' && item.origen_adquisicion === 'REGALO'"
            color="pink"
            variant="subtle"
          >
            🎁 {{ item.gifter_name || 'Regalo' }}
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

    <ItemFormModal
      v-if="modalForm"
      :item="itemEditando"
      @close="modalForm = false"
    />
    <AdquirirModal
      v-if="itemAdquirir"
      :item="itemAdquirir"
      @close="itemAdquirir = null"
    />
    <CajaModal
      v-if="itemCaja"
      :item="itemCaja"
      @close="itemCaja = null"
    />
    <ConfirmModal
      v-if="itemEliminar"
      titulo="Eliminar item"
      :descripcion="`Se eliminará «${itemEliminar.nombre}» y sus fotos. Esta acción no se puede deshacer.`"
      confirm-label="Eliminar"
      @close="itemEliminar = null"
      @confirm="confirmarEliminar"
    />
    <ConfirmModal
      v-if="itemLiberar"
      titulo="Liberar reserva"
      :descripcion="`«${itemLiberar.nombre}» volverá a estar disponible en la wishlist. La persona que lo reservó NO será notificada y su nombre seguirá oculto — la sorpresa se mantiene.`"
      confirm-label="Liberar"
      color="pink"
      @close="itemLiberar = null"
      @confirm="confirmarLiberar"
    />
  </div>
</template>
