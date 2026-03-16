import { defineConfig } from 'vite'
import mdx from '@mdx-js/rollup'
import react from '@vitejs/plugin-react'
import remarkGfm from 'remark-gfm'

export default defineConfig({
  plugins: [
    mdx({ remarkPlugins: [remarkGfm] }),
    react({ include: /\.(mdx|js|jsx|ts|tsx)$/ }),
  ],
})
