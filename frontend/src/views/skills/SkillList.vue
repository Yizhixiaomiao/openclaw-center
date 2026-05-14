<template>
  <div class="oc-page">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- Tab 1: 本地技能 -->
      <el-tab-pane label="本地技能" name="local">
    <!-- 搜索筛选区 -->
    <el-card class="oc-filter-card" shadow="never">
      <el-form :model="filters" inline>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="全字段搜索" clearable style="width: 180px" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="机器IP">
          <el-select v-model="filters.machine_ip" placeholder="全部IP" clearable style="width: 160px" @change="handleSearch">
            <el-option v-for="ip in machineIps" :key="ip" :label="ip" :value="ip" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card shadow="never" class="oc-table-card">
      <el-table v-loading="loading" :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="code" label="编码" min-width="140" show-overflow-tooltip />
        <el-table-column prop="version" label="版本" width="90" align="center" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="来源" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.source === 'clawhub'" type="warning" size="small">ClawHub</el-tag>
            <el-tag v-else type="info" size="small">本地</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="已安装机器" width="100" align="center">
          <template #default="{ row }">
            <el-link type="primary" :underline="false" @click="showDetail(row.id)" style="cursor: pointer">
              {{ row.machines?.length || 0 }} 台
            </el-link>
          </template>
        </el-table-column>
        <el-table-column label="来源IP" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.machines && row.machines.length > 0">{{ row.machines[0].ip || '-' }}</span>
            <span v-else class="oc-text-placeholder">-</span>
          </template>
        </el-table-column>
        <el-table-column label="来源主机名" min-width="130" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.machines && row.machines.length > 0">{{ row.machines[0].hostname || '-' }}</span>
            <span v-else class="oc-text-placeholder">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="showDetail(row.id)">查看</el-button>
            <el-button link type="success" size="small" @click="openDistributeDialog(row)">分发</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="oc-pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>
      </el-tab-pane>

      <!-- Tab 2: ClawHub 市场 -->
      <el-tab-pane label="ClawHub 市场" name="clawhub">
        <!-- 搜索和排序 -->
        <el-card class="oc-filter-card" shadow="never">
          <el-form :inline="true" @submit.prevent="searchClawHub">
            <el-form-item label="搜索">
              <el-input v-model="clawhubQuery" placeholder="搜索技能名称/描述" clearable style="width: 260px" @keyup.enter="searchClawHub" />
            </el-form-item>
            <el-form-item label="排序">
              <el-select v-model="clawhubSort" style="width: 140px" @change="loadClawHubSkills">
                <el-option label="热门趋势" value="trending" />
                <el-option label="下载最多" value="downloads" />
                <el-option label="评分最高" value="stars" />
                <el-option label="最新发布" value="newest" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="searchClawHub">搜索</el-button>
              <el-button @click="resetClawHubSearch">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- ClawHub 技能列表 -->
        <el-card shadow="never" class="oc-table-card" v-loading="clawhubLoading">
          <el-table v-if="clawhubSearchMode" :data="clawhubSearchResults" border stripe style="width: 100%">
            <el-table-column prop="slug" label="Slug" min-width="140" show-overflow-tooltip />
            <el-table-column prop="displayName" label="名称" min-width="140" show-overflow-tooltip />
            <el-table-column prop="summary" label="描述" min-width="240" show-overflow-tooltip />
            <el-table-column label="操作" width="120" align="center">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openClawHubInstallDialog(row.slug, row.displayName)">安装</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-table v-else :data="clawhubSkills" border stripe style="width: 100%">
            <el-table-column prop="slug" label="Slug" min-width="140" show-overflow-tooltip />
            <el-table-column prop="displayName" label="名称" min-width="140" show-overflow-tooltip />
            <el-table-column prop="summary" label="描述" min-width="240" show-overflow-tooltip />
            <el-table-column label="版本" width="80" align="center">
              <template #default="{ row }">
                {{ row.latestVersion?.version || row.tags?.latest || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="下载" width="90" align="center">
              <template #default="{ row }">
                {{ row.stats?.downloads ? (row.stats.downloads >= 1000 ? (row.stats.downloads / 1000).toFixed(1) + 'k' : row.stats.downloads) : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="安装数" width="90" align="center">
              <template #default="{ row }">
                {{ row.stats?.installsCurrent ?? '-' }}
              </template>
            </el-table-column>
            <el-table-column label="评分" width="80" align="center">
              <template #default="{ row }">
                {{ row.stats?.stars ?? '-' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" align="center">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openClawHubInstallDialog(row.slug, row.displayName)">安装</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="oc-pagination" v-if="!clawhubSearchMode && clawhubNextCursor">
            <el-button type="primary" link @click="loadMoreClawHub">加载更多</el-button>
          </div>
          <div class="oc-pagination" v-if="!clawhubSearchMode && !clawhubNextCursor && clawhubSkills.length > 0">
            <span class="oc-text-secondary">没有更多了</span>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 新增技能对话框 -->
    <el-dialog v-model="dialogVisible" title="新增技能" width="600px" destroy-on-close @closed="resetForm">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入技能名称" />
        </el-form-item>
        <el-form-item label="编码" prop="code">
          <el-input v-model="formData.code" placeholder="请输入技能编码" />
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="formData.version" placeholder="如 1.0.0" style="width: 200px" />
        </el-form-item>
        <el-form-item label="适用岗位">
          <el-select v-model="formData.applicable_positions" multiple placeholder="请选择适用岗位" style="width: 100%">
            <el-option v-for="p in positionOptions" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="4" placeholder="请输入技能描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 分发技能对话框 -->
    <el-dialog v-model="distributeVisible" title="分发技能" width="720px" destroy-on-close @closed="resetDistribute">
      <div style="margin-bottom: 16px">
        <span>技能：<strong>{{ distributeSkill?.name }}</strong>（{{ distributeSkill?.code }}）</span>
      </div>
      <el-form label-width="90px" style="margin-bottom: 12px">
        <el-form-item label="安装路径">
          <el-input v-model="installPath" placeholder="留空则自动使用 Agent 配置的技能目录" />
        </el-form-item>
      </el-form>
      <el-form inline style="margin-bottom: 8px">
        <el-form-item label="筛选">
          <el-input v-model="machineFilter" placeholder="机器码/主机名/IP" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="deptFilter" placeholder="全部部门" clearable style="width: 160px">
            <el-option v-for="d in departments" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-table
        :data="filteredMachines"
        border
        height="320"
        style="width: 100%"
        @selection-change="onMachineSelect"
      >
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column prop="code" label="机器码" min-width="140" />
        <el-table-column prop="hostname" label="主机名" width="140" />
        <el-table-column prop="ip" label="IP" width="140" />
        <el-table-column prop="department" label="部门" width="120" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : 'info'" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div class="oc-text-secondary" style="margin-top: 8px; font-size: 12px">
        已选择 {{ selectedMachines.length }} 台机器
      </div>
      <template #footer>
        <el-button @click="distributeVisible = false">取消</el-button>
        <el-button type="primary" :loading="distributing" @click="handleDistribute">确认分发</el-button>
      </template>
    </el-dialog>

    <!-- ClawHub 安装对话框 -->
    <el-dialog v-model="clawhubInstallVisible" title="从 ClawHub 安装技能" width="720px" destroy-on-close @closed="resetClawHubInstall">
      <div style="margin-bottom: 16px">
        <span>技能：<strong>{{ clawhubInstallName }}</strong>（{{ clawhubInstallSlug }}）</span>
      </div>
      <el-form label-width="90px" style="margin-bottom: 12px">
        <el-form-item label="安装路径">
          <el-input v-model="clawhubInstallPath" placeholder="留空则自动使用 Agent 配置的技能目录" />
        </el-form-item>
      </el-form>
      <el-form inline style="margin-bottom: 8px">
        <el-form-item label="筛选">
          <el-input v-model="clawhubMachineFilter" placeholder="机器码/主机名/IP" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="clawhubDeptFilter" placeholder="全部部门" clearable style="width: 160px">
            <el-option v-for="d in departments" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-table
        :data="clawhubFilteredMachines"
        border
        height="320"
        style="width: 100%"
        @selection-change="onClawHubMachineSelect"
      >
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column prop="code" label="机器码" min-width="140" />
        <el-table-column prop="hostname" label="主机名" width="140" />
        <el-table-column prop="ip" label="IP" width="140" />
        <el-table-column prop="department" label="部门" width="120" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : 'info'" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div class="oc-text-secondary" style="margin-top: 8px; font-size: 12px">
        已选择 {{ clawhubSelectedMachines.length }} 台机器
      </div>
      <template #footer>
        <el-button @click="clawhubInstallVisible = false">取消</el-button>
        <el-button type="primary" :loading="clawhubInstalling" @click="handleClawHubInstall">确认安装</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getSkills, createSkill, getSkillDetail, deleteSkill, searchClawHubSkills, listClawHubSkills, installFromClawHub } from '../../api/skill'
import { getMachines, getMachineIps } from '../../api/machine'
import { distributeSkill as distributeSkillApi } from '../../api/deploy'

const router = useRouter()

// ---------- Tabs ----------
const activeTab = ref('local')

// ---------- 筛选 ----------
const filters = reactive({
  keyword: '',
  machine_ip: '',
})

// ---------- 表格 ----------
const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, size: 20, total: 0 })

async function fetchData() {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.size,
      limit: pagination.size,
      ...filters,
    }
    Object.keys(params).forEach((k) => { if (params[k] === '' || params[k] == null) delete params[k] })
    const res = await getSkills(params)
    tableData.value = res.items || res.data || (Array.isArray(res) ? res : [])
    pagination.total = res.total || 0
    await enrichSkills()
  } catch {
    // 已由拦截器处理
  } finally {
    loading.value = false
  }
}

const skillMachinesMap = reactive({})
const machineIps = ref([])

async function loadMachineIps() {
  try {
    const res = await getMachineIps()
    machineIps.value = Array.isArray(res) ? res : []
  } catch {
    machineIps.value = []
  }
}

async function enrichSkills() {
  for (const skill of tableData.value) {
    if (!skillMachinesMap[skill.id]) {
      try {
        const detail = await getSkillDetail(skill.id)
        skillMachinesMap[skill.id] = detail.machines || []
      } catch {
        skillMachinesMap[skill.id] = []
      }
    }
    skill.machines = skillMachinesMap[skill.id]
  }
}

function handleSearch() {
  pagination.page = 1
  fetchData()
}

function handleReset() {
  Object.assign(filters, { keyword: '', machine_ip: '' })
  pagination.page = 1
  fetchData()
}

function formatDateTime(val) {
  if (!val) return '-'
  const d = new Date(val)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

// ---------- 新增对话框 ----------
const dialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const formData = reactive({
  name: '',
  code: '',
  version: '',
  applicable_positions: [],
  description: '',
})

const formRules = reactive({
  name: [{ required: true, message: '请输入技能名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入技能编码', trigger: 'blur' }],
})

const positionOptions = ['工程师', '产品经理', '设计师', '运营', '主管', '经理', '数据分析师']

function openDialog() {
  dialogVisible.value = true
}

function resetForm() {
  Object.assign(formData, { name: '', code: '', version: '', applicable_positions: [], description: '' })
  formRef.value?.resetFields()
}

async function handleSubmit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    await createSkill({ ...formData })
    ElMessage.success('技能创建成功')
    dialogVisible.value = false
    fetchData()
  } catch {
    // 已由拦截器处理
  } finally {
    submitting.value = false
  }
}

// ---------- 查看详情（跳转独立页面） ----------
function showDetail(id) {
  router.push(`/skills/${id}`)
}

// ---------- 删除技能 ----------
async function handleDelete(id) {
  const skill = tableData.value.find((s) => s.id === id)
  try {
    await ElMessageBox.confirm(`确定删除技能「${skill?.name}」吗？将同时移除所有机器的关联记录和本地文件。`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteSkill(id)
    ElMessage.success('技能已删除')
    delete skillMachinesMap[id]
    fetchData()
  } catch {
    // cancelled
  }
}

// ---------- 状态映射 ----------
const statusLabel = (status) => {
  const map = { online: '在线', offline: '离线', error: '异常', pending_init: '待初始化', disabled: '已禁用' }
  return map[status] || status
}

// ---------- 技能分发 ----------
const distributeVisible = ref(false)
const distributing = ref(false)
const distributeSkill = ref(null)
const installPath = ref('')
const allMachines = ref([])
const selectedMachines = ref([])
const machineFilter = ref('')
const deptFilter = ref('')

const departments = computed(() => {
  const set = new Set()
  allMachines.value.forEach((m) => { if (m.department) set.add(m.department) })
  return Array.from(set).sort()
})

const filteredMachines = computed(() => {
  return allMachines.value.filter((m) => {
    if (deptFilter.value && m.department !== deptFilter.value) return false
    if (machineFilter.value) {
      const kw = machineFilter.value.toLowerCase()
      const match = (m.code || '').toLowerCase().includes(kw)
        || (m.hostname || '').toLowerCase().includes(kw)
        || (m.ip || '').toLowerCase().includes(kw)
      if (!match) return false
    }
    return true
  })
})

function openDistributeDialog(row) {
  distributeSkill.value = row
  distributeVisible.value = true
}

function resetDistribute() {
  distributeSkill.value = null
  selectedMachines.value = []
  machineFilter.value = ''
  deptFilter.value = ''
}

function onMachineSelect(rows) {
  selectedMachines.value = rows
}

async function handleDistribute() {
  if (selectedMachines.value.length === 0) {
    ElMessage.warning('请至少选择一台目标机器')
    return
  }
  distributing.value = true
  try {
    await distributeSkillApi(distributeSkill.value.code, selectedMachines.value.map((m) => m.id), installPath.value)
    ElMessage.success(`技能分发成功，共 ${selectedMachines.value.length} 台机器`)
    distributeVisible.value = false
    delete skillMachinesMap[distributeSkill.value.id]
    fetchData()
  } catch {
    // handled by interceptor
  } finally {
    distributing.value = false
  }
}

async function loadMachines() {
  try {
    const res = await getMachines({ skip: 0, limit: 200 })
    allMachines.value = Array.isArray(res) ? res : (res.items || res.data || [])
  } catch {
    // ignored
  }
}

// ---------- ClawHub 市场 ----------
const clawhubQuery = ref('')
const clawhubSort = ref('trending')
const clawhubSkills = ref([])
const clawhubSearchResults = ref([])
const clawhubSearchMode = ref(false)
const clawhubNextCursor = ref(null)
const clawhubLoading = ref(false)

async function loadClawHubSkills() {
  clawhubSearchMode.value = false
  clawhubLoading.value = true
  try {
    const params = { sort: clawhubSort.value, limit: 20 }
    const res = await listClawHubSkills(params)
    clawhubSkills.value = res.items || []
    clawhubNextCursor.value = res.nextCursor || null
  } catch {
    ElMessage.error('加载 ClawHub 技能列表失败')
  } finally {
    clawhubLoading.value = false
  }
}

async function loadMoreClawHub() {
  if (!clawhubNextCursor.value) return
  clawhubLoading.value = true
  try {
    const params = { sort: clawhubSort.value, limit: 20, cursor: clawhubNextCursor.value }
    const res = await listClawHubSkills(params)
    clawhubSkills.value = [...clawhubSkills.value, ...(res.items || [])]
    clawhubNextCursor.value = res.nextCursor || null
  } catch {
    ElMessage.error('加载更多失败')
  } finally {
    clawhubLoading.value = false
  }
}

async function searchClawHub() {
  if (!clawhubQuery.value.trim()) {
    clawhubSearchMode.value = false
    return
  }
  clawhubLoading.value = true
  clawhubSearchMode.value = true
  try {
    const res = await searchClawHubSkills({ q: clawhubQuery.value.trim(), limit: 20 })
    clawhubSearchResults.value = res.results || []
  } catch {
    ElMessage.error('搜索 ClawHub 失败')
  } finally {
    clawhubLoading.value = false
  }
}

function resetClawHubSearch() {
  clawhubQuery.value = ''
  clawhubSearchMode.value = false
  clawhubSearchResults.value = []
}

// ---------- ClawHub 安装对话框 ----------
const clawhubInstallVisible = ref(false)
const clawhubInstallSlug = ref('')
const clawhubInstallName = ref('')
const clawhubInstallPath = ref('')
const clawhubMachineFilter = ref('')
const clawhubDeptFilter = ref('')
const clawhubSelectedMachines = ref([])
const clawhubInstalling = ref(false)

const clawhubFilteredMachines = computed(() => {
  return allMachines.value.filter((m) => {
    if (clawhubDeptFilter.value && m.department !== clawhubDeptFilter.value) return false
    if (clawhubMachineFilter.value) {
      const kw = clawhubMachineFilter.value.toLowerCase()
      const match = (m.code || '').toLowerCase().includes(kw)
        || (m.hostname || '').toLowerCase().includes(kw)
        || (m.ip || '').toLowerCase().includes(kw)
      if (!match) return false
    }
    return true
  })
})

function openClawHubInstallDialog(slug, displayName) {
  clawhubInstallSlug.value = slug
  clawhubInstallName.value = displayName
  clawhubInstallVisible.value = true
}

function resetClawHubInstall() {
  clawhubInstallSlug.value = ''
  clawhubInstallName.value = ''
  clawhubInstallPath.value = ''
  clawhubMachineFilter.value = ''
  clawhubDeptFilter.value = ''
  clawhubSelectedMachines.value = []
}

function onClawHubMachineSelect(rows) {
  clawhubSelectedMachines.value = rows
}

async function handleClawHubInstall() {
  if (clawhubSelectedMachines.value.length === 0) {
    ElMessage.warning('请至少选择一台目标机器')
    return
  }
  clawhubInstalling.value = true
  try {
    await installFromClawHub({
      slug: clawhubInstallSlug.value,
      machine_ids: clawhubSelectedMachines.value.map((m) => m.id),
      install_path: clawhubInstallPath.value || null,
    })
    ElMessage.success(`技能安装任务已创建，共 ${clawhubSelectedMachines.value.length} 台机器`)
    clawhubInstallVisible.value = false
    fetchData()
  } catch {
    // handled by interceptor
  } finally {
    clawhubInstalling.value = false
  }
}

// ---------- 初始化 ----------
onMounted(() => {
  fetchData()
  loadMachines()
  loadMachineIps()
  loadClawHubSkills()
})
</script>

<style scoped>
</style>
