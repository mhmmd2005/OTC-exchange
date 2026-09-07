import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const sourceRoot = fileURLToPath(new URL('./src', import.meta.url))
const liveServiceRoot = fileURLToPath(new URL('./src/services/live', import.meta.url))
const serviceNames = [
  'auth',
  'bank',
  'market',
  'notification',
  'order',
  'security',
  'support',
  'trade',
  'transaction',
  'user',
  'verification',
  'wallet',
] as const

export default defineConfig(({ command }) => ({
  plugins: [vue()],
  resolve: {
    alias: [
      ...(command === 'build'
        ? [
            { find: /^@\/services$/, replacement: `${liveServiceRoot}/index.ts` },
            ...serviceNames.map((name) => ({
              find: new RegExp(`^@/services/${name}\\.service$`),
              replacement: `${liveServiceRoot}/${name}.service.ts`,
            })),
          ]
        : []),
      { find: '@', replacement: sourceRoot },
    ],
  },
  build: {
    target: 'es2020',
    sourcemap: false,
  },
}))
