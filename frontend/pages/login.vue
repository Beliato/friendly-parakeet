<script setup lang="ts">
const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const cargando = ref(false)

onMounted(() => {
  auth.init()
  if (auth.autenticado) router.replace('/admin')
})

async function entrar() {
  error.value = ''
  cargando.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/admin')
  } catch {
    error.value = 'Email o contraseña incorrectos'
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <div class="mx-auto mt-10 max-w-sm sm:mt-20">
    <UCard>
      <template #header>
        <h2 class="text-center text-xl font-medium text-pink-800 dark:text-pink-200">
          Iniciar sesión
        </h2>
      </template>

      <form class="space-y-4" @submit.prevent="entrar">
        <UFormGroup label="Email" name="email">
          <UInput
            v-model="email"
            type="email"
            required
            autocomplete="email"
            placeholder="pareja@ejemplo.com"
          />
        </UFormGroup>

        <UFormGroup label="Contraseña" name="password">
          <UInput
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
          />
        </UFormGroup>

        <UAlert
          v-if="error"
          color="red"
          variant="subtle"
          :title="error"
          role="alert"
        />

        <UButton type="submit" block :loading="cargando">
          Entrar
        </UButton>
      </form>
    </UCard>
  </div>
</template>
