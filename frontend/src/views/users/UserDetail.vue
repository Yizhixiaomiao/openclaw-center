<template>
  <div class="user-detail">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
      <span class="page-title">用户详情</span>
    </div>

    <!-- 基本信息 -->
    <el-card v-loading="loading" shadow="never" class="info-card">
      <template #header>
        <span>基本信息</span>
      </template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="姓名">{{ user.name }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ user.username }}</el-descriptions-item>
        <el-descriptions-item label="公司">{{ user.company }}</el-descriptions-item>
        <el-descriptions-item label="部门">{{ user.department }}</el-descriptions-item>
        <el-descriptions-item label="岗位">{{ user.position }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ user.phone }}</el-descriptions-item>
        <el-descriptions-item label="运维负责人">{{ user.support_owner }}</el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag :type="roleTagType(user.role)">{{ roleLabel(user.role) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="user.status === 'active' ? 'success' : 'danger'">
            {{ user.status === 'active' ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 标签页 -->
    <el-card shadow="never" class="tabs-card">
      <el-tabs v-model="activeTab">
        <!-- 职责画像 -->
        <el-tab-pane label="职责画像" name="profile">
          <div v-if="!profileEditing" class="profile-view">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="职责">{{ profile.duties || '-' }}</el-descriptions-item>
              <el-descriptions-item label="常用文件">{{ profile.frequent_files || '-' }}</el-descriptions-item>
              <el-descriptions-item label="输出报表">{{ profile.output_reports || '-' }}</el-descriptions-item>
              <el-descriptions-item label="使用频率">{{ profile.usage_frequency || '-' }}</el-descriptions-item>
              <el-descriptions-item label="优先级">{{ profile.priority || '-' }}</el-descriptions-item>
              <el-descriptions-item label="备注" :span="2">{{ profile.notes || '-' }}</el-descriptions-item>
            </el-descriptions>
            <el-button type="primary" style="margin-top: 16px" @click="startEditProfile">编辑</el-button>
          </div>

          <el-form v-else ref="profileFormRef" :model="profileForm" label-width="100px" style="max-width: 600px">
            <el-form-item label="职责">
              <el-input v-model="profileForm.duties" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="常用文件">
              <el-input v-model="profileForm.frequent_files" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="输出报表">
              <el-input v-model="profileForm.output_reports" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="使用频率">
              <el-select v-model="profileForm.usage_frequency" placeholder="请选择" clearable style="width: 100%">
                <el-option label="高频" value="high" />
                <el-option label="中频" value="medium" />
                <el-option label="低频" value="low" />
              </el-select>
            </el-form-item>
            <el-form-item label="优先级">
              <el-select v-model="profileForm.priority" placeholder="请选择" clearable style="width: 100%">
                <el-option label="高" value="high" />
                <el-option label="中" value="medium" />
                <el-option label="低" value="low" />
              </el-select>
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model="profileForm.notes" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="profileSaving" @click="saveProfile">保存</el-button>
              <el-button @click="profileEditing = false">取消</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 业务场景 -->
        <el-tab-pane label="业务场景" name="scenarios">
          <el-table :data="scenarios" border stripe style="width: 100%">
            <el-table-column prop="id" label="ID" width="70" align="center" />
            <el-table-column prop="name" label="场景名称" min-width="160" />
            <el-table-column prop="scenario_type" label="类型" width="120" align="center">
              <template #default="{ row }">
                {{ scenarioTypeLabel(row.scenario_type) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="130" align="center">
              <template #default="{ row }">
                <el-tag :type="scenarioStatusType(row.status)">{{ scenarioStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180" align="center">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 绑定机器 -->
        <el-tab-pane label="绑定机器" name="machines">
          <el-table :data="machines" border stripe style="width: 100%">
            <el-table-column prop="code" label="机器码" min-width="160" />
            <el-table-column prop="hostname" label="主机名" min-width="130" />
            <el-table-column prop="ip" label="IP" width="140" />
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="machineStatusType(row.status)">{{ machineStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="last_heartbeat_at" label="最近心跳" width="180" align="center">
              <template #default="{ row }">
                {{ row.last_heartbeat_at ? formatDateTime(row.last_heartbeat_at) : '从未上线' }}
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getUser, getUserProfile, updateUserProfile, getUserScenarios } from '../../api/user'
import { getMachines } from '../../api/machine'

const route = useRoute()
const router = useRouter()
const userId = route.params.id

const loading = ref(false)
const user = ref({})
const profile = ref({})
const scenarios = ref([])
const machines = ref([])
const activeTab = ref('profile')

// ---------- 角色工具函数 ----------
const roleTagType = (role) => {
  const map = { admin: 'danger', support: 'warning', ops: 'info', manager: 'success', user: '' }
  return map[role] || ''
}
const roleLabel = (role) => {
  const map = { admin: '管理员', support: '运维', ops: '运营', manager: '经理', user: '普通用户' }
  return map[role] || role
}

// ---------- 场景状态 ----------
const scenarioStatusType = (status) => {
  const map = {
    pending: 'info', organized: '', prompt_generated: 'warning', skill_configured: 'primary',
    testing: 'warning', online: 'success', needs_optimization: 'danger', paused: 'info',
  }
  return map[status] || ''
}
const scenarioStatusLabel = (status) => {
  const map = {
    pending: '待处理', organized: '已整理', prompt_generated: '已生成提示词',
    skill_configured: '已配置技能', testing: '测试中', online: '已上线',
    needs_optimization: '需优化', paused: '已暂停',
  }
  return map[status] || status
}
const scenarioTypeLabel = (type) => {
  const map = { data_query: '数据查询', report_generation: '报表生成', workflow: '工作流', automation: '自动化' }
  return map[type] || type
}

// ---------- 机器状态 ----------
const machineStatusType = (status) => {
  const map = { online: 'success', offline: 'info', error: 'danger', pending_init: 'warning', disabled: 'info' }
  return map[status] || ''
}
const machineStatusLabel = (status) => {
  const map = { online: '在线', offline: '离线', error: '异常', pending_init: '待初始化', disabled: '已禁用' }
  return map[status] || status
}

// ---------- 时间格式化 ----------
function formatDateTime(val) {
  if (!val) return '-'
  const d = new Date(val)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

// ---------- 职责画像编辑 ----------
const profileEditing = ref(false)
const profileSaving = ref(false)
const profileFormRef = ref(null)
const profileForm = reactive({
  duties: '',
  frequent_files: '',
  output_reports: '',
  usage_frequency: '',
  priority: '',
  notes: '',
})

function startEditProfile() {
  Object.keys(profileForm).forEach((k) => {
    profileForm[k] = profile.value[k] || ''
  })
  profileEditing.value = true
}

async function saveProfile() {
  profileSaving.value = true
  try {
    await updateUserProfile(userId, { ...profileForm })
    ElMessage.success('画像更新成功')
    profileEditing.value = false
    await loadProfile()
  } catch {
    // 已由拦截器处理
  } finally {
    profileSaving.value = false
  }
}

// ---------- 数据加载 ----------
async function loadUser() {
  loading.value = true
  try {
    const res = await getUser(userId)
    user.value = res.data || res
  } catch {
    // 已由拦截器处理
  } finally {
    loading.value = false
  }
}

async function loadProfile() {
  try {
    const res = await getUserProfile(userId)
    profile.value = res.data || res
  } catch {
    // 可能 404 - 用户暂无画像
  }
}

async function loadScenarios() {
  try {
    const res = await getUserScenarios(userId)
    scenarios.value = res.items || res.data || res || []
  } catch {
    // 静默
  }
}

async function loadMachines() {
  try {
    const res = await getMachines({ user_id: userId })
    machines.value = res.items || res.data || res || []
  } catch {
    // 静默
  }
}

function goBack() {
  router.push('/users')
}

onMounted(() => {
  loadUser()
  loadProfile()
  loadScenarios()
  loadMachines()
})
</script>

<style scoped>
.user-detail {
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
