<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const auth = useAuthStore()
const router = useRouter()

onMounted(() => auth.fetchMe())

function salir() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-medium text-pink-700 dark:text-pink-200">
        Catálogo
      </h2>
      <UButton variant="ghost" color="gray" icon="i-heroicons-arrow-right-on-rectangle" @click="salir">
        Salir
      </UButton>
    </div>
    <UCard>
      <p class="text-sm text-gray-600 dark:text-gray-300">
        El listado de items llega en la fase 9. Sesión activa como
        <span class="font-medium">{{ auth.admin?.email }}</span>.
      </p>
    </UCard>
  </div>
</template>
