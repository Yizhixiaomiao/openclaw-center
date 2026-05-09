<template>
  <div class="dashboard-container">
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card stat-card--blue">
          <div class="stat-card__content">
            <div class="stat-card__icon stat-card__icon--blue">
              <el-icon :size="32"><Monitor /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__number">{{ overview.total_machines ?? 0 }}</div>
              <div class="stat-card__label">机器总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card stat-card--green">
          <div class="stat-card__content">
            <div class="stat-card__icon stat-card__icon--green">
              <el-icon :size="32"><CircleCheck /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__number">{{ overview.online_machines ?? 0 }}</div>
              <div class="stat-card__label">在线机器</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card stat-card--orange">
          <div class="stat-card__content">
            <div class="stat-card__icon stat-card__icon--orange">
              <el-icon :size="32"><User /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__number">{{ overview.active_users ?? 0 }}</div>
              <div class="stat-card__label">活跃用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card stat-card--red">
          <div class="stat-card__content">
            <div class="stat-card__icon stat-card__icon--red">
              <el-icon :size="32"><Warning /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__number">{{ overview.warning_plans ?? 0 }}</div>
              <div class="stat-card__label">告警数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="alert-card" shadow="never">
      <template #header>
        <div class="alert-card__header">
          <span class="alert-card__title">最近告警</span>
          <el-button text type="primary" @click="router.push('/monitor')">
            查看全部
          </el-button>
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
import { Monitor, CircleCheck, User, Warning } from '@element-plus/icons-vue'
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
.dashboard-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stat-row {
  margin-bottom: 0;
}

.stat-card__content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-card__icon {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.stat-card__icon--blue {
  background: linear-gradient(135deg, #409EFF, #66b1ff);
}

.stat-card__icon--green {
  background: linear-gradient(135deg, #67C23A, #85ce61);
}

.stat-card__icon--orange {
  background: linear-gradient(135deg, #E6A23C, #ebb563);
}

.stat-card__icon--red {
  background: linear-gradient(135deg, #F56C6C, #f78989);
}

.stat-card__number {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-card__label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.alert-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.alert-card__title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
</style>
