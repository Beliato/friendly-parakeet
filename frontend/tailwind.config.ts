import type { Config } from 'tailwindcss'

// Paleta definida en specs/001-baby-wishlist/plan.md — sección "Identidad
// visual". Los tonos marcados (dado) vienen de la referencia del usuario.
export default <Partial<Config>>{
  theme: {
    extend: {
      colors: {
        pink: {
          50: '#fff5fa',
          100: '#ffe5f0',
          200: '#fdcae1',
          300: '#f5b3d1',
          400: '#dba3bd',
          500: '#c594aa',
          600: '#a97a8f',
          700: '#8c6274',
          800: '#6f4c5b',
          900: '#523845',
          950: '#3a2731',
        },
        neutral: {
          900: '#131313',
          950: '#050505',
        },
      },
    },
  },
}
