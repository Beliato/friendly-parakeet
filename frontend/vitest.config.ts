import { defineVitestConfig } from '@nuxt/test-utils/config'

export default defineVitestConfig({
  test: {
    environment: 'nuxt',
    coverage: {
      provider: 'v8',
      include: ['stores/**', 'composables/**'],
      thresholds: {
        lines: 70,
        functions: 70,
        statements: 70,
        // Más bajo a propósito: los guards `import.meta.client` (localStorage)
        // tienen su rama de servidor inalcanzable en el entorno de test, así
        // que ese porcentaje nunca llega a 70 aunque el código esté cubierto.
        branches: 60,
      },
    },
  },
})
