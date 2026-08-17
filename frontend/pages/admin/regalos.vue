<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const regalos = useRegalosStore()
const items = useItemsStore()
const toast = useToast()

const vista = ref<'EN_CAMINO' | 'CRONOLOGICA' | 'POR_PERSONA'>('EN_CAMINO')
const recibiendo = ref<number | null>(null)
const soloPendientes = ref(false)
const modalRegistrar = ref(false)

async function cargar() {
  await Promise.all([
    regalos.fetchAll(soloPendientes.value ? { agradecido: false } : {}),
    regalos.fetchPorPersona(),
    items.fetchEnCamino(),
  ])
}

function antiguedad(dias: number): string {
  if (dias === 0) return 'hoy'
  if (dias === 1) return 'ayer'
  if (dias < 30) return `hace ${dias} días`
  const meses = Math.floor(dias / 30)
  return meses === 1 ? 'hace 1 mes' : `hace ${meses} meses`
}

/** Un toque desde la lista: no hay nada que elegir, ya sabemos qué
 *  reserva es. */
async function yaLlego(reserva: { id: number; item_id: number }) {
  recibiendo.value = reserva.id
  try {
    const revelada = await items.recibirUnidad(reserva.item_id, reserva.id)
    toast.add({
      title: '¡Sorpresa revelada! 🎁',
      description: revelada.mensaje
        ? `De ${revelada.nombre}: «${revelada.mensaje}»`
        : `Este regalo era de: ${revelada.nombre}`,
      color: 'pink',
      timeout: 10000,
    })
    await cargar()
  } catch {
    toast.add({ title: 'No se pudo marcar como recibido', color: 'red' })
  } finally {
    recibiendo.value = null
  }
}

async function liberar(reserva: { id: number; item_id: number }) {
  recibiendo.value = reserva.id
  try {
    await items.liberarUnidad(reserva.item_id, reserva.id)
    toast.add({ title: 'Reserva liberada — vuelve a la lista', color: 'green' })
    await cargar()
  } catch {
    toast.add({ title: 'No se pudo liberar', color: 'red' })
  } finally {
    recibiendo.value = null
  }
}

onMounted(cargar)
watch(soloPendientes, cargar)

const totalPendientes = computed(() =>
  regalos.porPersona.reduce((acc, p) => acc + p.pendientes_de_agradecer, 0),
)

async function agradecerTodos(persona: string) {
  const grupo = regalos.porPersona.find((p) => p.persona === persona)
  if (!grupo) return
  try {
    await Promise.all(
      grupo.regalos
        .filter((r) => !r.agradecido)
        .map((r) => regalos.marcarAgradecido(r.id, true)),
    )
    toast.add({ title: `Listo, ya agradeciste a ${persona}`, color: 'green' })
    await cargar()
  } catch {
    toast.add({ title: 'No se pudo actualizar', color: 'red' })
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div class="flex items-center gap-3">
        <UButton
          variant="ghost"
          color="gray"
          icon="i-heroicons-arrow-left"
          to="/admin"
          aria-label="Volver al catálogo"
        />
        <h2 class="text-xl font-medium text-pink-800 dark:text-pink-200">
          Regalos
        </h2>
        <UBadge v-if="totalPendientes > 0" color="amber" variant="subtle">
          {{ totalPendientes }} sin agradecer
        </UBadge>
      </div>
      <UButton icon="i-heroicons-gift" @click="modalRegistrar = true">
        Registrar regalo
      </UButton>
    </div>

    <div class="flex flex-wrap items-center gap-2">
      <UButton
        size="xs"
        :variant="vista === 'EN_CAMINO' ? 'solid' : 'outline'"
        @click="vista = 'EN_CAMINO'"
      >
        En camino{{ items.enCamino.length > 0 ? ` (${items.enCamino.length})` : '' }}
      </UButton>
      <UButton
        size="xs"
        :variant="vista === 'CRONOLOGICA' ? 'solid' : 'outline'"
        @click="vista = 'CRONOLOGICA'"
      >
        Recibidos
      </UButton>
      <UButton
        size="xs"
        :variant="vista === 'POR_PERSONA' ? 'solid' : 'outline'"
        @click="vista = 'POR_PERSONA'"
      >
        Por persona
      </UButton>
      <UCheckbox
        v-if="vista === 'CRONOLOGICA'"
        v-model="soloPendientes"
        label="Solo los que faltan agradecer"
        class="ml-2"
      />
    </div>

    <div v-if="regalos.cargando" class="py-10 text-center">
      <UIcon name="i-heroicons-heart" class="h-8 w-8 animate-pulse text-pink-400" />
    </div>

    <!-- Lo que está por llegar: el momento de "ya me lo dieron" -->
    <template v-else-if="vista === 'EN_CAMINO'">
      <UCard v-if="items.enCamino.length === 0">
        <p class="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
          No hay nada en camino por ahora.
        </p>
      </UCard>
      <ul v-else class="space-y-2">
        <li
          v-for="reserva in items.enCamino"
          :key="reserva.id"
          class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900"
        >
          <div class="min-w-0">
            <p class="font-medium">
              {{ reserva.item_nombre }}
              <span
                v-if="reserva.total_unidades > 1"
                class="text-sm text-gray-500"
              >
                — unidad {{ reserva.unidad }} de {{ reserva.total_unidades }}
              </span>
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              Reservado {{ antiguedad(reserva.dias_desde_reserva) }}
            </p>
          </div>
          <div class="flex gap-2">
            <UButton
              icon="i-heroicons-gift"
              :loading="recibiendo === reserva.id"
              @click="yaLlego(reserva)"
            >
              Ya llegó
            </UButton>
            <UButton
              variant="ghost"
              color="gray"
              size="sm"
              :loading="recibiendo === reserva.id"
              @click="liberar(reserva)"
            >
              Liberar
            </UButton>
          </div>
        </li>
      </ul>
      <p class="mt-3 text-xs text-gray-500 dark:text-gray-400">
        Los nombres siguen ocultos: se revelan al tocar «Ya llegó».
      </p>
    </template>

    <!-- Vista cronológica -->
    <template v-else-if="vista === 'CRONOLOGICA'">
      <UCard v-if="regalos.regalos.length === 0">
        <p class="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
          {{
            soloPendientes
              ? '¡No queda nadie por agradecer! 💕'
              : 'Todavía no registraron ningún regalo.'
          }}
        </p>
      </UCard>
      <div v-else class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <RegaloCard
          v-for="regalo in regalos.regalos"
          :key="regalo.id"
          :regalo="regalo"
          @cambio="cargar"
        />
      </div>
    </template>

    <!-- Vista por persona: para agradecer sin olvidarse de nadie -->
    <template v-else>
      <UCard v-if="regalos.porPersona.length === 0">
        <p class="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
          Todavía no hay regalos de nadie.
        </p>
      </UCard>
      <UCard v-for="grupo in regalos.porPersona" :key="grupo.persona" class="mb-3">
        <template #header>
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <h3 class="font-medium">{{ grupo.persona }}</h3>
              <UBadge color="gray" variant="subtle" size="xs">
                {{ grupo.total_regalos }}
                regalo{{ grupo.total_regalos > 1 ? 's' : '' }}
              </UBadge>
              <UBadge
                v-if="grupo.pendientes_de_agradecer > 0"
                color="amber"
                variant="subtle"
                size="xs"
              >
                {{ grupo.pendientes_de_agradecer }} sin agradecer
              </UBadge>
            </div>
            <UButton
              v-if="grupo.pendientes_de_agradecer > 0"
              size="xs"
              @click="agradecerTodos(grupo.persona)"
            >
              Ya le agradecí todo
            </UButton>
          </div>
        </template>

        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <RegaloCard
            v-for="regalo in grupo.regalos"
            :key="regalo.id"
            :regalo="regalo"
            :mostrar-persona="false"
            @cambio="cargar"
          />
        </div>
      </UCard>
    </template>

    <RegistrarRegaloModal
      v-if="modalRegistrar"
      @close="modalRegistrar = false"
      @done="cargar"
    />
  </div>
</template>
