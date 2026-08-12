<script setup lang="ts">
import type { Item } from '~/types/api'

const props = defineProps<{ item: Item }>()
const emit = defineEmits<{ close: []; done: [] }>()

const items = useItemsStore()
const toast = useToast()

const esReservado = computed(() => props.item.estado === 'RESERVADO')
const origen = ref<'NOSOTROS' | 'REGALO'>(esReservado.value ? 'REGALO' : 'NOSOTROS')
const gifterName = ref('')
const guardando = ref(false)

async function confirmar() {
  guardando.value = true
  try {
    const item = await items.adquirir(
      props.item.id,
      origen.value,
      origen.value === 'REGALO' ? gifterName.value.trim() || null : null,
    )
    if (esReservado.value && item.gifter_name) {
      toast.add({
        title: `¡Sorpresa revelada! 🎁`,
        description: `Este regalo era de: ${item.gifter_name}`,
        color: 'pink',
        timeout: 8000,
      })
    }
    emit('done')
    emit('close')
  } catch {
    toast.add({ title: 'No se pudo marcar como adquirido', color: 'red' })
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <UModal :model-value="true" @update:model-value="emit('close')">
    <UCard>
      <template #header>
        <h3 class="text-lg font-medium">
          {{ esReservado ? 'Marcar regalo como recibido' : 'Marcar como adquirido' }}
        </h3>
      </template>

      <div class="space-y-4">
        <p class="text-sm text-gray-600 dark:text-gray-300">
          <span class="font-medium">{{ props.item.nombre }}</span>
        </p>

        <template v-if="esReservado">
          <UAlert
            color="pink"
            variant="subtle"
            icon="i-heroicons-gift"
            title="Al confirmar se revelará quién lo reservó"
            description="El nombre estuvo oculto hasta ahora para mantener la sorpresa."
          />
        </template>

        <template v-else>
          <UFormGroup label="¿Cómo lo obtuvieron?">
            <URadioGroup
              v-model="origen"
              :options="[
                { value: 'NOSOTROS', label: 'Lo compramos nosotros' },
                { value: 'REGALO', label: 'Fue un regalo' },
              ]"
            />
          </UFormGroup>

          <UFormGroup v-if="origen === 'REGALO'" label="¿Quién lo regaló?">
            <UInput v-model="gifterName" placeholder="Nombre de la persona" />
          </UFormGroup>
        </template>

        <div class="flex justify-end gap-2">
          <UButton variant="ghost" color="gray" @click="emit('close')">
            Cancelar
          </UButton>
          <UButton :loading="guardando" @click="confirmar">
            Confirmar
          </UButton>
        </div>
      </div>
    </UCard>
  </UModal>
</template>
