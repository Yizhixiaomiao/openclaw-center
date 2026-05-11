<template>
  <div class="machine-list">
    <!-- Agent 下载提示 -->
    <el-alert type="info" :closable="false" class="agent-download-alert">
      <template #title>
        <span>Agent 安装：以管理员身份在目标机器上执行以下 PowerShell 命令即可下载并运行 Agent（将自动注册为计划任务，开机自启）</span>
      </template>
      <div class="agent-download-info">
        <div class="agent-download-cmd">
          <code>Invoke-WebRequest -Uri "http://{{ centerHost }}:8000/api/agent/download" -OutFile "OpenClawCenterAgent.exe"; .\OpenClawCenterAgent.exe</code>
          <el-button type="primary" link size="small" @click="copyAgentCmd">复制</el-button>
        </div>
        <div class="agent-version-row">
          <span>当前版本：<el-tag v-if="agentVersionInfo.version && agentVersionInfo.version !== '0.0.0'" size="small">{{ agentVersionInfo.version }}</el-tag><el-tag v-else type="info" size="small">未上传</el-tag></span>
          <el-button type="warning" size="small" @click="openUploadDialog">上传新版本</el-button>
        </div>
      </div>
    </el-alert>

    <!-- 搜索筛选区 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="filters" inline>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="机器码/主机名/IP" clearable style="width: 200px" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="filters.department" placeholder="部门" clearable style="width: 140px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
      <el-button type="success" :icon="Plus" @click="openDialog">新增机器</el-button>
    </el-card>

    <!-- 数据表格 -->
    <el-card shadow="never" class="table-card">
      <el-table v-loading="loading" :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="id" label="编号" width="70" align="center" />
        <el-table-column prop="code" label="机器码" min-width="180" show-overflow-tooltip />
        <el-table-column prop="hostname" label="主机名" min-width="130" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" width="140" />
        <el-table-column prop="os" label="系统" width="100" align="center" />
        <el-table-column prop="cpu" label="CPU" width="80" align="center" />
        <el-table-column prop="memory" label="内存" width="80" align="center" />
        <el-table-column label="CPU使用率" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.cpu_usage != null">{{ row.cpu_usage.toFixed(1) }}%</span>
            <span v-else style="color: #ccc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="内存使用率" width="110" align="center">
          <template #default="{ row }">
            <span v-if="row.memory_usage != null">{{ row.memory_usage.toFixed(1) }}%</span>
            <span v-else style="color: #ccc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="磁盘使用率" width="110" align="center">
          <template #default="{ row }">
            <span v-if="row.disk_usage != null">{{ row.disk_usage.toFixed(1) }}%</span>
            <span v-else style="color: #ccc">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="user_id" label="用户ID" width="80" align="center" />
        <el-table-column prop="skills_count" label="已安装技能" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.skills_count" type="primary" size="small">{{ row.skills_count }} 个</el-tag>
            <span v-else style="color: #ccc">0</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_heartbeat_at" label="最近心跳" width="180" align="center">
          <template #default="{ row }">
            {{ row.last_heartbeat_at ? formatDateTime(row.last_heartbeat_at) : '从未上线' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="goDetail(row.id)">查看</el-button>
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

    <!-- 新增机器对话框 -->
    <el-dialog v-model="dialogVisible" title="新增机器" width="520px" destroy-on-close @closed="resetForm">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="90px">
        <el-form-item label="机器码" prop="code">
          <el-input v-model="formData.code" placeholder="请输入机器码" />
        </el-form-item>
        <el-form-item label="主机名" prop="hostname">
          <el-input v-model="formData.hostname" placeholder="请输入主机名" />
        </el-form-item>
        <el-form-item label="IP" prop="ip">
          <el-input v-model="formData.ip" placeholder="请输入IP地址" />
        </el-form-item>
        <el-form-item label="系统">
          <el-input v-model="formData.os" placeholder="如 Windows 11" />
        </el-form-item>
        <el-form-item label="CPU">
          <el-input v-model="formData.cpu" placeholder="如 8核" />
        </el-form-item>
        <el-form-item label="内存">
          <el-input v-model="formData.memory" placeholder="如 16GB" />
        </el-form-item>
        <el-form-item label="用户ID">
          <el-input v-model="formData.user_id" placeholder="绑定用户ID" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 上传 Agent 新版本对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传 Agent 新版本" width="520px" destroy-on-close @closed="resetUploadForm">
      <el-form ref="uploadFormRef" :model="uploadForm" :rules="uploadFormRules" label-width="100px">
        <el-form-item label="版本号" prop="version">
          <el-input v-model="uploadForm.version" placeholder="如 1.1.0" />
        </el-form-item>
        <el-form-item label="Agent程序" prop="file">
          <el-upload
            ref="uploadFileRef"
            :auto-upload="false"
            :limit="1"
            accept=".exe"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
          >
            <el-button type="primary" size="small">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">请选择 OpenClawCenterAgent.exe 文件</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { getMachines, createMachine, uploadAgent, getAgentVersion } from '../../api/machine'

const router = useRouter()

// ---------- Agent 下载提示 ----------
const centerHost = computed(() => {
  const base = import.meta.env.VITE_API_URL || window.location.hostname
  return base.replace(/^https?:\/\//, '')
})

function copyAgentCmd() {
  const cmd = `Invoke-WebRequest -Uri "http://${centerHost.value}:8000/api/agent/download" -OutFile "OpenClawCenterAgent.exe"; .\\OpenClawCenterAgent.exe`
  navigator.clipboard.writeText(cmd).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.warning('复制失败，请手动复制')
  })
}

// ---------- 状态映射 ----------
const statusOptions = [
  { value: 'online', label: '在线' },
  { value: 'offline', label: '离线' },
  { value: 'error', label: '异常' },
  { value: 'pending_init', label: '待初始化' },
  { value: 'disabled', label: '已禁用' },
]

const statusTagType = (status) => {
  const map = { online: 'success', offline: 'info', error: 'danger', pending_init: 'warning', disabled: 'info' }
  return map[status] || ''
}
const statusLabel = (status) => {
  const map = { online: '在线', offline: '离线', error: '异常', pending_init: '待初始化', disabled: '已禁用' }
  return map[status] || status
}

// ---------- 筛选 ----------
const filters = reactive({
  keyword: '',
  status: '',
  department: '',
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
    const res = await getMachines(params)
    tableData.value = Array.isArray(res) ? res : (res.items || res.data || [])
    pagination.total = res.total || tableData.value.length
  } catch {
    // 已由拦截器处理
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchData()
}

function handleReset() {
  Object.assign(filters, { keyword: '', status: '', department: '' })
  pagination.page = 1
  fetchData()
}

// ---------- 时间格式化 ----------
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
  code: '',
  hostname: '',
  ip: '',
  os: '',
  cpu: '',
  memory: '',
  user_id: '',
})

const formRules = reactive({
  code: [{ required: true, message: '请输入机器码', trigger: 'blur' }],
  hostname: [{ required: true, message: '请输入主机名', trigger: 'blur' }],
})

function openDialog() {
  dialogVisible.value = true
}

function resetForm() {
  Object.assign(formData, { code: '', hostname: '', ip: '', os: '', cpu: '', memory: '', user_id: '' })
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
    const payload = { ...formData }
    if (payload.user_id) payload.user_id = Number(payload.user_id)
    else delete payload.user_id
    await createMachine(payload)
    ElMessage.success('机器创建成功')
    dialogVisible.value = false
    fetchData()
  } catch {
    // 已由拦截器处理
  } finally {
    submitting.value = false
  }
}

// ---------- Agent 版本信息 ----------
const agentVersionInfo = reactive({ version: '', available: false })

async function fetchAgentVersion() {
  try {
    const res = await getAgentVersion()
    agentVersionInfo.version = res.version || ''
    agentVersionInfo.available = res.available || false
  } catch { /* ignored */ }
}

// ---------- 上传 Agent 新版本 ----------
const uploadDialogVisible = ref(false)
const uploading = ref(false)
const uploadFormRef = ref(null)
const uploadFileRef = ref(null)
const uploadFile = ref(null)

const uploadForm = reactive({ version: '', file: null })
const uploadFormRules = {
  version: [{ required: true, message: '请输入版本号', trigger: 'blur' }],
}

function openUploadDialog() {
  uploadDialogVisible.value = true
}

function resetUploadForm() {
  uploadForm.version = ''
  uploadForm.file = null
  uploadFile.value = null
  uploadFormRef.value?.resetFields()
}

function handleFileChange(file) {
  uploadFile.value = file.raw
}

function handleFileRemove() {
  uploadFile.value = null
}

async function handleUpload() {
  try {
    await uploadFormRef.value.validate()
  } catch {
    return
  }
  if (!uploadFile.value) {
    ElMessage.warning('请选择 Agent 程序文件')
    return
  }
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('version', uploadForm.version)
    formData.append('file', uploadFile.value)
    await uploadAgent(formData)
    ElMessage.success('Agent 新版本上传成功')
    uploadDialogVisible.value = false
    fetchAgentVersion()
  } catch {
    // handled by interceptor
  } finally {
    uploading.value = false
  }
}

// ---------- 跳转详情 ----------
function goDetail(id) {
  router.push(`/machines/${id}`)
}

// ---------- 初始化 ----------
onMounted(() => {
  fetchData()
  fetchAgentVersion()
})
</script>

<style scoped>
.machine-list {
  padding: 16px;
}
.agent-download-alert {
  margin-bottom: 16px;
}
.agent-download-info {
  margin-top: 4px;
}
.agent-download-cmd {
  display: flex;
  align-items: center;
  gap: 8px;
}
.agent-version-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}
.agent-download-cmd code {
  background: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 13px;
  word-break: break-all;
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
</style>
