import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import type { Plugin } from 'vite'

// Strips version specifiers from Shadcn/Lovable-style imports:
// "@radix-ui/react-slot@1.1.2" → "@radix-ui/react-slot"
// "cmdk@1.1.1"                  → "cmdk"
function stripVersionedImports(): Plugin {
  return {
    name: 'strip-versioned-imports',
    transform(code, id) {
      if (!id.endsWith('.tsx') && !id.endsWith('.ts')) return
      return {
        code: code.replace(
          /(from\s+['"])((?:@[^/'"]+\/[^@'"]+|[^@'"]+))@[\d][^'"]*(['"])/g,
          '$1$2$3'
        ),
        map: null,
      }
    },
  }
}

export default defineConfig({
  plugins: [stripVersionedImports(), react()],
  resolve: {
    alias: {
      '@': new URL('./src', import.meta.url).pathname,
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
  },
})
