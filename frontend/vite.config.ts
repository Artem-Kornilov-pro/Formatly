/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Docker Desktop's bind-mount file sharing (particularly on Windows
    // hosts) doesn't reliably forward inotify events into the container, so
    // chokidar's default watcher silently never fires and HMR/reload never
    // happens for files edited from the host. Polling works regardless of
    // how the mount delivers (or fails to deliver) filesystem events.
    watch: {
      usePolling: true,
      interval: 300,
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/setupTests.ts',
  },
})
