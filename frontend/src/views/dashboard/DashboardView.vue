<template>
  <div class="oc-page">
    <div class="oc-page-header">
      <div>
        <h1 class="oc-page-header__title">仪表盘</h1>
        <div class="oc-page-header__subtitle">系统概览与最近告警</div>
      </div>
    </div>

    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <el-card shadow="never">
          <div class="oc-metric-value">{{ overview.total_machines ?? 0 }}</div>
          <div class="oc-metric-label">机器总数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="oc-metric-value oc-status-ok">{{ overview.online_machines ?? 0 }}</div>
          <div class="oc-metric-label">在线机器</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="oc-metric-value oc-status-warn">{{ overview.active_users ?? 0 }}</div>
          <div class="oc-metric-label">活跃用户</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="oc-metric-value oc-status-error">{{ overview.warning_plans ?? 0 }}</div>
          <div class="oc-metric-label">告警数量</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="oc-table-card">
      <template #header>
        <div class="card-header">
          <span>最近告警</span>
          <span class="oc-action-link" @click="router.push('/monitor')">查看全部</span>
        </div>
      </template>
      <el-table :data="alerts" stripe style="width: 100%;" v-loading="tableLoading">
        <el-table-column prop="alert_time" label="时间" width="180" />
        <el-table-column prop="machine_name" label="机器" width="160" />
        <el-table-column prop="alert_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="alertTagType(row.alert_type)" size="small">
              {{ row.alert_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="内容" min-width="240" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'resolved' ? 'success' : 'danger'" size="small">
              {{ row.status === 'resolved' ? '已处理' : '未处理' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getMonitorOverview, getMonitorAlerts } from '../../api/monitor'

const router = useRouter()

const overview = ref({})
const alerts = ref([])
const tableLoading = ref(false)

function alertTagType(type) {
  const map = {
    critical: 'danger',
    warning: 'warning',
    info: 'info',
  }
  return map[type] || 'info'
}

async function loadOverview() {
  try {
    overview.value = await getMonitorOverview()
  } catch {
    ElMessage.error('获取概览数据失败')
  }
}

async function loadAlerts() {
  tableLoading.value = true
  try {
    const data = await getMonitorAlerts()
    alerts.value = Array.isArray(data) ? data : []
  } catch {
    ElMessage.error('获取告警数据失败')
  } finally {
    tableLoading.value = false
  }
}

onMounted(() => {
  loadOverview()
  loadAlerts()
})
</script>

<style scoped>
.stat-row {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
