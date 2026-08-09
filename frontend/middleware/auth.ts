export default defineNuxtRouteMiddleware(() => {
  const auth = useAuthStore()
  if (import.meta.client && !auth.token) {
    auth.init()
  }
  if (!auth.autenticado) {
    return navigateTo('/login')
  }
})
