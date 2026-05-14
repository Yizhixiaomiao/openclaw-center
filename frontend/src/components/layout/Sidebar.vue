<template>
  <div class="sidebar-container">
    <div class="sidebar-logo">
      <img src="/favicon.png" alt="logo" class="sidebar-logo-icon" />
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
