import type { Config } from 'tailwindcss'

// Paleta definida en specs/004-pagina-publica/plan.md. Los tonos vienen
// del diseño hecho en Stitch: crema cálido para las superficies y rosa
// vino para los acentos.
//
// Nuxt UI toma `pink` como primary y `neutral` como gray (ver
// app.config.ts), así que todo lo ya construido adopta estos valores solo.
export default <Partial<Config>>{
  theme: {
    extend: {
      colors: {
        pink: {
          50: '#fbf5f4',
          100: '#f7e9e8',
          200: '#ecd2d1',
          300: '#dfb3b3',
          400: '#c98d8e',
          500: '#b06d6e',
          600: '#8c4c4d',
          700: '#743f40',
          800: '#5f3536',
          900: '#4f2e2f',
          950: '#2a1717',
        },
        neutral: {
          50: '#fdf9f0',
          100: '#f7f3ea',
          200: '#ece8df',
          300: '#dddad1',
          400: '#b5afa4',
          500: '#857372',
          600: '#6b5f5e',
          700: '#534343',
          800: '#332b2b',
          900: '#1c1c17',
          950: '#121210',
        },
      },
      fontFamily: {
        // Solo para los títulos de la página pública; el admin sigue con
        // la sans, que se lee mejor en tablas y datos.
        serif: ['"Libre Caslon Text"', 'Georgia', 'serif'],
      },
    },
  },
}
