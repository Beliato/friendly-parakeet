<script setup lang="ts">
const props = defineProps<{
  titulo: string
  descripcion: string
  confirmLabel?: string
  color?: 'red' | 'pink'
}>()
const emit = defineEmits<{ close: []; confirm: [] }>()

const trabajando = ref(false)

async function confirmar() {
  trabajando.value = true
  emit('confirm')
}
</script>

<template>
  <UModal :model-value="true" @update:model-value="emit('close')">
    <UCard>
      <template #header>
        <h3 class="text-lg font-medium">{{ props.titulo }}</h3>
      </template>
      <div class="space-y-4">
        <p class="text-sm text-gray-600 dark:text-gray-300">
          {{ props.descripcion }}
        </p>
        <div class="flex justify-end gap-2">
          <UButton variant="ghost" color="gray" @click="emit('close')">
            Cancelar
          </UButton>
          <UButton
            :color="props.color ?? 'red'"
            :loading="trabajando"
            @click="confirmar"
          >
            {{ props.confirmLabel ?? 'Confirmar' }}
          </UButton>
        </div>
      </div>
    </UCard>
  </UModal>
</template>
