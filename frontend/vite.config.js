import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// Prints the admin site's address under Vite's Local/Network lines.
// Django admin is reached through Vite's /admin proxy, so it shares port 5173.
const printAdminUrl = () => ({
  name: 'print-admin-url',
  configureServer(server) {
    const printUrls = server.printUrls
    server.printUrls = () => {
      printUrls()
      const urls = server.resolvedUrls
      if (!urls) return
      const green = (s) => `\x1b[32m${s}\x1b[0m`
      const cyan = (s) => `\x1b[36m${s}\x1b[0m`
      const bold = (s) => `\x1b[1m${s}\x1b[0m`
      const admin = (url) => new URL('/admin/', url).toString()
      urls.local.forEach((u) => console.log(`  ${green('➜')}  ${bold('Admin')}:   ${cyan(admin(u))}`))
      urls.network.forEach((u) => console.log(`  ${green('➜')}  ${bold('Admin')}:   ${cyan(admin(u))}  (network)`))
    }
  },
})

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    printAdminUrl(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'apple-touch-icon.png'],
      manifest: {
        name: 'Treadstone',
        short_name: 'Treadstone',
        description: 'Community savings held in gold and silver',
        theme_color: '#FAF8F2',
        background_color: '#FAF8F2',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: 'pwa-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'pwa-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        navigateFallbackDenylist: [/^\/api\//, /^\/admin\//],
        runtimeCaching: [
          {
            // Offline rule: cache GET responses only (balances, history, last price).
            // POSTs (contributions, loans, payouts) are never cached or queued.
            urlPattern: ({ url, request }) => url.pathname.startsWith('/api/') && request.method === 'GET',
            handler: 'NetworkFirst',
            method: 'GET',
            options: {
              cacheName: 'treadstone-api',
              networkTimeoutSeconds: 5,
              expiration: { maxEntries: 100, maxAgeSeconds: 7 * 24 * 60 * 60 },
              cacheableResponse: { statuses: [200] },
            },
          },
        ],
      },
    }),
  ],
  server: {
    // Listen on the Wi-Fi address too, so a phone on the same network can open the app.
    host: true,
    // Django stays on 127.0.0.1; the phone only ever talks to Vite, which forwards these.
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/admin': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/static': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
