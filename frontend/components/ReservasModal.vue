<script setup lang="ts">
import type { Item, ReservaAdmin } from '~/types/api'

const props = defineProps<{ item: Item }>()
const emit = defineEmits<{ close: []; done: [] }>()

const items = useItemsStore()
const toast = useToast()

const reservas = ref<ReservaAdmin[]>([])
const cargando = ref(true)
const trabajando = ref<number | null>(null)
const confirmandoLiberar = ref<ReservaAdmin | null>(null)

const DIAS_VIEJA = 60

onMounted(cargar)

async function cargar() {
  cargando.value = true
  try {
    reservas.value = await items.fetchReservas(props.item.id)
  } finally {
    cargando.value = false
  }
}

function antiguedad(dias: number): string {
  if (dias === 0) return 'hoy'
  if (dias === 1) return 'ayer'
  if (dias < 30) return `hace ${dias} días`
  const meses = Math.floor(dias / 30)
  return meses === 1 ? 'hace 1 mes' : `hace ${meses} meses`
}

async function recibir(reserva: ReservaAdmin) {
  trabajando.value = reserva.id
  try {
    const revelada = await items.recibirUnidad(props.item.id, reserva.id)
    toast.add({
      title: '¡Sorpresa revelada! 🎁',
      description: revelada.mensaje
        ? `De ${revelada.nombre}: «${revelada.mensaje}»`
        : `Este regalo era de: ${revelada.nombre}`,
      color: 'pink',
      timeout: 10000,
    })
    await cargar()
    emit('done')
    if (reservas.value.length === 0) emit('close')
  } catch {
    toast.add({ title: 'No se pudo marcar como recibido', color: 'red' })
  } finally {
    trabajando.value = null
  }
}

async function liberar(reserva: ReservaAdmin) {
  trabajando.value = reserva.id
  try {
    await items.liberarUnidad(props.item.id, reserva.id)
    toast.add({ title: 'Unidad liberada — vuelve a la lista', color: 'green' })
    await cargar()
    emit('done')
    if (reservas.value.length === 0) emit('close')
  } catch {
    toast.add({ title: 'No se pudo liberar', color: 'red' })
  } finally {
    trabajando.value = null
    confirmandoLiberar.value = null
  }
}
</script>

<template>
  <UModal :model-value="true" @update:model-value="emit('close')">
    <UCard>
      <template #header>
        <h3 class="text-lg font-medium">Regalos en camino</h3>
        <p class="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
          {{ props.item.nombre }}
        </p>
      </template>

      <div class="space-y-4">
        <UAlert
          color="pink"
          variant="subtle"
          icon="i-heroicons-sparkles"
          title="Los nombres siguen ocultos"
          description="Se revelan uno por uno, recién cuando marcás cada regalo como recibido."
        />

        <div v-if="cargando" class="py-6 text-center">
          <UIcon name="i-heroicons-heart" class="h-6 w-6 animate-pulse text-pink-400" />
        </div>

        <p
          v-else-if="reservas.length === 0"
          class="py-4 text-center text-sm text-gray-500 dark:text-gray-400"
        >
          No hay reservas activas para este item.
        </p>

        <ul v-else class="space-y-2">
          <li
            v-for="reserva in reservas"
            :key="reserva.id"
            class="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-pink-200 p-3 dark:border-neutral-800"
          >
            <div class="flex items-center gap-2">
              <span class="text-sm">🎁 Unidad {{ reserva.unidad }}</span>
              <UBadge
                :color="reserva.dias_desde_reserva > DIAS_VIEJA ? 'amber' : 'gray'"
                variant="subtle"
                size="xs"
              >
                {{ antiguedad(reserva.dias_desde_reserva) }}
              </UBadge>
            </div>
            <div class="flex gap-1">
              <UButton
                size="xs"
                icon="i-heroicons-gift"
                :loading="trabajando === reserva.id"
                @click="recibir(reserva)"
              >
                Recibido
              </UButton>
              <UButton
                size="xs"
                variant="ghost"
                color="gray"
                :loading="trabajando === reserva.id"
                @click="confirmandoLiberar = reserva"
              >
                Liberar
              </UButton>
            </div>
          </li>
        </ul>

        <p
          v-if="reservas.some((r) => r.dias_desde_reserva > DIAS_VIEJA)"
          class="text-xs text-gray-500 dark:text-gray-400"
        >
          Hay reservas de hace más de dos meses. Si el regalo nunca llegó,
          podés liberar esa unidad para que vuelva a la lista.
        </p>

        <div class="flex justify-end">
          <UButton variant="ghost" color="gray" @click="emit('close')">
            Cerrar
          </UButton>
        </div>
      </div>
    </UCard>
  </UModal>

  <ConfirmModal
    v-if="confirmandoLiberar"
    titulo="Liberar esta unidad"
    descripcion="La unidad vuelve a estar disponible en la wishlist. La persona que la reservó NO será notificada y su nombre seguirá oculto — la sorpresa se mantiene."
    confirm-label="Liberar"
    color="pink"
    @close="confirmandoLiberar = null"
    @confirm="liberar(confirmandoLiberar)"
  />
</template>
