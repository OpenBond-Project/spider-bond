import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// Element Plus 按需自动引入：模板里用 <el-* /> 时，只打包该组件及其样式，
// 避免全量引入 element-plus/dist/index.css 带来的 370KB 首屏开销。
export default defineConfig({
  base: '/',
  plugins: [
    vue(),
    AutoImport({ resolvers: [ElementPlusResolver()] }),
    Components({
      resolvers: [ElementPlusResolver()],
      dts: false,
    }),
  ],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    assetsDir: 'assets',
    chunkSizeWarningLimit: 1200,
  },
})
