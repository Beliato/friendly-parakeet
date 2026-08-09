export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  modules: ['@nuxt/ui', '@pinia/nuxt', '@vueuse/nuxt'],

  components: {
    dirs: [{ path: '~/components', pathPrefix: false }],
  },

  app: {
    head: {
      htmlAttrs: { lang: 'es' },
      meta: [
        { name: 'description', content: 'Julia en Camino — catálogo y wishlist para bebé' },
      ],
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/icon.svg' }],
    },
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
    },
  },

  typescript: {
    strict: true,
  },
})
