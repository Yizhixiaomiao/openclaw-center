<template>
  <div class="monitor-view">
    <div class="page-header">
      <h2>监控中心</h2>
      <el-button @click="refreshAll">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- Stat Cards -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">总机器数</div>
            <div class="stat-value">{{ overview.total_machines ?? '-' }}</div>
          </div>
          <el-icon class="stat-icon" :size="40" color="#409EFF"><Monitor /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">在线数</div>
            <div class="stat-value online">{{ overview.online_count ?? '-' }}</div>
          </div>
          <el-icon class="stat-icon" :size="40" color="#67C23A"><CircleCheck /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">离线数</div>
            <div class="stat-value offline">{{ overview.offline_count ?? '-' }}</div>
          </div>
          <el-icon class="stat-icon" :size="40" color="#909399"><CircleClose /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">异常数</div>
            <div class="stat-value error">{{ overview.error_count ?? '-' }}</div>
          </div>
          <el-icon class="stat-icon" :size="40" color="#F56C6C"><WarningFilled /></el-icon>
        </el-card>
      </el-col>
    </el-row>

    <!-- Machine Status Grid -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <span>机器状态</span>
      </template>
      <el-table
        v-loading="machinesLoading"
        :data="machines"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="machine_code" label="机器码" min-width="160" show-overflow-tooltip />
        <el-table-column prop="hostname" label="主机名" width="140" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" width="140" />
        <el-table-column label="在线状态" width="100" align="center">
          <template #default="{ row }">
            <span
              class="status-dot"
              :class="row.is_online ? 'online' : 'offline'"
            />
            {{ row.is_online ? '在线' : '离线' }}
          </template>
        </el-table-column>
        <el-table-column prop="department" label="部门" width="120" show-overflow-tooltip />
        <el-table-column prop="user_id" label="用户ID" width="100" align="center" />
        <el-table-column prop="last_heartbeat" label="最近心跳" width="170" align="center">
          <template #default="{ row }">
            {{ formatTime(row.last_heartbeat) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Alert List -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <span>告警列表</span>
      </template>
      <el-table
        v-loading="alertsLoading"
        :data="alerts"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column label="类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="alertTypeMap[row.type]?.tagType" size="small">
              {{ alertTypeMap[row.type]?.label || row.type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="related_id" label="关联ID" width="120" align="center" />
        <el-table-column prop="message" label="消息" min-width="300" show-overflow-tooltip />
      </el-table>
    </el-card>

    <!-- Log Viewer -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <span>日志查看</span>
      </template>
      <!-- Log Filters -->
      <el-form :inline="true" :model="logFilters" class="log-filter-form" @submit.prevent="loadLogs">
        <el-form-item label="机器ID">
          <el-input
            v-model="logFilters.machine_id"
            placeholder="请输入机器ID"
            clearable
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item label="级别">
          <el-select v-model="logFilters.level" placeholder="全部级别" clearable>
            <el-option label="Debug" value="debug" />
            <el-option label="Info" value="info" />
            <el-option label="Warning" value="warning" />
            <el-option label="Error" value="error" />
            <el-option label="Critical" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="类别">
          <el-input
            v-model="logFilters.category"
            placeholder="请输入类别"
            clearable
            style="width: 150px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadLogs">查询</el-button>
          <el-button @click="resetLogFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- Log Table -->
      <el-table
        v-loading="logsLoading"
        :data="logs"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="machine_id" label="机器ID" width="120" align="center" show-overflow-tooltip />
        <el-table-column label="级别" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="logLevelTagMap[row.level]?.type" size="small">
              {{ logLevelTagMap[row.level]?.label || row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="类别" width="120" show-overflow-tooltip />
        <el-table-column prop="message" label="消息" min-width="280" show-overflow-tooltip />
        <el-table-column prop="created_at" label="时间" width="170" align="center">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="logPagination.page"
          v-model:page-size="logPagination.size"
          :total="logPagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadLogs"
          @current-change="loadLogs"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import {
  Refresh,
  Monitor,
  CircleCheck,
  CircleClose,
  WarningFilled,
} from '@element-plus/icons-vue'
import {
  getMonitorOverview,
  getMonitorMachines,
  getMonitorAlerts,
  getMonitorLogs,
} from '../../api/monitor'

const alertTypeMap = {
  offline: { label: '离线', tagType: 'danger' },
  error: { label: '异常', tagType: 'danger' },
  plan_warning: { label: '额度预警', tagType: 'warning' },
  plan_high_risk: { label: '额度超限', tagType: 'danger' },
}

const logLevelTagMap = {
  debug: { label: 'Debug', type: 'info' },
  info: { label: 'Info', type: '' },
  warning: { label: 'Warning', type: 'warning' },
  error: { label: 'Error', type: 'danger' },
  critical: { label: 'Critical', type: 'danger' },
}

// Overview
const overview = ref({})

async function loadOverview() {
  try {
    const res = await getMonitorOverview()
    overview.value = res || {}
  } catch {
    // error handled by interceptor
  }
}

// Machines
const machinesLoading = ref(false)
const machines = ref([])

async function loadMachines() {
  machinesLoading.value = true
  try {
    const res = await getMonitorMachines()
    machines.value = Array.isArray(res) ? res : (res.items || res.data || [])
  } catch {
    // error handled by interceptor
  } finally {
    machinesLoading.value = false
  }
}

// Alerts
const alertsLoading = ref(false)
const alerts = ref([])

async function loadAlerts() {
  alertsLoading.value = true
  try {
    const res = await getMonitorAlerts()
    alerts.value = Array.isArray(res) ? res : (res.items || res.data || [])
  } catch {
    // error handled by interceptor
  } finally {
    alertsLoading.value = false
  }
}

// Logs
const logsLoading = ref(false)
const logs = ref([])

const logFilters = reactive({
  machine_id: '',
  level: '',
  category: '',
})

const logPagination = reactive({
  page: 1,
  size: 20,
  total: 0,
})

async function loadLogs() {
  logsLoading.value = true
  try {
    const params = {
      skip: (logPagination.page - 1) * logPagination.size,
      limit: logPagination.size,
      ...logFilters,
    }
    Object.keys(params).forEach((key) => {
      if (params[key] === '' || params[key] == null) delete params[key]
    })
    const res = await getMonitorLogs(params)
    logs.value = Array.isArray(res) ? res : (res.items || res.data || [])
    logPagination.total = res.total || logs.value.length
  } catch {
    // error handled by interceptor
  } finally {
    logsLoading.value = false
  }
}

function resetLogFilters() {
  logFilters.machine_id = ''
  logFilters.level = ''
  logFilters.category = ''
  logPagination.page = 1
  loadLogs()
}

function formatTime(val) {
  if (!val) return '-'
  return new Date(val).toLocaleString('zh-CN')
}

function refreshAll() {
  loadOverview()
  loadMachines()
  loadAlerts()
  loadLogs()
}

onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
.monitor-view {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 20px;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.stat-value.online {
  color: #67C23A;
}

.stat-value.offline {
  color: #909399;
}

.stat-value.error {
  color: #F56C6C;
}

.stat-icon {
  flex-shrink: 0;
  opacity: 0.6;
}

.section-card {
  margin-bottom: 16px;
}

.log-filter-form {
  margin-bottom: 16px;
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}

.status-dot.online {
  background-color: #67C23A;
  box-shadow: 0 0 4px #67C23A;
}

.status-dot.offline {
  background-color: #909399;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
