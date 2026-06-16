import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

import fs from 'node:fs'
import path from 'node:path'

// 读取版本号的函数（Node.js 环境）
function getAppVersion() {
  try {
    const version = fs.readFileSync(path.resolve(__dirname, '../VERSION'), 'utf-8').trim()
    // 注意：define 要求值必须是 JSON 字符串化的格式
    return JSON.stringify(version)
  } catch (e) {
    return JSON.stringify('unknown')
  }
}

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8896',
        changeOrigin: true,
      },
    },
  },
  define: {
    __APP_VERSION__: getAppVersion(),
  },
})
