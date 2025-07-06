<template>
  <view class="home-page">
    <!-- 顶部问候区域 -->
    <view class="greeting-section">
      <view class="greeting-content">
        <view class="greeting-text">
          <text class="greeting-main">{{ greetingText }}，{{ userDisplayName }}</text>
          <text class="greeting-subtitle">{{ motivationalText }}</text>
        </view>
        <view class="user-avatar" @tap="goToProfile">
          <image class="avatar-image" :src="userAvatar" mode="aspectFill" />
          <view v-if="hasNotification" class="notification-dot"></view>
        </view>
      </view>
    </view>
    
    <!-- 今日摘要卡片 -->
    <view class="summary-card">
      <view class="summary-header">
        <text class="summary-title">今日摘要</text>
        <text class="summary-date">{{ todayDateText }}</text>
      </view>
      
      <!-- 热量进度环 -->
      <view class="calories-section">
        <view class="calories-ring">
          <canvas 
            canvas-id="caloriesRing" 
            class="ring-canvas"
            @touchstart="handleRingTouch"
          ></canvas>
          <view class="ring-content">
            <text class="calories-value">{{ todaySummary.calories }}</text>
            <text class="calories-unit">kcal</text>
            <text class="calories-target">/ {{ todaySummary.targetCalories }}</text>
          </view>
        </view>
        <view class="calories-info">
          <text class="progress-text">{{ caloriesProgressText }}</text>
        </view>
      </view>
      
      <!-- 营养素进度条 -->
      <view class="nutrition-grid">
        <view class="nutrition-item">
          <view class="nutrition-header">
            <text class="nutrition-label">蛋白质</text>
            <text class="nutrition-value">{{ todaySummary.protein }}g</text>
          </view>
          <view class="progress-bar">
            <view 
              class="progress-fill protein"
              :style="{ width: proteinProgress + '%' }"
            ></view>
          </view>
        </view>
        
        <view class="nutrition-item">
          <view class="nutrition-header">
            <text class="nutrition-label">碳水</text>
            <text class="nutrition-value">{{ todaySummary.carbs }}g</text>
          </view>
          <view class="progress-bar">
            <view 
              class="progress-fill carbs"
              :style="{ width: carbsProgress + '%' }"
            ></view>
          </view>
        </view>
        
        <view class="nutrition-item">
          <view class="nutrition-header">
            <text class="nutrition-label">脂肪</text>
            <text class="nutrition-value">{{ todaySummary.fat }}g</text>
          </view>
          <view class="progress-bar">
            <view 
              class="progress-fill fat"
              :style="{ width: fatProgress + '%' }"
            ></view>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 快速操作 -->
    <view class="quick-actions">
      <view class="action-item camera-action" @tap="openCamera">
        <view class="action-icon-wrapper">
          <view class="action-icon camera-icon">
            <text class="icon">📷</text>
          </view>
          <view class="icon-ring"></view>
        </view>
        <text class="action-text">拍照记录</text>
      </view>
      
      <view class="action-item" @tap="openChat">
        <view class="action-icon-wrapper">
          <view class="action-icon">
            <text class="icon">🤖</text>
          </view>
        </view>
        <text class="action-text">AI咨询</text>
      </view>
      
      <view class="action-item" @tap="recordWeight">
        <view class="action-icon-wrapper">
          <view class="action-icon">
            <text class="icon">⚖️</text>
          </view>
        </view>
        <text class="action-text">体重记录</text>
      </view>
      
      <view class="action-item" @tap="viewRecords">
        <view class="action-icon-wrapper">
          <view class="action-icon">
            <text class="icon">📊</text>
          </view>
        </view>
        <text class="action-text">查看记录</text>
      </view>
    </view>
    
    <!-- 最近记录 -->
    <view class="recent-section">
      <view class="section-header">
        <text class="section-title">最近记录</text>
        <text class="section-more" @tap="viewAllRecords">查看全部</text>
      </view>
      
      <view class="recent-list">
        <view 
          v-for="record in recentRecords" 
          :key="record.id"
          class="record-item"
          @tap="viewRecord(record)"
        >
          <view class="record-meal">
            <view class="meal-icon">
              <text class="meal-emoji">{{ getMealIcon(record.meal_type) }}</text>
            </view>
            <text class="meal-time">{{ formatTime(record.created_at) }}</text>
          </view>
          
          <view class="record-content">
            <text class="food-name">{{ record.food_name }}</text>
            <view class="nutrition-summary">
              <text class="calories">{{ record.calories }}kcal</text>
              <text class="divider">·</text>
              <text class="protein">{{ record.protein }}g蛋白质</text>
            </view>
          </view>
          
          <view class="record-arrow">
            <text class="arrow">→</text>
          </view>
        </view>
        
        <!-- 空状态 -->
        <view v-if="recentRecords.length === 0" class="empty-state">
          <text class="empty-icon">🍽️</text>
          <text class="empty-text">还没有记录，开始记录您的第一餐吧！</text>
          <button class="empty-action" @tap="openCamera">
            <text class="action-text">拍照记录</text>
          </button>
        </view>
      </view>
    </view>
    
    <!-- 今日建议 -->
    <view class="tips-section" v-if="dailyTip">
      <view class="tips-card">
        <view class="tips-header">
          <text class="tips-icon">💡</text>
          <text class="tips-title">今日建议</text>
        </view>
        <text class="tips-content">{{ dailyTip }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useUserStore } from '@/stores/user'
import { useFoodStore } from '@/stores/food'
import dayjs from 'dayjs'

const userStore = useUserStore()
const foodStore = useFoodStore()

// 响应式数据
const hasNotification = ref(false)
const dailyTip = ref('')

// 计算属性
const userDisplayName = computed(() => userStore.displayName)
const userAvatar = computed(() => userStore.avatar)
const todaySummary = computed(() => foodStore.todaySummary)
const recentRecords = computed(() => foodStore.recentRecords.slice(0, 5))

const greetingText = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const motivationalText = computed(() => {
  const texts = [
    '今天也要健康饮食哦',
    '坚持记录，拥抱健康',
    '营养均衡，活力满满',
    '让我们一起变得更健康'
  ]
  return texts[Math.floor(Math.random() * texts.length)]
})

const todayDateText = computed(() => {
  return dayjs().format('M月D日')
})

const caloriesProgress = computed(() => {
  return Math.min((todaySummary.value.calories / todaySummary.value.targetCalories) * 100, 100)
})

const caloriesProgressText = computed(() => {
  const progress = caloriesProgress.value
  if (progress < 50) return '还需要加油哦'
  if (progress < 80) return '进展不错'
  if (progress < 100) return '快达到目标了'
  return '今日目标已达成'
})

const proteinProgress = computed(() => {
  return Math.min((todaySummary.value.protein / todaySummary.value.targetProtein) * 100, 100)
})

const carbsProgress = computed(() => {
  return Math.min((todaySummary.value.carbs / todaySummary.value.targetCarbs) * 100, 100)
})

const fatProgress = computed(() => {
  return Math.min((todaySummary.value.fat / todaySummary.value.targetFat) * 100, 100)
})

// 页面生命周期
onMounted(async () => {
  await loadData()
  nextTick(() => {
    drawCaloriesRing()
  })
})

// 方法
const loadData = async () => {
  try {
    await Promise.all([
      foodStore.fetchTodaySummary(),
      foodStore.fetchRecentRecords(),
      loadDailyTip()
    ])
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

const loadDailyTip = async () => {
  // 模拟获取每日建议
  const tips = [
    '多吃蔬菜水果，补充维生素和纤维',
    '适量摄入蛋白质，有助于肌肉修复',
    '控制精制糖的摄入，选择复合碳水化合物',
    '保持规律的用餐时间，有助于消化',
    '多喝水，保持身体水分平衡'
  ]
  dailyTip.value = tips[Math.floor(Math.random() * tips.length)]
}

const drawCaloriesRing = () => {
  const ctx = uni.createCanvasContext('caloriesRing')
  const centerX = 75
  const centerY = 75
  const radius = 60
  const lineWidth = 8
  
  // 清除画布
  ctx.clearRect(0, 0, 150, 150)
  
  // 背景圆环
  ctx.beginPath()
  ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI)
  ctx.setStrokeStyle('#F0F0F0')
  ctx.setLineWidth(lineWidth)
  ctx.stroke()
  
  // 进度圆环
  const progressAngle = (caloriesProgress.value / 100) * 2 * Math.PI
  ctx.beginPath()
  ctx.arc(centerX, centerY, radius, -Math.PI / 2, -Math.PI / 2 + progressAngle)
  ctx.setStrokeStyle('#007AFF')
  ctx.setLineWidth(lineWidth)
  ctx.setLineCap('round')
  ctx.stroke()
  
  ctx.draw()
}

const handleRingTouch = () => {
  uni.vibrateShort({ type: 'light' })
}

// 页面跳转方法
const openCamera = () => {
  uni.navigateTo({
    url: '/pages/record/camera/index'
  })
}

const openChat = () => {
  uni.switchTab({
    url: '/pages/chat/index'
  })
}

const recordWeight = () => {
  uni.navigateTo({
    url: '/pages/health/weight/index'
  })
}

const viewRecords = () => {
  uni.switchTab({
    url: '/pages/record/index'
  })
}

const viewAllRecords = () => {
  uni.switchTab({
    url: '/pages/record/index'
  })
}

const goToProfile = () => {
  uni.switchTab({
    url: '/pages/profile/index'
  })
}

const viewRecord = (record) => {
  uni.navigateTo({
    url: `/pages/record/detail/index?id=${record.id}`
  })
}

// 工具方法
const getMealIcon = (mealType) => {
  const icons = {
    1: '🌅', // 早餐
    2: '🌞', // 午餐  
    3: '🌙', // 晚餐
    4: '🍎', // 加餐
    5: '🍿'  // 零食
  }
  return icons[mealType] || '🍽️'
}

const formatTime = (timestamp) => {
  return dayjs(timestamp).format('HH:mm')
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';
@import '@/styles/common.scss';

.home-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 0 32rpx;
  padding-bottom: 200rpx;
}

.greeting-section {
  padding: 60rpx 0 40rpx;
}

.greeting-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.greeting-text {
  flex: 1;
}

.greeting-main {
  font-size: 36rpx;
  font-weight: bold;
  color: $text-color;
  display: block;
  margin-bottom: 8rpx;
}

.greeting-subtitle {
  font-size: 28rpx;
  color: $text-secondary;
}

.user-avatar {
  position: relative;
  width: 80rpx;
  height: 80rpx;
}

.avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 4rpx solid white;
  box-shadow: $shadow-light;
}

.notification-dot {
  position: absolute;
  top: -4rpx;
  right: -4rpx;
  width: 24rpx;
  height: 24rpx;
  background: $error-color;
  border-radius: 50%;
  border: 4rpx solid white;
}

.summary-card {
  @include card-style;
  margin-bottom: 32rpx;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32rpx;
}

.summary-title {
  font-size: 32rpx;
  font-weight: bold;
  color: $text-color;
}

.summary-date {
  font-size: 24rpx;
  color: $text-secondary;
}

.calories-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 40rpx;
}

.calories-ring {
  position: relative;
  margin-bottom: 16rpx;
}

.ring-canvas {
  width: 150px;
  height: 150px;
}

.ring-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.calories-value {
  font-size: 40rpx;
  font-weight: bold;
  color: $primary-color;
  display: block;
}

.calories-unit {
  font-size: 24rpx;
  color: $text-secondary;
}

.calories-target {
  font-size: 20rpx;
  color: $text-tertiary;
}

.calories-info {
  text-align: center;
}

.progress-text {
  font-size: 28rpx;
  color: $text-secondary;
}

.nutrition-grid {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.nutrition-item {
  
}

.nutrition-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8rpx;
}

.nutrition-label {
  font-size: 28rpx;
  color: $text-secondary;
}

.nutrition-value {
  font-size: 28rpx;
  font-weight: 500;
  color: $text-color;
}

.progress-bar {
  height: 8rpx;
  background: $border-light;
  border-radius: 4rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4rpx;
  transition: width 0.6s ease;
  
  &.protein {
    background: $nutrition-protein;
  }
  
  &.carbs {
    background: $nutrition-carbs;
  }
  
  &.fat {
    background: $nutrition-fat;
  }
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24rpx;
  margin-bottom: 32rpx;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24rpx 16rpx;
  background: white;
  border-radius: 20rpx;
  box-shadow: $shadow-light;
  transition: all 0.3s ease;
  
  &:active {
    transform: scale(0.95);
  }
  
  &.camera-action {
    .action-icon-wrapper {
      position: relative;
    }
    
    .camera-icon {
      background: $gradient-primary;
      transform: scale(1.2);
    }
    
    .icon-ring {
      position: absolute;
      top: -8rpx;
      left: -8rpx;
      right: -8rpx;
      bottom: -8rpx;
      border: 3rpx solid rgba(0, 122, 255, 0.3);
      border-radius: 50%;
      animation: pulse 2s infinite;
    }
  }
}

.action-icon-wrapper {
  margin-bottom: 16rpx;
}

.action-icon {
  width: 80rpx;
  height: 80rpx;
  background: $background-color;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon {
  font-size: 36rpx;
}

.action-text {
  font-size: 24rpx;
  color: $text-secondary;
  text-align: center;
}

.recent-section {
  @include card-style;
  margin-bottom: 32rpx;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  color: $text-color;
}

.section-more {
  font-size: 24rpx;
  color: $primary-color;
}

.recent-list {
  
}

.record-item {
  display: flex;
  align-items: center;
  padding: 24rpx 0;
  border-bottom: 1rpx solid $border-light;
  transition: all 0.3s ease;
  
  &:last-child {
    border-bottom: none;
  }
  
  &:active {
    background: rgba(0, 122, 255, 0.05);
    transform: translateX(8rpx);
  }
}

.record-meal {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-right: 24rpx;
  width: 80rpx;
}

.meal-icon {
  width: 48rpx;
  height: 48rpx;
  background: $background-color;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4rpx;
}

.meal-emoji {
  font-size: 24rpx;
}

.meal-time {
  font-size: 20rpx;
  color: $text-tertiary;
}

.record-content {
  flex: 1;
}

.food-name {
  font-size: 28rpx;
  color: $text-color;
  font-weight: 500;
  display: block;
  margin-bottom: 4rpx;
}

.nutrition-summary {
  display: flex;
  align-items: center;
}

.calories {
  font-size: 24rpx;
  color: $text-secondary;
}

.divider {
  margin: 0 8rpx;
  color: $text-tertiary;
  font-size: 20rpx;
}

.protein {
  font-size: 24rpx;
  color: $text-secondary;
}

.record-arrow {
  margin-left: 16rpx;
}

.arrow {
  font-size: 24rpx;
  color: $text-tertiary;
}

.empty-state {
  text-align: center;
  padding: 80rpx 32rpx;
}

.empty-icon {
  font-size: 80rpx;
  display: block;
  margin-bottom: 24rpx;
}

.empty-text {
  font-size: 28rpx;
  color: $text-secondary;
  margin-bottom: 32rpx;
  display: block;
}

.empty-action {
  @include btn-style;
  background: $gradient-primary;
  color: white;
  padding: 20rpx 40rpx;
}

.tips-section {
  @include card-style;
  margin-bottom: 32rpx;
}

.tips-card {
  
}

.tips-header {
  display: flex;
  align-items: center;
  margin-bottom: 16rpx;
}

.tips-icon {
  font-size: 32rpx;
  margin-right: 12rpx;
}

.tips-title {
  font-size: 28rpx;
  font-weight: 500;
  color: $text-color;
}

.tips-content {
  font-size: 26rpx;
  color: $text-secondary;
  line-height: 1.5;
}

// 动画
@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.7;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
