<template>
  <div class="oc-page">
    <!-- 顶部操作栏 -->
    <div class="oc-page-header">
      <div style="display: flex; align-items: center; gap: 12px;">
        <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
        <h1 class="oc-page-header__title">机器详情</h1>
      </div>
    </div>

    <!-- 基本信息 -->
    <el-card v-loading="loading" shadow="never" class="oc-table-card">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>基本信息</span>
          <div v-if="!isEditingBasic">
            <el-button type="primary" size="small" @click="startEditBasic">编辑</el-button>
          </div>
          <div v-else>
            <el-button size="small" @click="cancelEditBasic">取消</el-button>
            <el-button type="primary" size="small" :loading="savingBasic" @click="saveBasicInfo">保存</el-button>
          </div>
        </div>
      </template>
      <!-- 查看模式 -->
      <el-descriptions v-if="!isEditingBasic" :column="3" border>
        <el-descriptions-item label="编号">{{ machine.id }}</el-descriptions-item>
        <el-descriptions-item label="机器码">{{ machine.code }}</el-descriptions-item>
        <el-descriptions-item label="主机名">{{ machine.hostname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="IP">{{ machine.ip || '-' }}</el-descriptions-item>
        <el-descriptions-item label="MAC">{{ machine.mac || '-' }}</el-descriptions-item>
        <el-descriptions-item label="部门">{{ machine.department || '-' }}</el-descriptions-item>
        <el-descriptions-item label="系统">{{ machine.os }}</el-descriptions-item>
        <el-descriptions-item label="CPU">{{ machine.cpu }}</el-descriptions-item>
        <el-descriptions-item label="内存">{{ machine.memory }}</el-descriptions-item>
        <el-descriptions-item label="CPU使用率">
          <span v-if="machine.cpu_usage != null">{{ machine.cpu_usage.toFixed(1) }}%</span>
          <span v-else class="oc-text-placeholder">-</span>
        </el-descriptions-item>
        <el-descriptions-item label="内存使用率">
          <span v-if="machine.memory_usage != null">{{ machine.memory_usage.toFixed(1) }}%</span>
          <span v-else class="oc-text-placeholder">-</span>
        </el-descriptions-item>
        <el-descriptions-item label="磁盘使用率">
          <span v-if="machine.disk_usage != null">{{ machine.disk_usage.toFixed(1) }}%</span>
          <span v-else class="oc-text-placeholder">-</span>
        </el-descriptions-item>
        <el-descriptions-item label="使用人">{{ machine.operator || '-' }}</el-descriptions-item>
        <el-descriptions-item label="当前用户">{{ machine.current_user || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTagType(machine.status)">{{ statusLabel(machine.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="最近心跳">
          {{ machine.last_heartbeat_at ? formatDateTime(machine.last_heartbeat_at) : '从未上线' }}
        </el-descriptions-item>
        <el-descriptions-item v-if="accessLinks.length" label="远程访问">
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <el-button v-for="link in accessLinks" :key="link.url" type="primary" size="small" @click="openAccessLink(link.url)">{{ link.label }}</el-button>
          </div>
        </el-descriptions-item>
      </el-descriptions>
      <!-- 编辑模式 -->
      <el-form v-else ref="basicFormRef" :model="editForm" :rules="basicFormRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="编号">
              <el-input :model-value="String(machine.id)" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="机器码">
              <el-input :model-value="machine.code" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="主机名" prop="hostname">
              <el-input v-model="editForm.hostname" placeholder="请输入主机名" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="IP" prop="ip">
              <el-input v-model="editForm.ip" placeholder="请输入IP地址" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="MAC" prop="mac">
              <el-input v-model="editForm.mac" placeholder="请输入MAC地址" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="部门" prop="department">
              <el-input v-model="editForm.department" placeholder="请输入部门" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="系统">
              <el-input :model-value="machine.os" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="CPU">
              <el-input :model-value="machine.cpu" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="内存">
              <el-input :model-value="machine.memory" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="使用人" prop="operator">
              <el-input v-model="editForm.operator" placeholder="请输入使用人" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="状态">
              <el-tag :type="statusTagType(machine.status)">{{ statusLabel(machine.status) }}</el-tag>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最近心跳">
              <span style="color: var(--oc-text-secondary); font-size: 13px">
                {{ machine.last_heartbeat_at ? formatDateTime(machine.last_heartbeat_at) : '从未上线' }}
              </span>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 标签页 -->
    <el-card shadow="never" class="oc-table-card">
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

            <!-- 用户设定目录配置 -->
            <el-card shadow="never" style="margin-bottom: 16px; border: 1px dashed var(--oc-border-color);">
              <template #header>
                <span style="font-weight: 600">用户设定目录</span>
              </template>
              <el-form :inline="true" style="margin-bottom: 0">
                <el-form-item label="目录路径" style="margin-bottom: 0; flex: 1">
                  <el-input v-model="profilesDir" placeholder="如 C:\OpenClaw\profiles" style="width: 400px" />
                </el-form-item>
                <el-form-item style="margin-bottom: 0">
                  <el-button type="primary" size="small" :loading="profilesDirSaving" @click="saveProfilesDir">保存并下发</el-button>
                </el-form-item>
              </el-form>
              <div style="color: var(--oc-text-tertiary); font-size: 12px; margin-top: 8px">
                用于存放 USER.md 和 IDENTITY.md 文件，Agent 将从此目录采集用户设定信息
              </div>
            </el-card>

            <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600">Agent 配置</span>
              <div>
                <el-button size="small" :loading="syncing" @click="handleSync">同步</el-button>
                <el-button type="primary" size="small" :loading="agentConfigSaving" @click="saveAgentConfig">保存并下发</el-button>
              </div>
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
              <div>
                <el-button size="small" :loading="syncing" @click="handleSync">同步</el-button>
                <el-button type="primary" size="small" :loading="configSaving" @click="saveConfig">保存并下发</el-button>
              </div>
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

        <!-- 用户设定 -->
        <el-tab-pane label="用户设定" name="profiles">
          <div v-if="machine.agent">
            <el-descriptions :column="1" border style="margin-bottom: 16px">
              <el-descriptions-item label="配置目录">{{ machine.agent.profiles_dir || '-' }}</el-descriptions-item>
            </el-descriptions>

            <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600">USER.md</span>
              <div>
                <el-button size="small" :loading="syncing" @click="handleSync">同步</el-button>
                <el-button type="primary" size="small" :loading="profilesSaving" @click="saveProfiles">保存并下发</el-button>
              </div>
            </div>
            <el-input
              v-model="userMdContent"
              type="textarea"
              :rows="10"
              placeholder="暂无 USER.md 内容"
              style="font-family: monospace; margin-bottom: 20px"
            />

            <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600">IDENTITY.md</span>
            </div>
            <el-input
              v-model="identifyMdContent"
              type="textarea"
              :rows="10"
              placeholder="暂无 IDENTITY.md 内容"
              style="font-family: monospace"
            />
          </div>
          <el-empty v-else description="暂无Agent信息" />
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
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getMachine, updateMachine, updateMachineConfig, updateAgentConfig, syncMachine as syncMachineApi, updateMachineProfiles } from '../../api/machine'
import { getSkillDetail } from '../../api/skill'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const machineId = route.params.id

const loading = ref(false)
const machine = ref({})
const accessLinks = ref([])
const activeTab = ref('agent')

// ---------- 基本信息编辑 ----------
const isEditingBasic = ref(false)
const savingBasic = ref(false)
const basicFormRef = ref(null)
const editForm = reactive({
  hostname: '',
  ip: '',
  mac: '',
  department: '',
  operator: '',
})

const basicFormRules = {
  hostname: [{ required: true, message: '请输入主机名', trigger: 'blur' }],
}

function startEditBasic() {
  editForm.hostname = machine.value.hostname || ''
  editForm.ip = machine.value.ip || ''
  editForm.mac = machine.value.mac || ''
  editForm.department = machine.value.department || ''
  editForm.operator = machine.value.operator || ''
  isEditingBasic.value = true
}

function cancelEditBasic() {
  isEditingBasic.value = false
}

async function saveBasicInfo() {
  try {
    await basicFormRef.value?.validate()
  } catch {
    return
  }
  savingBasic.value = true
  try {
    await updateMachine(machineId, {
      hostname: editForm.hostname,
      ip: editForm.ip,
      mac: editForm.mac,
      department: editForm.department,
      operator: editForm.operator,
    })
    ElMessage.success('基本信息已保存')
    isEditingBasic.value = false
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    savingBasic.value = false
  }
}

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
    const data = res.data || res
    // Backend returns {machine, agent, config, skills, recent_logs, recent_deploys}
    // Flatten so template can access machine fields directly
    machine.value = {
      ...(data.machine || {}),
      agent: data.agent || null,
      config: data.config || null,
      skills: data.skills || [],
      logs: data.recent_logs || [],
      deploy_items: data.recent_deploys || [],
    }
    accessLinks.value = data.access_links || []
    if (machine.value.config?.config_content) {
      configContent.value = machine.value.config.config_content
    }
    if (machine.value.agent?.agent_config_content) {
      agentConfigContent.value = machine.value.agent.agent_config_content
    }
    if (machine.value.agent?.user_md_content) {
      userMdContent.value = machine.value.agent.user_md_content
    }
    if (machine.value.agent?.identify_md_content) {
      identifyMdContent.value = machine.value.agent.identify_md_content
    }
    if (machine.value.agent?.profiles_dir) {
      profilesDir.value = machine.value.agent.profiles_dir
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

// ---------- 用户设定编辑 ----------
const userMdContent = ref('')
const identifyMdContent = ref('')
const profilesSaving = ref(false)
const profilesDir = ref('')
const profilesDirSaving = ref(false)

async function saveProfiles() {
  profilesSaving.value = true
  try {
    await updateMachineProfiles(machineId, {
      user_md_content: userMdContent.value,
      identify_md_content: identifyMdContent.value,
    })
    ElMessage.success('用户设定已保存，同步任务已下发')
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    profilesSaving.value = false
  }
}

async function saveProfilesDir() {
  profilesDirSaving.value = true
  try {
    // Inject openclaw_profiles_dir into agent config YAML and save both
    const dir = profilesDir.value.trim()
    let yaml = agentConfigContent.value
    if (yaml.includes('openclaw_profiles_dir:')) {
      yaml = yaml.replace(/openclaw_profiles_dir:\s*.*/, `openclaw_profiles_dir: '${dir}'`)
    } else {
      yaml = yaml.trimEnd() + `\n\n# OpenClaw profiles directory containing USER.md and IDENTITY.md (optional)\nopenclaw_profiles_dir: '${dir}'\n`
    }
    agentConfigContent.value = yaml
    await updateAgentConfig(machineId, { agent_config_content: yaml })
    ElMessage.success('用户设定目录已保存，同步任务已下发')
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    profilesDirSaving.value = false
  }
}

// ---------- 手动同步 ----------
const syncing = ref(false)

async function handleSync() {
  syncing.value = true
  try {
    await syncMachineApi(machineId)
    ElMessage.success('同步指令已下发')
  } catch {
    // handled by interceptor
  } finally {
    syncing.value = false
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

function openAccessLink(url) {
  window.open(url, '_blank')
}

function goBack() {
  router.push('/machines')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
</style>
