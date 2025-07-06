import { createSSRApp } from 'vue'
import App from './App.vue'
import { createPinia } from 'pinia'

export function createApp() {
  const app = createSSRApp(App)

  // 创建pinia实例
  const pinia = createPinia()

  // 安装pinia
  app.use(pinia)

  return {
    app
  }
}