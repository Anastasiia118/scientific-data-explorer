import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'

// Components are imported automatically by vite-plugin-vuetify (see
// vite.config.ts), so only the ones we use end up in the bundle.
export default createVuetify({
  theme: {
    // Vuetify defaults to 'system' (follows the OS dark mode), but style.css
    // only has light colors so far.
    defaultTheme: 'light',
    themes: {
      // Same values as the --color-* variables in style.css, so Vuetify
      // components match the parts of the app that don't use Vuetify yet.
      light: {
        colors: {
          background: '#f6f7f9',
          surface: '#ffffff',
          primary: '#2563eb',
          success: '#16a34a',
          error: '#dc2626',
        },
      },
    },
  },
})
