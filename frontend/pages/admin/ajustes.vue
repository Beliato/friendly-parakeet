<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const config = useConfigStore()
const toast = useToast()

const shareToken = ref('')
const nombre = ref('')
const guardando = ref(false)
const copiado = ref(false)

const shareUrl = computed(() =>
  shareToken.value ? `${location.origin}/w/${shareToken.value}` : '',
)

onMounted(async () => {
  await config.fetch()
  nombre.value = config.nombreApp
  const api = useApi()
  const data = await api<{ share_token: string }>('/wishlist/link')
  shareToken.value = data.share_token
})

async function copiarLink() {
  await navigator.clipboard.writeText(shareUrl.value)
  copiado.value = true
  setTimeout(() => (copiado.value = false), 2000)
}

async function guardarNombre() {
  guardando.value = true
  try {
    const api = useApi()
    const data = await api<{ nombre_app: string }>('/config', {
      method: 'PATCH',
      body: { nombre_app: nombre.value.trim() },
    })
    config.setNombre(data.nombre_app)
    toast.add({ title: 'Nombre actualizado', color: 'green' })
  } catch {
    toast.add({ title: 'No se pudo actualizar el nombre', color: 'red' })
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center gap-2">
      <UButton
        variant="ghost"
        color="gray"
        icon="i-heroicons-arrow-left"
        to="/admin"
        aria-label="Volver al catálogo"
      />
      <h2 class="text-xl font-medium text-pink-700 dark:text-pink-200">
        Ajustes
      </h2>
    </div>

    <UCard>
      <template #header>
        <h3 class="font-medium">Compartir la wishlist</h3>
      </template>
      <div class="space-y-3">
        <p class="text-sm text-gray-600 dark:text-gray-300">
          Comparte este link con familiares y amigos. Verán solo los items
          por comprar y podrán reservar qué regalar — sin crear cuenta.
        </p>
        <div class="flex gap-2">
          <UInput :model-value="shareUrl" readonly class="flex-1" aria-label="Link de la wishlist" />
          <UButton
            :icon="copiado ? 'i-heroicons-check' : 'i-heroicons-clipboard'"
            :color="copiado ? 'green' : 'pink'"
            @click="copiarLink"
          >
            {{ copiado ? 'Copiado' : 'Copiar' }}
          </UButton>
        </div>
        <p class="text-xs text-gray-500 dark:text-gray-400">
          Cualquiera con el link puede ver y reservar — compártelo solo con
          el círculo cercano.
        </p>
      </div>
    </UCard>

    <UCard>
      <template #header>
        <h3 class="font-medium">Nombre de la app</h3>
      </template>
      <form class="flex gap-2" @submit.prevent="guardarNombre">
        <UInput v-model="nombre" required class="flex-1" aria-label="Nombre de la app" />
        <UButton type="submit" :loading="guardando">Guardar</UButton>
      </form>
    </UCard>
  </div>
</template>
