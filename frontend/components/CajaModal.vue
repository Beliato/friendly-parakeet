<script setup lang="ts">
import type { Item } from '~/types/api'

const props = defineProps<{ item: Item }>()
const emit = defineEmits<{ close: []; done: [] }>()

const items = useItemsStore()
const cajas = useCajasStore()
const toast = useToast()

const SIN_CAJA = 0
const cajaId = ref<number>(props.item.caja?.id ?? SIN_CAJA)
const creandoNueva = ref(false)
const nuevaEtiqueta = ref('')
const nuevaDescripcion = ref('')
const guardando = ref(false)

onMounted(() => cajas.fetchAll())

const opciones = computed(() => [
  { value: SIN_CAJA, label: 'Sin caja' },
  ...cajas.cajas.map((c) => ({
    value: c.id,
    label: c.descripcion ? `${c.etiqueta} — ${c.descripcion}` : c.etiqueta,
  })),
])

async function guardar() {
  guardando.value = true
  try {
    let id: number | null = cajaId.value === SIN_CAJA ? null : cajaId.value
    if (creandoNueva.value && nuevaEtiqueta.value.trim()) {
      const caja = await cajas.crear(
        nuevaEtiqueta.value.trim(),
        nuevaDescripcion.value.trim() || null,
      )
      id = caja.id
    }
    await items.asignarCaja(props.item.id, id)
    emit('done')
    emit('close')
  } catch {
    toast.add({
      title: 'No se pudo asignar la caja',
      description: '¿La etiqueta ya existe?',
      color: 'red',
    })
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <UModal :model-value="true" @update:model-value="emit('close')">
    <UCard>
      <template #header>
        <h3 class="text-lg font-medium">Caja de almacenamiento</h3>
      </template>

      <div class="space-y-4">
        <p class="text-sm text-gray-600 dark:text-gray-300">
          ¿Dónde van a guardar
          <span class="font-medium">{{ props.item.nombre }}</span>?
        </p>

        <template v-if="!creandoNueva">
          <UFormGroup label="Caja existente">
            <USelectMenu
              v-model="cajaId"
              :options="opciones"
              value-attribute="value"
              option-attribute="label"
            />
          </UFormGroup>
          <UButton
            variant="link"
            size="sm"
            icon="i-heroicons-plus"
            @click="creandoNueva = true"
          >
            Crear caja nueva
          </UButton>
        </template>

        <template v-else>
          <UFormGroup label="Etiqueta" required>
            <UInput v-model="nuevaEtiqueta" placeholder="Caja A, Ropa 0-3m…" />
          </UFormGroup>
          <UFormGroup label="Ubicación (opcional)">
            <UInput v-model="nuevaDescripcion" placeholder="Closet del cuarto, bajo la cama…" />
          </UFormGroup>
          <UButton variant="link" size="sm" @click="creandoNueva = false">
            Usar una existente
          </UButton>
        </template>

        <div class="flex justify-end gap-2">
          <UButton variant="ghost" color="gray" @click="emit('close')">
            Cancelar
          </UButton>
          <UButton :loading="guardando" @click="guardar">
            Guardar
          </UButton>
        </div>
      </div>
    </UCard>
  </UModal>
</template>
