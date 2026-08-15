// El módulo virtual de vite-plugin-pwa no resuelve dentro del entorno de
// Vitest, así que se excluye al correr los tests.
const enTests = !!process.env.VITEST

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  modules: [
    '@nuxt/ui',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    '@nuxt/eslint',
    ...(enTests ? [] : ['@vite-pwa/nuxt']),
  ],

  pwa: {
    registerType: 'autoUpdate',
    manifest: {
      name: 'Julia en Camino',
      short_name: 'Julia',
      description: 'Catálogo y wishlist para la llegada de Julia',
      theme_color: '#c594aa',
      background_color: '#ffe5f0',
      display: 'standalone',
      start_url: '/',
      lang: 'es',
      icons: [
        { src: '/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any maskable' },
        { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
      ],
    },
    workbox: {
      navigateFallback: null,
      globPatterns: ['**/*.{js,css,html,svg,png,ico,woff2}'],
    },
    devOptions: { enabled: false },
  },

  components: {
    dirs: [{ path: '~/components', pathPrefix: false }],
  },

  app: {
    head: {
      htmlAttrs: { lang: 'es' },
      meta: [
        { name: 'description', content: 'Julia en Camino — catálogo y wishlist para bebé' },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/icon.svg' },
        { rel: 'apple-touch-icon', sizes: '180x180', href: '/apple-touch-icon.png' },
      ],
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
