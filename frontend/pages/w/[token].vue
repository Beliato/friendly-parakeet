<script setup lang="ts">
import type { ItemPublico, RegaloPublico, WishlistPublica } from '~/types/api'
import { RANGO_PRECIO_LABEL } from '~/types/api'

definePageMeta({ layout: false })

const route = useRoute()
const runtime = useRuntimeConfig()
const toast = useToast()
const { reservas, cargar, guardar, olvidar } = useReservasLocales()

const token = computed(() => String(route.params.token))
const nombreApp = ref('Julia en Camino')
const items = ref<ItemPublico[]>([])
const recibidos = ref<RegaloPublico[]>([])
const cargando = ref(true)
const error = ref(false)

const itemReservando = ref<ItemPublico | null>(null)
const nombreInvitado = ref('')
const mensajeInvitado = ref('')
const enviando = ref(false)
// Se ata en runtime y no como src estático: si el archivo todavía no está
// en public/, Vite fallaría al resolver el import en build.
const ILUSTRACION = '/hero-flores.png'
const ilustracionOk = ref(true)

// Items reservados desde este navegador ya no vienen en la lista pública,
// así que se muestran aparte para poder deshacerlos.
const misReservas = computed(() => Object.keys(reservas.value).map(Number))

/** Agrupa por categoría preservando el orden por prioridad del backend. */
const grupos = computed(() => {
  const mapa = new Map<string, ItemPublico[]>()
  for (const item of items.value) {
    const clave = item.categoria ?? ''
    if (!mapa.has(clave)) mapa.set(clave, [])
    mapa.get(clave)!.push(item)
  }
  // Los items sin categoría van al final.
  return [...mapa.entries()].sort(([a], [b]) => {
    if (a === '') return 1
    if (b === '') return -1
    return a.localeCompare(b)
  })
})

async function fetchWishlist() {
  cargando.value = true
  try {
    const data = await $fetch<WishlistPublica>(`/w/${token.value}`, {
      baseURL: runtime.public.apiBase,
    })
    nombreApp.value = data.nombre_app
    items.value = data.items
    recibidos.value = data.recibidos ?? []
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
    const data = await $fetch<{ token_deshacer: string; unidad: number }>(
      `/w/${token.value}/items/${item.id}/reservar`,
      {
        method: 'POST',
        baseURL: runtime.public.apiBase,
        body: {
          nombre: nombreInvitado.value.trim(),
          mensaje: mensajeInvitado.value.trim() || null,
        },
      },
    )
    guardar(item.id, data.token_deshacer)
    // Con varias unidades el item sigue disponible para otros.
    await fetchWishlist()
    itemReservando.value = null
    nombreInvitado.value = ''
    mensajeInvitado.value = ''
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
          ? 'Ya no quedan unidades de este regalo. Elegí otro de la lista.'
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
  <div class="min-h-screen bg-neutral-50 dark:bg-neutral-950">
    <header class="px-4 pb-8 pt-10 text-center sm:pt-16">
      <img src="/icon.svg" alt="" class="mx-auto h-16 w-16" aria-hidden="true">
      <h1
        class="mt-4 font-serif text-4xl italic text-pink-800 sm:text-5xl dark:text-pink-200"
      >
        {{ nombreApp }}
      </h1>
      <p class="mt-2 text-lg text-neutral-700 dark:text-neutral-300">
        Florece donde estás plantada
      </p>
      <!-- La ilustración es opcional: si el archivo no está, el hero se
           sostiene igual con el ícono y la tipografía. -->
      <img
        v-if="ilustracionOk"
        :src="ILUSTRACION"
        alt=""
        class="mx-auto mt-8 w-full max-w-3xl rounded-2xl object-cover"
        @error="ilustracionOk = false"
      >
      <p class="mt-8 text-2xl tracking-[0.6em] text-pink-400" aria-hidden="true">
        ❀
      </p>
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
        <!-- Muro de agradecimiento: solo lo ya recibido -->
        <section v-if="recibidos.length > 0" class="mb-10">
          <h2
            class="mb-1 text-center font-serif text-2xl text-pink-800 dark:text-pink-200"
          >
            Regalos recibidos
          </h2>
          <p class="mb-5 text-center text-sm text-neutral-600 dark:text-neutral-400">
            Con mucho cariño y gratitud.
          </p>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <UCard v-for="r in recibidos" :key="r.id">
              <div class="flex flex-col items-center text-center">
                <img
                  v-if="r.foto"
                  :src="r.foto"
                  alt=""
                  class="mb-4 h-32 w-32 rounded-full border border-neutral-200 object-cover dark:border-neutral-800"
                >
                <div
                  v-else
                  class="mb-4 flex h-32 w-32 items-center justify-center rounded-full border border-neutral-200 bg-neutral-100 dark:border-neutral-800 dark:bg-neutral-900"
                  aria-hidden="true"
                >
                  <UIcon name="i-heroicons-gift" class="h-10 w-10 text-pink-400" />
                </div>
                <p class="font-serif text-lg">{{ r.item }}</p>
                <p class="mt-1 text-sm italic text-neutral-600 dark:text-neutral-400">
                  de {{ r.persona }}
                </p>
              </div>
            </UCard>
          </div>
        </section>

        <h2
          v-if="items.length > 0"
          class="mb-1 text-center font-serif text-2xl text-pink-800 dark:text-pink-200"
        >
          Lista de deseos
        </h2>
        <p class="mb-4 text-sm text-gray-600 dark:text-gray-300">
          Si querés regalar algo de esta lista, tocá «Yo lo regalo» y escribí
          tu nombre. Se aparta esa unidad para que nadie la repita, y tu
          nombre queda en secreto hasta que reciban el regalo.
        </p>

        <div v-if="misReservas.length > 0" class="mb-6">
          <h2 class="mb-2 text-sm font-medium text-pink-800 dark:text-pink-200">
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

        <section v-for="[categoria, deCategoria] in grupos" :key="categoria" class="mb-6">
          <h2
            v-if="categoria"
            class="mb-2 text-sm font-medium text-pink-800 dark:text-pink-200"
          >
            {{ categoria }}
          </h2>
          <h2
            v-else-if="grupos.length > 1"
            class="mb-2 text-sm font-medium text-gray-500 dark:text-gray-400"
          >
            Otros
          </h2>

          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <UCard v-for="item in deCategoria" :key="item.id">
              <img
                v-if="item.fotos.length > 0"
                :src="item.fotos[0]!.url"
                alt=""
                class="mb-3 h-40 w-full rounded-lg object-cover"
              >
              <div class="flex items-start justify-between gap-2">
                <p class="font-medium">{{ item.nombre }}</p>
                <UBadge
                  v-if="item.prioridad === 'URGENTE'"
                  color="red"
                  variant="subtle"
                  size="xs"
                >
                  Urgente
                </UBadge>
              </div>
              <p
                v-if="item.descripcion"
                class="mt-1 text-sm text-gray-500 dark:text-gray-400"
              >
                {{ item.descripcion }}
              </p>

              <div class="mt-2 flex flex-wrap items-center gap-2">
                <UBadge v-if="item.cantidad > 1" color="blue" variant="subtle" size="xs">
                  Quedan {{ item.disponibles }} de {{ item.cantidad }}
                </UBadge>
                <UBadge v-if="item.rango_precio" color="gray" variant="subtle" size="xs">
                  {{ RANGO_PRECIO_LABEL[item.rango_precio] }}
                </UBadge>
              </div>

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
        </section>
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
            <span v-if="itemReservando.cantidad > 1">
              — reservás una unidad de {{ itemReservando.cantidad }}
            </span>
          </p>
          <UFormGroup label="Tu nombre" required>
            <UInput
              v-model="nombreInvitado"
              required
              autofocus
              placeholder="¿Cómo te llamás?"
            />
          </UFormGroup>
          <UFormGroup label="Mensaje (opcional)">
            <UTextarea
              v-model="mensajeInvitado"
              :rows="2"
              maxlength="500"
              placeholder="Unas palabras para acompañar el regalo…"
            />
          </UFormGroup>
          <UAlert
            color="pink"
            variant="subtle"
            icon="i-heroicons-sparkles"
            title="Tu nombre y tu mensaje quedan en secreto"
            description="No los verán hasta que marquen el regalo como recibido."
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
