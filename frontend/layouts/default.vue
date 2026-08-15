<script setup lang="ts">
const config = useConfigStore()
onMounted(() => config.fetch())
</script>

<template>
  <div class="min-h-screen bg-neutral-50 dark:bg-neutral-950">
    <header
      class="border-b border-neutral-200 bg-neutral-100/80 backdrop-blur dark:border-neutral-900 dark:bg-neutral-950/80"
    >
      <div class="mx-auto flex max-w-5xl items-center gap-3 px-4 py-3">
        <img src="/icon.svg" alt="" class="h-9 w-9" aria-hidden="true">
        <h1 class="text-lg font-medium text-pink-800 dark:text-pink-200">
          {{ config.nombreApp }}
        </h1>
        <slot name="header-extra" />
      </div>
    </header>
    <main class="mx-auto max-w-5xl p-4 sm:p-6">
      <slot />
    </main>
  </div>
</template>
