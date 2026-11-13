import { createApp } from 'vue'
import 'element-plus/theme-chalk/dark/css-vars.css'
import './style.css'
import './theme.css'   // 主题层放在最后，覆盖基础样式与 Element Plus 的硬编码配色
import App from './App.vue'

createApp(App).mount('#app')
