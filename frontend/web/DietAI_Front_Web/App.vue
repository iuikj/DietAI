<template>
  <div id="app">
    <!-- 这里会渲染页面内容 -->
  </div>
</template>

<script>
import { useUserStore } from '@/stores/user'
import { useFoodStore } from '@/stores/food'

export default {
  name: 'App',
  onLaunch() {
    console.log('App Launch')
    
    // 初始化用户状态
    const userStore = useUserStore()
    userStore.initializeAuth()
    
    // 初始化食物状态
    const foodStore = useFoodStore()
    foodStore.initializePersistedData()
    
    // 检查登录状态
    this.checkLoginStatus()
  },
  onShow() {
    console.log('App Show')
  },
  onHide() {
    console.log('App Hide')
  },
  methods: {
    checkLoginStatus() {
      const userStore = useUserStore()
      const token = uni.getStorageSync('token')
      
      if (!token && getCurrentPages().length > 0) {
        const currentPage = getCurrentPages()[getCurrentPages().length - 1]
        const route = currentPage.route
        
        // 需要登录的页面
        const needAuthPages = [
          'pages/index/index',
          'pages/record/index',
          'pages/health/index',
          'pages/chat/index',
          'pages/profile/index'
        ]
        
        if (needAuthPages.includes(route)) {
          uni.redirectTo({
            url: '/pages/auth/login/index'
          })
        }
      }
    }
  }
}
</script>

<style lang="scss">
/* 全局样式 */
@import '@/styles/variables.scss';
@import '@/styles/common.scss';

/* 应用基础样式 */
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  line-height: 1.6;
}

/* 重置样式 */
* {
  box-sizing: border-box;
}

page {
  background-color: #f5f5f5;
  font-size: 32rpx;
}

/* 通用工具类 */
.flex {
  display: flex;
}

.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.text-center {
  text-align: center;
}

.text-right {
  text-align: right;
}

/* 按钮样式 */
.btn {
  padding: 24rpx 48rpx;
  border-radius: 16rpx;
  font-size: 32rpx;
  font-weight: 500;
  text-align: center;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #007AFF 0%, #5AC8FA 100%);
  color: white;
}

.btn-primary:active {
  transform: scale(0.95);
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
}

.btn-secondary:active {
  background: #e0e0e0;
}

/* 卡片样式 */
.card {
  background: white;
  border-radius: 24rpx;
  padding: 32rpx;
  margin: 16rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.08);
}

/* 输入框样式 */
.input {
  width: 100%;
  padding: 24rpx;
  border: 2rpx solid #e0e0e0;
  border-radius: 12rpx;
  font-size: 32rpx;
  background: white;
}

.input:focus {
  border-color: #007AFF;
  outline: none;
}

/* 动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(100%);
  opacity: 0;
}
</style>
