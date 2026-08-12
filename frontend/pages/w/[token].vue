<script setup lang="ts">
import type { ItemPublico, WishlistPublica } from '~/types/api'

definePageMeta({ layout: false })

const route = useRoute()
const runtime = useRuntimeConfig()
const toast = useToast()
const { reservas, cargar, guardar, olvidar } = useReservasLocales()

const token = computed(() => String(route.params.token))
const nombreApp = ref('Julia en Camino')
const items = ref<ItemPublico[]>([])
const cargando = ref(true)
const error = ref(false)

const itemReservando = ref<ItemPublico | null>(null)
const nombreInvitado = ref('')
const enviando = ref(false)

// Items reservados desde este navegador ya no vienen en la lista pública,
// así que se muestran aparte para poder deshacerlos.
const misReservas = computed(() => Object.keys(reservas.value).map(Number))

async function fetchWishlist() {
  cargando.value = true
  try {
    const data = await $fetch<WishlistPublica>(`/w/${token.value}`, {
      baseURL: runtime.public.apiBase,
    })
    nombreApp.value = data.nombre_app
    items.value = data.items
    error.value = false
  } catch {
    error.value = true
  } finally {
    cargando.value = false
  }
}

onMounted(() => {
  cargar()
  fetchWishlist()
})

useHead(() => ({ title: nombreApp.value }))

async function reservar() {
  if (!itemReservando.value || !nombreInvitado.value.trim()) return
  enviando.value = true
  const item = itemReservando.value
  try {
    const data = await $fetch<{ token_deshacer: string }>(
      `/w/${token.value}/items/${item.id}/reservar`,
      {
        method: 'POST',
        baseURL: runtime.public.apiBase,
        body: { nombre: nombreInvitado.value.trim() },
      },
    )
    guardar(item.id, data.token_deshacer)
    items.value = items.value.filter((i) => i.id !== item.id)
    itemReservando.value = null
    nombreInvitado.value = ''
    toast.add({
      title: '¡Gracias! 🎁',
      description: `Anotamos que vos traés «${item.nombre}». Tu nombre queda en secreto hasta que lo reciban.`,
      color: 'pink',
      timeout: 7000,
    })
  } catch (e: unknown) {
    const status = (e as { statusCode?: number }).statusCode
    toast.add({
      title: status === 409 ? 'Alguien se adelantó' : 'No se pudo reservar',
      description:
        status === 409
          ? 'Otra persona ya reservó este regalo. Elegí otro de la lista.'
          : 'Intentá de nuevo en un momento.',
      color: 'red',
    })
    if (status === 409) await fetchWishlist()
  } finally {
    enviando.value = false
  }
}

async function deshacer(itemId: number) {
  const tokenDeshacer = reservas.value[itemId]
  if (!tokenDeshacer) return
  try {
    await $fetch(`/w/reservas/${tokenDeshacer}/deshacer`, {
      method: 'POST',
      baseURL: runtime.public.apiBase,
    })
    olvidar(itemId)
    await fetchWishlist()
    toast.add({ title: 'Reserva liberada', color: 'green' })
  } catch {
    olvidar(itemId)
    toast.add({
      title: 'Esa reserva ya no está activa',
      color: 'amber',
    })
    await fetchWishlist()
  }
}
</script>

<template>
  <div class="min-h-screen bg-pink-100 dark:bg-neutral-950">
    <header
      class="border-b border-pink-200 bg-pink-50/80 backdrop-blur dark:border-neutral-900 dark:bg-neutral-950/80"
    >
      <div class="mx-auto flex max-w-5xl items-center gap-3 px-4 py-4">
        <img src="/icon.svg" alt="" class="h-10 w-10" aria-hidden="true">
        <div>
          <h1 class="text-lg font-medium text-pink-700 dark:text-pink-200">
            {{ nombreApp }}
          </h1>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            Lista de regalos
          </p>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-5xl p-4 sm:p-6">
      <div v-if="cargando" class="py-20 text-center">
        <UIcon name="i-heroicons-heart" class="h-8 w-8 animate-pulse text-pink-400" />
      </div>

      <UCard v-else-if="error">
        <p class="py-6 text-center text-sm text-gray-600 dark:text-gray-300">
          Este link no es válido o ya no está disponible.
        </p>
      </UCard>

      <template v-else>
        <p class="mb-4 text-sm text-gray-600 dark:text-gray-300">
          Si querés regalar algo de esta lista, tocá «Yo lo regalo» y escribí
          tu nombre. El item desaparece para que nadie lo repita, y tu nombre
          queda en secreto hasta que reciban el regalo.
        </p>

        <div v-if="misReservas.length > 0" class="mb-6">
          <h2 class="mb-2 text-sm font-medium text-pink-700 dark:text-pink-200">
            Lo que vas a regalar
          </h2>
          <div class="flex flex-wrap gap-2">
            <UCard
              v-for="itemId in misReservas"
              :key="itemId"
              class="flex-1 sm:max-w-xs"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm">🎁 Regalo reservado</span>
                <UButton
                  size="xs"
                  variant="ghost"
                  color="gray"
                  @click="deshacer(itemId)"
                >
                  Ya no puedo
                </UButton>
              </div>
            </UCard>
          </div>
        </div>

        <UCard v-if="items.length === 0">
          <p class="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
            Por ahora no queda nada por regalar. ¡Gracias! 💕
          </p>
        </UCard>

        <div v-else class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <UCard v-for="item in items" :key="item.id">
            <img
              v-if="item.fotos.length > 0"
              :src="item.fotos[0]!.url"
              alt=""
              class="mb-3 h-40 w-full rounded-lg object-cover"
            >
            <p class="font-medium">{{ item.nombre }}</p>
            <p
              v-if="item.descripcion"
              class="mt-1 text-sm text-gray-500 dark:text-gray-400"
            >
              {{ item.descripcion }}
            </p>
            <div class="mt-3 flex items-center gap-2">
              <UButton size="sm" @click="itemReservando = item">
                Yo lo regalo
              </UButton>
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
      </template>
    </main>

    <UModal
      v-if="itemReservando"
      :model-value="true"
      @update:model-value="itemReservando = null"
    >
      <UCard>
        <template #header>
          <h3 class="text-lg font-medium">Vas a regalar</h3>
        </template>
        <form class="space-y-4" @submit.prevent="reservar">
          <p class="text-sm text-gray-600 dark:text-gray-300">
            <span class="font-medium">{{ itemReservando.nombre }}</span>
          </p>
          <UFormGroup label="Tu nombre" required>
            <UInput
              v-model="nombreInvitado"
              required
              autofocus
              placeholder="¿Cómo te llamás?"
            />
          </UFormGroup>
          <UAlert
            color="pink"
            variant="subtle"
            icon="i-heroicons-sparkles"
            title="Tu nombre queda en secreto"
            description="No lo verán hasta que marquen el regalo como recibido."
          />
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" color="gray" @click="itemReservando = null">
              Cancelar
            </UButton>
            <UButton type="submit" :loading="enviando">
              Confirmar
            </UButton>
          </div>
        </form>
      </UCard>
    </UModal>
  </div>
</template>
