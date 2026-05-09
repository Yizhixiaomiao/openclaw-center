<template>
  <div class="machine-detail">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
      <span class="page-title">机器详情</span>
    </div>

    <!-- 基本信息 -->
    <el-card v-loading="loading" shadow="never" class="info-card">
      <template #header>
        <span>基本信息</span>
      </template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="编号">{{ machine.id }}</el-descriptions-item>
        <el-descriptions-item label="机器码">{{ machine.code }}</el-descriptions-item>
        <el-descriptions-item label="主机名">{{ machine.hostname }}</el-descriptions-item>
        <el-descriptions-item label="IP">{{ machine.ip }}</el-descriptions-item>
        <el-descriptions-item label="系统">{{ machine.os }}</el-descriptions-item>
        <el-descriptions-item label="CPU">{{ machine.cpu }}</el-descriptions-item>
        <el-descriptions-item label="内存">{{ machine.memory }}</el-descriptions-item>
        <el-descriptions-item label="CPU使用率">
          <span v-if="machine.cpu_usage != null">{{ machine.cpu_usage.toFixed(1) }}%</span>
          <span v-else style="color: #ccc">-</span>
        </el-descriptions-item>
        <el-descriptions-item label="内存使用率">
          <span v-if="machine.memory_usage != null">{{ machine.memory_usage.toFixed(1) }}%</span>
          <span v-else style="color: #ccc">-</span>
        </el-descriptions-item>
        <el-descriptions-item label="磁盘使用率">
          <span v-if="machine.disk_usage != null">{{ machine.disk_usage.toFixed(1) }}%</span>
          <span v-else style="color: #ccc">-</span>
        </el-descriptions-item>
        <el-descriptions-item label="用户ID">{{ machine.user_id }}</el-descriptions-item>
        <el-descriptions-item label="当前用户">{{ machine.current_user || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTagType(machine.status)">{{ statusLabel(machine.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="最近心跳">
          {{ machine.last_heartbeat_at ? formatDateTime(machine.last_heartbeat_at) : '从未上线' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 标签页 -->
    <el-card shadow="never" class="tabs-card">
      <el-tabs v-model="activeTab">
        <!-- Agent 信息 -->
        <el-tab-pane label="Agent信息" name="agent">
          <div v-if="machine.agent">
            <el-descriptions :column="2" border style="margin-bottom: 16px">
              <el-descriptions-item label="Agent版本">{{ machine.agent.agent_version || '-' }}</el-descriptions-item>
              <el-descriptions-item label="服务状态">
                <el-tag :type="machine.agent.service_status === 'running' ? 'success' : 'danger'">
                  {{ machine.agent.service_status === 'running' ? '运行中' : '已停止' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="最近上报时间">
                {{ machine.agent.last_report_at ? formatDateTime(machine.agent.last_report_at) : '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="配置文件路径">{{ machine.agent.agent_config_path || '-' }}</el-descriptions-item>
            </el-descriptions>
            <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600">Agent 配置</span>
              <el-button type="primary" size="small" :loading="agentConfigSaving" @click="saveAgentConfig">保存并同步</el-button>
            </div>
            <el-input
              v-model="agentConfigContent"
              type="textarea"
              :rows="16"
              placeholder="暂无Agent配置"
              style="font-family: monospace"
            />
          </div>
          <el-empty v-else description="暂无Agent信息" />
        </el-tab-pane>

        <!-- 配置摘要 -->
        <el-tab-pane label="配置摘要" name="config">
          <div v-if="machine.config">
            <el-descriptions :column="2" border style="margin-bottom: 16px">
              <el-descriptions-item label="模型供应商">{{ machine.config.model_provider || '-' }}</el-descriptions-item>
              <el-descriptions-item label="模型名称">{{ machine.config.model_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="配置版本">{{ machine.config.config_version || '-' }}</el-descriptions-item>
              <el-descriptions-item label="配置文件路径">{{ machine.config.config_file_path || '-' }}</el-descriptions-item>
            </el-descriptions>
            <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600">配置内容</span>
              <el-button type="primary" size="small" :loading="configSaving" @click="saveConfig">保存并同步</el-button>
            </div>
            <el-input
              v-model="configContent"
              type="textarea"
              :rows="16"
              placeholder="暂无配置内容"
              style="font-family: monospace"
            />
          </div>
          <el-empty v-else description="暂无配置信息" />
        </el-tab-pane>

        <!-- 已安装技能 -->
        <el-tab-pane label="已安装技能" name="skills">
          <el-table :data="machine.skills || []" border stripe style="width: 100%">
            <el-table-column prop="name" label="技能名称" min-width="150" show-overflow-tooltip />
            <el-table-column prop="installed_version" label="安装版本" min-width="120" />
            <el-table-column prop="status" label="状态" width="120" align="center">
              <template #default="{ row }">
                <el-tag :type="skillStatusType(row.status)">{{ skillStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="查看" width="80" align="center">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="showSkillDetail(row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!machine.skills || machine.skills.length === 0" description="暂无已安装技能" />
        </el-tab-pane>

        <!-- 分发记录 -->
        <el-tab-pane label="分发记录" name="deploys">
          <el-table :data="machine.deploy_items || []" border stripe style="width: 100%">
            <el-table-column prop="task_id" label="任务ID" min-width="80" align="center" />
            <el-table-column prop="status" label="状态" width="120" align="center">
              <template #default="{ row }">
                <el-tag :type="deployStatusType(row.status)">{{ deployStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="消息" min-width="200" show-overflow-tooltip />
            <el-table-column prop="finished_at" label="完成时间" width="180" align="center">
              <template #default="{ row }">
                {{ row.finished_at ? formatDateTime(row.finished_at) : '-' }}
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!machine.deploy_items || machine.deploy_items.length === 0" description="暂无分发记录" />
        </el-tab-pane>

        <!-- 最近日志 -->
        <el-tab-pane label="最近日志" name="logs">
          <el-table :data="machine.logs || []" border stripe style="width: 100%">
            <el-table-column prop="level" label="级别" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="logLevelType(row.level)" size="small">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="120" align="center" />
            <el-table-column prop="message" label="消息" min-width="300" show-overflow-tooltip />
            <el-table-column prop="created_at" label="时间" width="180" align="center">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!machine.logs || machine.logs.length === 0" description="暂无日志记录" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 技能详情弹窗 -->
    <el-dialog v-model="skillDetailVisible" title="技能详情" width="800px" destroy-on-close>
      <div v-loading="skillDetailLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="技能ID">{{ skillDetail.id }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{ skillDetail.name }}</el-descriptions-item>
          <el-descriptions-item label="编码">{{ skillDetail.code }}</el-descriptions-item>
          <el-descriptions-item label="版本">{{ skillDetail.version || '-' }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ skillDetail.description || '-' }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin: 20px 0 10px">已安装机器</h4>
        <el-table :data="skillDetailMachines" border stripe style="width: 100%">
          <el-table-column prop="machine_code" label="机器码" min-width="160" />
          <el-table-column prop="hostname" label="主机名" min-width="130" />
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'installed' ? 'success' : 'info'" size="small">
                {{ row.status === 'installed' ? '已安装' : row.status }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="skillDetailMachines.length === 0" description="暂无机器安装此技能" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getMachine, updateMachineConfig, updateAgentConfig } from '../../api/machine'
import { getSkillDetail } from '../../api/skill'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const machineId = route.params.id

const loading = ref(false)
const machine = ref({})
const activeTab = ref('agent')

// ---------- 状态映射 ----------
const statusTagType = (status) => {
  const map = { online: 'success', offline: 'info', error: 'danger', pending_init: 'warning', disabled: 'info' }
  return map[status] || ''
}
const statusLabel = (status) => {
  const map = { online: '在线', offline: '离线', error: '异常', pending_init: '待初始化', disabled: '已禁用' }
  return map[status] || status
}

const skillStatusType = (status) => {
  const map = { active: 'success', inactive: 'info', updating: 'warning', error: 'danger' }
  return map[status] || ''
}
const skillStatusLabel = (status) => {
  const map = { active: '正常', inactive: '未激活', updating: '更新中', error: '异常' }
  return map[status] || status
}

const deployStatusType = (status) => {
  const map = { pending: 'info', running: 'warning', success: 'success', failed: 'danger', cancelled: 'info' }
  return map[status] || ''
}
const deployStatusLabel = (status) => {
  const map = { pending: '待执行', running: '执行中', success: '成功', failed: '失败', cancelled: '已取消' }
  return map[status] || status
}

const logLevelType = (level) => {
  const map = { DEBUG: '', INFO: 'success', WARNING: 'warning', ERROR: 'danger', CRITICAL: 'danger' }
  return map[level] || ''
}

// ---------- 时间格式化 ----------
function formatDateTime(val) {
  if (!val) return '-'
  const d = new Date(val)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

// ---------- 数据加载 ----------
async function loadData() {
  loading.value = true
  try {
    const res = await getMachine(machineId)
    machine.value = res.data || res
    if (machine.value.config?.config_content) {
      configContent.value = machine.value.config.config_content
    }
    if (machine.value.agent?.agent_config_content) {
      agentConfigContent.value = machine.value.agent.agent_config_content
    }
  } catch {
    // 已由拦截器处理
  } finally {
    loading.value = false
  }
}

// ---------- 配置编辑 ----------
const configContent = ref('')
const configSaving = ref(false)

async function saveConfig() {
  try {
    JSON.parse(configContent.value)
  } catch {
    ElMessage.error('配置内容不是有效的 JSON 格式')
    return
  }
  configSaving.value = true
  try {
    await updateMachineConfig(machineId, { config_content: configContent.value })
    ElMessage.success('配置已保存，同步任务已下发')
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    configSaving.value = false
  }
}

// ---------- Agent 配置编辑 ----------
const agentConfigContent = ref('')
const agentConfigSaving = ref(false)

async function saveAgentConfig() {
  agentConfigSaving.value = true
  try {
    await updateAgentConfig(machineId, { agent_config_content: agentConfigContent.value })
    ElMessage.success('Agent配置已保存，同步任务已下发')
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    agentConfigSaving.value = false
  }
}

// ---------- 技能详情弹窗 ----------
const skillDetailVisible = ref(false)
const skillDetailLoading = ref(false)
const skillDetail = ref({})
const skillDetailMachines = ref([])

async function showSkillDetail(row) {
  skillDetailVisible.value = true
  skillDetailLoading.value = true
  skillDetail.value = {}
  skillDetailMachines.value = []
  try {
    const res = await getSkillDetail(row.skill_id)
    skillDetail.value = res.skill || {}
    skillDetailMachines.value = res.machines || []
  } catch {
    // handled by interceptor
  } finally {
    skillDetailLoading.value = false
  }
}

function goBack() {
  router.push('/machines')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.machine-detail {
  padding: 16px;
}
.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}
.page-title {
  font-size: 16px;
  font-weight: 600;
  margin-left: 12px;
}
.info-card {
  margin-bottom: 16px;
}
.tabs-card {
  margin-bottom: 16px;
}
</style>
