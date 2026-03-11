import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 默认端口配置:
// - 前端: 50888 (Vite 开发服务器)
// - 后端: 50801 (FastAPI 主服务)
// - 估值API: 50802 (独立估值计算服务)

export default defineConfig({
  plugins: [react()],
  server: {
    port: 50888,  // 前端开发服务器端口
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:50801',  // 后端 API 服务地址
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
