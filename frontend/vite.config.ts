import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // Forward API calls to the Django dev server (avoids CORS issues).
      // 127.0.0.1 rather than localhost: Node may resolve localhost to IPv6
      // (::1), while `manage.py runserver` listens on IPv4 only.
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
