<script setup lang="ts">
const auth = useAuthStore()
const router = useRouter()

onMounted(() => {
  auth.init()
  router.replace(auth.autenticado ? '/admin' : '/login')
})
</script>

<template>
  <div class="flex items-center justify-center py-20">
    <UIcon name="i-heroicons-heart" class="h-8 w-8 animate-pulse text-pink-400" />
  </div>
</template>
