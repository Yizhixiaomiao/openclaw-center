<template>
  <div class="sidebar-container">
    <div class="sidebar-logo">
      <svg class="sidebar-logo-icon" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M14 2C9 2 5 6 5 11c0 3 1.5 5.5 4 7l1.5-3C9 13.5 8 11.5 8 10c0-3.5 3-6 6-6s6 2.5 6 6c0 1.5-1 3.5-2.5 5L19 18c2.5-1.5 4-4 4-7 0-5-4-9-9-9z" fill="currentColor"/>
        <path d="M10 17c-1 2-1.5 4-1 6 .2.6.8 1 1.4 1h7.2c.6 0 1.2-.4 1.4-1 .5-2 0-4-1-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" fill="none"/>
        <circle cx="11" cy="23" r="1.2" fill="currentColor"/>
        <circle cx="17" cy="23" r="1.2" fill="currentColor"/>
        <circle cx="14" cy="25" r="1.2" fill="currentColor"/>
      </svg>
      <h1>OpenClaw Center</h1>
    </div>
    <el-scrollbar>
      <el-menu
        :default-active="activeMenu"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/machines">
          <el-icon><Monitor /></el-icon>
          <span>机器管理</span>
        </el-menu-item>
        <el-menu-item index="/scenarios">
          <el-icon><Files /></el-icon>
          <span>业务场景</span>
        </el-menu-item>
        <el-menu-item index="/prompts">
          <el-icon><Document /></el-icon>
          <span>提示词模板</span>
        </el-menu-item>
        <el-menu-item index="/skills">
          <el-icon><Box /></el-icon>
          <span>技能管理</span>
        </el-menu-item>
        <el-menu-item index="/deploy">
          <el-icon><Upload /></el-icon>
          <span>分发任务</span>
        </el-menu-item>
        <el-menu-item index="/plans">
          <el-icon><Money /></el-icon>
          <span>Coding Plan</span>
        </el-menu-item>
        <el-menu-item index="/monitor">
          <el-icon><Warning /></el-icon>
          <span>监控日志</span>
        </el-menu-item>
      </el-menu>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  DataBoard,
  User,
  Monitor,
  Files,
  Document,
  Box,
  Upload,
  Money,
  Warning,
} from '@element-plus/icons-vue'

const route = useRoute()

const activeMenu = computed(() => {
  const matched = route.matched
  if (matched.length > 1) {
    return matched[1].path
  }
  return route.path
})
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.el-scrollbar {
  flex: 1;
}
</style>
