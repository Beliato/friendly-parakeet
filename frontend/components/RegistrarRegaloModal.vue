<script setup lang="ts">
import type { Etapa, Item, OrigenRegalo } from '~/types/api'
import { ETAPAS, ETAPA_LABEL } from '~/types/api'

const emit = defineEmits<{ close: []; done: [] }>()

const regalos = useRegalosStore()
const items = useItemsStore()
const toast = useToast()

// Objeto: se elige uno existente o se crea acá mismo. La mayoría de los
// regalos llegan sin haber pasado por el catálogo.
const modoNuevo = ref(false)
const SIN_ITEM = 0
const itemId = ref<number>(SIN_ITEM)
const busquedaItem = ref('')
const nombreNuevo = ref('')
const etapa = ref<Etapa>('CUALQUIERA')

const origen = ref<OrigenRegalo>('REGALO')
const persona = ref('')
const cantidad = ref(1)
const fecha = ref(new Date().toISOString().slice(0, 10))
const nota = ref('')
const guardando = ref(false)

onMounted(async () => {
  await Promise.all([items.fetchAll(), regalos.fetchPersonas()])
})

const itemsFiltrados = computed(() => {
  const q = busquedaItem.value.trim().toLowerCase()
  const lista = q
    ? items.items.filter((i) => i.nombre.toLowerCase().includes(q))
    : items.items
  return lista.slice(0, 50).map((i: Item) => ({
    value: i.id,
    label:
      i.cantidad > 1
        ? `${i.nombre} (${i.cantidad_recibida}/${i.cantidad})`
        : i.nombre,
  }))
})

const sugerencias = computed(() => {
  const q = persona.value.trim().toLowerCase()
  if (!q) return regalos.personas.slice(0, 6)
  return regalos.personas
    .filter((p) => p.toLowerCase().includes(q) && p.toLowerCase() !== q)
    .slice(0, 6)
})

const puedeGuardar = computed(() => {
  const objetoOk = modoNuevo.value
    ? !!nombreNuevo.value.trim()
    : itemId.value !== SIN_ITEM
  const personaOk = origen.value === 'NOSOTROS' || !!persona.value.trim()
  return objetoOk && personaOk
})

async function guardar() {
  if (!puedeGuardar.value) return
  guardando.value = true
  try {
    await regalos.registrar({
      ...(modoNuevo.value
        ? { item_nuevo: { nombre: nombreNuevo.value.trim(), etapa: etapa.value } }
        : { item_id: itemId.value }),
      persona: origen.value === 'REGALO' ? persona.value.trim() : '',
      origen: origen.value,
      cantidad: cantidad.value,
      fecha: fecha.value,
      nota: nota.value.trim() || null,
    })
    toast.add({
      title: '¡Anotado! 🎁',
      description:
        origen.value === 'REGALO'
          ? `Gracias a ${persona.value.trim()} quedó registrado.`
          : 'Quedó registrado como comprado por ustedes.',
      color: 'pink',
    })
    emit('done')
    emit('close')
  } catch {
    toast.add({ title: 'No se pudo registrar', color: 'red' })
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <UModal :model-value="true" @update:model-value="emit('close')">
    <UCard>
      <template #header>
        <h3 class="text-lg font-medium">Registrar un regalo</h3>
        <p class="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
          Anotá qué recibieron y de parte de quién.
        </p>
      </template>

      <form class="space-y-4" @submit.prevent="guardar">
        <UFormGroup label="¿Qué recibieron?" required>
          <template v-if="!modoNuevo">
            <USelectMenu
              v-model="itemId"
              v-model:query="busquedaItem"
              :options="itemsFiltrados"
              value-attribute="value"
              option-attribute="label"
              searchable
              placeholder="Buscá en el catálogo…"
            />
            <UButton
              variant="link"
              size="xs"
              icon="i-heroicons-plus"
              class="mt-1"
              @click="modoNuevo = true"
            >
              No está en la lista, agregarlo
            </UButton>
          </template>
          <template v-else>
            <UInput v-model="nombreNuevo" placeholder="Nombre del objeto" autofocus />
            <USelect
              v-model="etapa"
              class="mt-2"
              :options="ETAPAS.map((e) => ({ value: e, label: ETAPA_LABEL[e] }))"
            />
            <UButton variant="link" size="xs" class="mt-1" @click="modoNuevo = false">
              Elegir uno del catálogo
            </UButton>
          </template>
        </UFormGroup>

        <UFormGroup label="¿De dónde vino?">
          <URadioGroup
            v-model="origen"
            :options="[
              { value: 'REGALO', label: 'Nos lo regalaron' },
              { value: 'NOSOTROS', label: 'Lo compramos nosotros' },
            ]"
          />
        </UFormGroup>

        <UFormGroup v-if="origen === 'REGALO'" label="¿Quién lo regaló?" required>
          <UInput v-model="persona" placeholder="Nombre de la persona" />
          <div v-if="sugerencias.length > 0" class="mt-2 flex flex-wrap gap-1">
            <UButton
              v-for="s in sugerencias"
              :key="s"
              size="xs"
              variant="soft"
              color="pink"
              @click="persona = s"
            >
              {{ s }}
            </UButton>
          </div>
        </UFormGroup>

        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="¿Cuántos?">
            <UInput v-model.number="cantidad" type="number" min="1" max="99" />
          </UFormGroup>
          <UFormGroup label="¿Cuándo?">
            <UInput v-model="fecha" type="date" />
          </UFormGroup>
        </div>

        <UFormGroup label="Nota (opcional)">
          <UTextarea v-model="nota" :rows="2" placeholder="Algo para recordar…" />
        </UFormGroup>

        <div class="flex justify-end gap-2">
          <UButton variant="ghost" color="gray" @click="emit('close')">
            Cancelar
          </UButton>
          <UButton type="submit" :loading="guardando" :disabled="!puedeGuardar">
            Registrar
          </UButton>
        </div>
      </form>
    </UCard>
  </UModal>
</template>
