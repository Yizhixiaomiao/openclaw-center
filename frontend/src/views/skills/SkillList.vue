<template>
  <div class="skill-list">
    <!-- 搜索筛选区 -->
    <el-card class="filter-card" shadow="never">
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
    <el-card shadow="never" class="table-card">
      <el-table v-loading="loading" :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="code" label="编码" min-width="140" show-overflow-tooltip />
        <el-table-column prop="version" label="版本" width="90" align="center" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
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
            <span v-else style="color: #ccc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="来源主机名" min-width="130" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.machines && row.machines.length > 0">{{ row.machines[0].hostname || '-' }}</span>
            <span v-else style="color: #ccc">-</span>
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

      <div class="pagination-wrapper">
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

    <!-- 技能详情对话框 -->
    <el-dialog v-model="detailVisible" title="技能详情" width="960px" destroy-on-close>
      <div v-loading="detailLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="技能ID">{{ detailSkill.id }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{ detailSkill.name }}</el-descriptions-item>
          <el-descriptions-item label="编码">{{ detailSkill.code }}</el-descriptions-item>
          <el-descriptions-item label="版本">{{ detailSkill.version || '-' }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ detailSkill.description || '-' }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin: 20px 0 10px">已安装机器</h4>
        <el-table :data="detailMachines" border stripe style="width: 100%">
          <el-table-column prop="machine_code" label="机器码" min-width="140" />
          <el-table-column prop="ip" label="IP" min-width="130" />
          <el-table-column prop="hostname" label="主机名" min-width="120" />
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'installed' ? 'success' : 'info'" size="small">
                {{ row.status === 'installed' ? '已安装' : row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-button link type="danger" size="small" @click="removeFromMachine(row)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="detailMachines.length === 0" description="暂无机器安装此技能" />

        <h4 style="margin: 20px 0 10px">文件浏览</h4>
        <div class="file-browser">
          <div class="file-tree-panel">
            <el-tree
              v-if="skillFiles.length > 0"
              :data="skillFiles"
              :props="{ label: 'path', children: 'children' }"
              node-key="path"
              highlight-current
              default-expand-all
              @node-click="onFileNodeClick"
            >
              <template #default="{ node, data }">
                <span class="file-tree-node">
                  <span>{{ data.type === 'dir' ? '📁' : '📄' }} {{ node.label.split('/').pop() }}</span>
                  <span v-if="data.type === 'file'" class="file-size">{{ formatSize(data.size) }}</span>
                </span>
              </template>
            </el-tree>
            <el-empty v-else description="暂无文件" :image-size="60" />
          </div>
          <div class="file-content-panel">
            <div v-if="selectedFilePath" class="file-content-header">
              <span>{{ selectedFilePath }}</span>
            </div>
            <el-input
              v-if="fileContent !== null"
              v-model="fileContent"
              type="textarea"
              :rows="20"
              readonly
              style="font-family: monospace; font-size: 13px"
            />
            <div v-else-if="selectedFilePath" class="file-content-placeholder">
              点击左侧文件查看内容
            </div>
            <div v-else class="file-content-placeholder">
              选择文件以查看内容
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 分发技能对话框 -->
    <el-dialog v-model="distributeVisible" title="分发技能" width="720px" destroy-on-close @closed="resetDistribute">
      <div style="margin-bottom: 16px">
        <span>技能：<strong>{{ distributeSkill?.name }}</strong>（{{ distributeSkill?.code }}）</span>
      </div>
      <el-form label-width="90px" style="margin-bottom: 12px">
        <el-form-item label="安装路径">
          <el-input v-model="installPath" placeholder="目标机器上的技能安装路径" />
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
      <div style="margin-top: 8px; color: #909399; font-size: 12px">
        已选择 {{ selectedMachines.length }} 台机器
      </div>
      <template #footer>
        <el-button @click="distributeVisible = false">取消</el-button>
        <el-button type="primary" :loading="distributing" @click="handleDistribute">确认分发</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getSkills, createSkill, getSkillDetail, deleteSkill, removeSkillFromMachine, getSkillFiles, getSkillFileContent } from '../../api/skill'
import { getMachines, getMachineIps } from '../../api/machine'
import { distributeSkill as distributeSkillApi } from '../../api/deploy'

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
    tableData.value = Array.isArray(res) ? res : (res.items || res.data || [])
    pagination.total = res.total || tableData.value.length
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

function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
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

// ---------- 技能详情 ----------
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailSkill = ref({})
const detailMachines = ref([])

// File browsing state
const skillFiles = ref([])
const selectedFilePath = ref('')
const fileContent = ref(null)
const fileContentLoading = ref(false)

async function showDetail(id) {
  detailVisible.value = true
  detailLoading.value = true
  detailSkill.value = {}
  detailMachines.value = []
  skillFiles.value = []
  selectedFilePath.value = ''
  fileContent.value = null
  try {
    const [res, filesRes] = await Promise.all([
      getSkillDetail(id),
      getSkillFiles(id),
    ])
    detailSkill.value = res.skill || {}
    detailMachines.value = res.machines || []
    skillFiles.value = filesRes.files || []
  } catch {
    // handled by interceptor
  } finally {
    detailLoading.value = false
  }
}

async function onFileNodeClick(data) {
  if (data.type === 'dir') return
  selectedFilePath.value = data.path
  fileContent.value = null
  fileContentLoading.value = true
  try {
    const res = await getSkillFileContent(detailSkill.value.id, data.path)
    fileContent.value = res.content || ''
  } catch {
    fileContent.value = '（读取文件内容失败）'
  } finally {
    fileContentLoading.value = false
  }
}

async function removeFromMachine(row) {
  try {
    await ElMessageBox.confirm(`确定从机器「${row.hostname || row.machine_code}」移除技能「${detailSkill.value.name}」吗？`, '确认移除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await removeSkillFromMachine(detailSkill.value.id, row.machine_id)
    ElMessage.success('技能已移除')
    showDetail(detailSkill.value.id)
    delete skillMachinesMap[detailSkill.value.id]
    fetchData()
  } catch {
    // cancelled
  }
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
const installPath = ref('C:\\OpenClaw\\skills')
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

// ---------- 初始化 ----------
onMounted(() => {
  fetchData()
  loadMachines()
  loadMachineIps()
})
</script>

<style scoped>
.skill-list {
  padding: 16px;
}
.filter-card {
  margin-bottom: 16px;
}
.filter-card :deep(.el-form-item) {
  margin-bottom: 12px;
}
.table-card {
  margin-bottom: 16px;
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.file-browser {
  display: flex;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  min-height: 400px;
}
.file-tree-panel {
  width: 260px;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
  padding: 8px;
}
.file-content-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.file-content-header {
  padding: 8px 12px;
  border-bottom: 1px solid #e4e7ed;
  font-size: 13px;
  color: #606266;
  font-family: monospace;
}
.file-content-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: #c0c4cc;
  font-size: 14px;
}
.file-tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  font-size: 13px;
}
.file-size {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
}
</style>
