<template>
  <div class="oc-page">
    <div class="oc-page-header">
      <div>
        <h1 class="oc-page-header__title">仪表盘</h1>
        <div class="oc-page-header__subtitle">系统概览与运营数据</div>
      </div>
    </div>

    <!-- Row 1: Metric Cards -->
    <el-row :gutter="16" class="metric-row">
      <el-col :span="6">
        <el-card shadow="never" class="metric-card">
          <div class="metric-card__value">{{ overview.total_machines ?? 0 }}</div>
          <div class="metric-card__label">机器总数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="metric-card metric-card--success">
          <div class="metric-card__value">{{ overview.online_machines ?? 0 }}</div>
          <div class="metric-card__label">在线机器</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="metric-card metric-card--warning">
          <div class="metric-card__value">{{ overview.total_users ?? 0 }}</div>
          <div class="metric-card__label">活跃用户</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="metric-card metric-card--danger">
          <div class="metric-card__value">{{ overview.warning_plans ?? 0 }}</div>
          <div class="metric-card__label">告警套餐</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 2: Machine Status + Department -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="12">
        <el-card shadow="never" class="chart-card">
          <template #header><span>机器状态分布</span></template>
          <v-chart :option="statusPieOption" autoresize style="height: 280px" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" class="chart-card">
          <template #header><span>部门机器分布</span></template>
          <v-chart :option="deptBarOption" autoresize style="height: 280px" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 3: Usage Trend + Deploy Stats -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="14">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="trend-header">
              <span>API 用量趋势</span>
              <el-radio-group v-model="trendDays" size="small" @change="loadUsageTrend">
                <el-radio-button :value="7">7天</el-radio-button>
                <el-radio-button :value="30">30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <v-chart :option="usageTrendOption" autoresize style="height: 280px" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never" class="chart-card">
          <template #header><span>部署任务状态</span></template>
          <v-chart :option="deployPieOption" autoresize style="height: 280px" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 4: Skill Ranking + Alerts -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="12">
        <el-card shadow="never" class="chart-card">
          <template #header><span>技能安装排行</span></template>
          <v-chart :option="skillRankOption" autoresize style="height: 280px" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>最近告警</span>
              <span class="oc-action-link" @click="router.push('/monitor')">查看全部</span>
            </div>
          </template>
          <el-table :data="alerts.slice(0, 5)" stripe size="small" style="width: 100%;">
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="alertTagType(row.type)" size="small">{{ alertTypeLabel(row.type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="内容" min-width="200" show-overflow-tooltip />
          </el-table>
          <el-empty v-if="alerts.length === 0" description="暂无告警" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import { getMonitorOverview, getMonitorAlerts, getUsageTrend, getMachineStats, getSkillRanking, getDeployStats } from '../../api/monitor'

const router = useRouter()

// ---------- Data ----------
const overview = ref({})
const alerts = ref([])
const trendDays = ref(7)
const usageTrend = ref([])
const machineStats = ref({ status_distribution: [], department_distribution: [] })
const skillRanking = ref([])
const deployStats = ref([])

// ---------- Colors ----------
const COLORS = {
  primary: '#dc3545',
  success: '#16a34a',
  warning: '#ea580c',
  info: '#6b7280',
  danger: '#dc2626',
  blue: '#3b82f6',
  purple: '#8b5cf6',
  pink: '#ec4899',
  teal: '#14b8a6',
  amber: '#f59e0b',
}

const PIE_COLORS = [COLORS.success, COLORS.info, COLORS.danger, COLORS.warning, '#9ca3af']
const DEPLOY_COLORS = [COLORS.blue, COLORS.warning, COLORS.success, COLORS.danger, COLORS.purple]

// ---------- Alert helpers ----------
function alertTagType(type) {
  const map = { error: 'danger', plan_high_risk: 'danger', offline: 'warning', plan_warning: 'warning' }
  return map[type] || 'info'
}

function alertTypeLabel(type) {
  const map = { offline: '离线', error: '异常', plan_warning: '套餐预警', plan_high_risk: '额度超限' }
  return map[type] || type
}

// ---------- Chart Options ----------
const statusPieOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { bottom: 0, type: 'scroll' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    center: ['50%', '45%'],
    label: { show: true, formatter: '{b}\n{c}', fontSize: 12 },
    data: machineStats.value.status_distribution,
    color: PIE_COLORS,
    emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.15)' } },
  }],
}))

const deptBarOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 80, right: 20, top: 10, bottom: 10 },
  xAxis: { type: 'value' },
  yAxis: {
    type: 'category',
    data: machineStats.value.department_distribution.map(d => d.name),
    inverse: true,
    axisLabel: { width: 70, overflow: 'truncate' },
  },
  series: [{
    type: 'bar',
    data: machineStats.value.department_distribution.map(d => d.value),
    barWidth: 18,
    itemStyle: { color: COLORS.primary, borderRadius: [0, 4, 4, 0] },
    label: { show: true, position: 'right', fontSize: 12 },
  }],
}))

const usageTrendOption = computed(() => {
  const dates = usageTrend.value.map(d => d.date.slice(5))
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['调用次数', 'Token数'], bottom: 0 },
    grid: { left: 60, right: 60, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 11 } },
    yAxis: [
      { type: 'value', name: '调用次数', axisLabel: { fontSize: 11 } },
      { type: 'value', name: 'Token数', axisLabel: { fontSize: 11 } },
    ],
    series: [
      {
        name: '调用次数',
        type: 'line',
        data: usageTrend.value.map(d => d.total_calls),
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2 },
        itemStyle: { color: COLORS.primary },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(220,53,69,0.15)' }, { offset: 1, color: 'rgba(220,53,69,0)' }] } },
      },
      {
        name: 'Token数',
        type: 'line',
        yAxisIndex: 1,
        data: usageTrend.value.map(d => d.total_tokens),
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2 },
        itemStyle: { color: COLORS.blue },
      },
    ],
  }
})

const deployPieOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { bottom: 0, type: 'scroll' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    center: ['50%', '45%'],
    label: { show: true, formatter: '{b}\n{c}', fontSize: 12 },
    data: deployStats.value,
    color: DEPLOY_COLORS,
    emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.15)' } },
  }],
}))

const skillRankOption = computed(() => {
  const list = [...skillRanking.value].reverse()
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 100, right: 30, top: 10, bottom: 10 },
    xAxis: { type: 'value' },
    yAxis: {
      type: 'category',
      data: list.map(d => d.name),
      axisLabel: { width: 90, overflow: 'truncate' },
    },
    series: [{
      type: 'bar',
      data: list.map(d => d.install_count),
      barWidth: 16,
      itemStyle: { color: COLORS.teal, borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: 'right', fontSize: 12 },
    }],
  }
})

// ---------- Data Loading ----------
async function loadOverview() {
  try { overview.value = await getMonitorOverview() } catch {}
}

async function loadAlerts() {
  try {
    const data = await getMonitorAlerts()
    alerts.value = Array.isArray(data) ? data : []
  } catch {}
}

async function loadUsageTrend() {
  try { usageTrend.value = await getUsageTrend(trendDays.value) } catch {}
}

async function loadMachineStats() {
  try { machineStats.value = await getMachineStats() } catch {}
}

async function loadSkillRankingData() {
  try { skillRanking.value = await getSkillRanking(10) } catch {}
}

async function loadDeployStats() {
  try { deployStats.value = await getDeployStats() } catch {}
}

onMounted(() => {
  Promise.allSettled([
    loadOverview(),
    loadAlerts(),
    loadUsageTrend(),
    loadMachineStats(),
    loadSkillRankingData(),
    loadDeployStats(),
  ])
})
</script>

<style scoped>
.metric-row {
  margin-bottom: 16px;
  flex-shrink: 0;
}

.metric-card {
  text-align: center;
  padding: 8px 0;
}

.metric-card__value {
  font-size: 32px;
  font-weight: 700;
  color: var(--oc-text-primary);
  line-height: 1.2;
}

.metric-card__label {
  font-size: 13px;
  color: var(--oc-text-secondary);
  margin-top: 4px;
}

.metric-card--success .metric-card__value { color: var(--oc-color-success); }
.metric-card--warning .metric-card__value { color: var(--oc-color-warning); }
.metric-card--danger .metric-card__value { color: var(--oc-color-danger); }

.chart-row {
  margin-bottom: 16px;
  flex-shrink: 0;
}

.chart-card :deep(.el-card__body) {
  padding: 12px 20px 16px;
}

.trend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
</style>
