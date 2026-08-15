<script setup lang="ts">
import type { Item, Prioridad, RangoPrecio } from '~/types/api'

const props = defineProps<{ item?: Item | null }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const items = useItemsStore()
const categorias = useCategoriasStore()
const toast = useToast()

const SIN_CATEGORIA = 0

const nombre = ref(props.item?.nombre ?? '')
const descripcion = ref(props.item?.descripcion ?? '')
const amazonLink = ref(props.item?.amazon_link ?? '')
const cantidad = ref(props.item?.cantidad ?? 1)
const prioridad = ref<Prioridad>(props.item?.prioridad ?? 'NORMAL')
const rangoPrecio = ref<RangoPrecio | ''>(props.item?.rango_precio ?? '')
const categoriaId = ref<number>(props.item?.categoria?.id ?? SIN_CATEGORIA)
const nuevaCategoria = ref('')
const creandoCategoria = ref(false)
const guardando = ref(false)
const subiendoFoto = ref(false)
const fileInput = ref<HTMLInputElement>()

const esEdicion = computed(() => !!props.item)

onMounted(() => categorias.fetchAll())

const opcionesCategoria = computed(() => [
  { value: SIN_CATEGORIA, label: 'Sin categoría' },
  ...categorias.categorias.map((c) => ({ value: c.id, label: c.nombre })),
])

async function guardar() {
  guardando.value = true
  try {
    let catId: number | null =
      categoriaId.value === SIN_CATEGORIA ? null : categoriaId.value
    if (creandoCategoria.value && nuevaCategoria.value.trim()) {
      const creada = await categorias.crear(nuevaCategoria.value.trim())
      catId = creada.id
    }
    const body = {
      nombre: nombre.value.trim(),
      descripcion: descripcion.value.trim() || null,
      amazon_link: amazonLink.value.trim() || null,
      cantidad: cantidad.value,
      prioridad: prioridad.value,
      rango_precio: rangoPrecio.value || null,
      categoria_id: catId,
    }
    if (props.item) {
      await items.editar(props.item.id, body)
    } else {
      await items.crear(body)
    }
    emit('saved')
    emit('close')
  } catch (e: unknown) {
    const status = (e as { statusCode?: number }).statusCode
    toast.add({
      title: 'No se pudo guardar',
      description:
        status === 409
          ? 'No podés bajar la cantidad por debajo de lo ya reservado o recibido.'
          : 'Revisá los datos (el link debe ser una URL válida).',
      color: 'red',
    })
  } finally {
    guardando.value = false
  }
}

async function onFotoSeleccionada(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file || !props.item) return
  subiendoFoto.value = true
  try {
    await items.subirFoto(props.item.id, file)
    toast.add({ title: 'Foto subida', color: 'green' })
  } catch {
    toast.add({
      title: 'No se pudo subir la foto',
      description:
        'Solo imágenes jpeg/png/webp de hasta 5 MB (requiere R2 configurado).',
      color: 'red',
    })
  } finally {
    subiendoFoto.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function quitarFoto(fotoId: number) {
  if (!props.item) return
  try {
    await items.eliminarFoto(props.item.id, fotoId)
  } catch {
    toast.add({ title: 'No se pudo eliminar la foto', color: 'red' })
  }
}
</script>

<template>
  <UModal :model-value="true" @update:model-value="emit('close')">
    <UCard>
      <template #header>
        <h3 class="text-lg font-medium">
          {{ esEdicion ? 'Editar item' : 'Nuevo item' }}
        </h3>
      </template>

      <form class="space-y-4" @submit.prevent="guardar">
        <UFormGroup label="Nombre" required>
          <UInput v-model="nombre" required placeholder="Cuna, pañalera, monitor…" />
        </UFormGroup>

        <UFormGroup label="Descripción">
          <UTextarea v-model="descripcion" :rows="2" placeholder="Color, talla, referencia…" />
        </UFormGroup>

        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="¿Cuántos necesitan?">
            <UInput v-model.number="cantidad" type="number" min="1" max="99" />
          </UFormGroup>

          <UFormGroup label="Rango de precio">
            <USelect
              v-model="rangoPrecio"
              :options="[
                { value: '', label: 'Sin indicar' },
                { value: 'BAJO', label: '$ — económico' },
                { value: 'MEDIO', label: '$$ — medio' },
                { value: 'ALTO', label: '$$$ — caro' },
              ]"
            />
          </UFormGroup>
        </div>

        <UFormGroup label="Prioridad">
          <USelect
            v-model="prioridad"
            :options="[
              { value: 'URGENTE', label: 'Urgente — hace falta ya' },
              { value: 'NORMAL', label: 'Normal' },
              { value: 'PUEDE_ESPERAR', label: 'Puede esperar' },
            ]"
          />
        </UFormGroup>

        <UFormGroup label="Categoría">
          <template v-if="!creandoCategoria">
            <USelectMenu
              v-model="categoriaId"
              :options="opcionesCategoria"
              value-attribute="value"
              option-attribute="label"
            />
            <UButton
              variant="link"
              size="xs"
              icon="i-heroicons-plus"
              class="mt-1"
              @click="creandoCategoria = true"
            >
              Crear categoría nueva
            </UButton>
          </template>
          <template v-else>
            <UInput v-model="nuevaCategoria" placeholder="Ropa, higiene, paseo…" />
            <UButton variant="link" size="xs" class="mt-1" @click="creandoCategoria = false">
              Usar una existente
            </UButton>
          </template>
        </UFormGroup>

        <UFormGroup label="Link de Amazon (o tienda)">
          <UInput v-model="amazonLink" type="url" placeholder="https://amazon.com/…" />
        </UFormGroup>

        <div v-if="esEdicion" class="space-y-2">
          <p class="text-sm font-medium">Fotos de referencia</p>
          <div class="flex flex-wrap items-center gap-2">
            <div
              v-for="foto in props.item?.fotos"
              :key="foto.id"
              class="group relative h-16 w-16 overflow-hidden rounded-lg border border-pink-200 dark:border-neutral-800"
            >
              <img :src="foto.url" alt="" class="h-full w-full object-cover">
              <button
                type="button"
                class="absolute inset-0 hidden items-center justify-center bg-black/50 text-white group-hover:flex"
                :aria-label="`Eliminar foto ${foto.id}`"
                @click="quitarFoto(foto.id)"
              >
                <UIcon name="i-heroicons-trash" class="h-5 w-5" />
              </button>
            </div>
            <UButton
              variant="outline"
              size="sm"
              icon="i-heroicons-photo"
              :loading="subiendoFoto"
              @click="fileInput?.click()"
            >
              Agregar foto
            </UButton>
            <input
              ref="fileInput"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              class="hidden"
              @change="onFotoSeleccionada"
            >
          </div>
        </div>
        <p v-else class="text-xs text-gray-500 dark:text-gray-400">
          Las fotos se agregan después de crear el item (al editarlo).
        </p>

        <div class="flex justify-end gap-2">
          <UButton variant="ghost" color="gray" @click="emit('close')">
            Cancelar
          </UButton>
          <UButton type="submit" :loading="guardando">
            {{ esEdicion ? 'Guardar' : 'Crear' }}
          </UButton>
        </div>
      </form>
    </UCard>
  </UModal>
</template>
