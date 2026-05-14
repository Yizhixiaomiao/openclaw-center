<template>
  <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item v-if="currentPageTitle">{{ currentPageTitle }}</el-breadcrumb-item>
    </el-breadcrumb>
    <div style="display: flex; align-items: center; gap: 16px;">
      <el-dropdown trigger="click" @command="handleCommand">
        <span style="display: flex; align-items: center; gap: 6px; cursor: pointer; color: var(--oc-text-secondary);">
          <el-avatar :size="28">{{ (authStore.userName || 'U').charAt(0) }}</el-avatar>
          <span>{{ authStore.userName }}</span>
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item disabled>
              <span style="font-weight: 600;">{{ authStore.userName }}</span>
            </el-dropdown-item>
            <el-dropdown-item disabled>
              <span style="font-size: 12px; color: var(--el-text-color-secondary);">{{ roleLabel }} · ID: {{ authStore.userId }}</span>
            </el-dropdown-item>
            <el-dropdown-item divided command="logout" style="color: var(--el-color-danger);">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { ArrowDown, SwitchButton } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

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
  AIConfig: 'AI配置',
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

function handleCommand(cmd) {
  if (cmd === 'logout') {
    ElMessage.success('已退出登录')
    authStore.logout()
    router.push('/login')
  }
}
</script>
