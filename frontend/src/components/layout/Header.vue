<template>
  <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item v-if="currentPageTitle">{{ currentPageTitle }}</el-breadcrumb-item>
    </el-breadcrumb>
    <div style="display: flex; align-items: center; gap: 16px;">
      <span class="oc-text-secondary">{{ authStore.userName }}</span>
      <el-tag size="small" type="info">{{ roleLabel }}</el-tag>
      <el-button type="danger" text @click="handleLogout">退出登录</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const pageTitleMap = {
  Dashboard: '仪表盘',
  Users: '用户管理',
  UserDetail: '用户详情',
  Machines: '机器管理',
  MachineDetail: '机器详情',
  Scenarios: '业务场景',
  Prompts: '提示词模板',
  TemplateDetail: '模板详情',
  Skills: '技能管理',
  Deploy: '分发任务',
  Plans: 'Coding Plan',
  Monitor: '监控日志',
}

const currentPageTitle = computed(() => {
  return pageTitleMap[route.name] || route.meta?.title || ''
})

const roleLabel = computed(() => {
  const roleMap = {
    admin: '管理员',
    support: '运维',
    ops: '运营',
  }
  return roleMap[authStore.userRole] || authStore.userRole || '未知'
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>
