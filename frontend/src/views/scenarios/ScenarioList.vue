<template>
  <div class="scenario-list">
    <!-- 搜索筛选区 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="filters" inline>
        <el-form-item label="用户ID">
          <el-input v-model="filters.user_id" placeholder="用户ID" clearable style="width: 120px" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="场景类型">
          <el-select v-model="filters.scenario_type" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="t in typeOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
      <el-button type="success" :icon="Plus" @click="openDialog('create')">新增场景</el-button>
    </el-card>

    <!-- 数据表格 -->
    <el-card shadow="never" class="table-card">
      <el-table v-loading="loading" :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="name" label="场景名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="user_id" label="用户ID" width="80" align="center" />
        <el-table-column prop="scenario_type" label="类型" width="120" align="center">
          <template #default="{ row }">
            {{ typeLabel(row.scenario_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="input_description" label="输入描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDialog('edit', row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
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

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新增场景' : '编辑场景'"
      width="600px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="场景名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入场景名称" />
        </el-form-item>
        <el-form-item label="用户ID" prop="user_id">
          <el-input v-model="formData.user_id" placeholder="请输入用户ID" :disabled="dialogMode === 'edit'" />
        </el-form-item>
        <el-form-item label="场景类型" prop="scenario_type">
          <el-select v-model="formData.scenario_type" placeholder="请选择类型" style="width: 100%">
            <el-option v-for="t in typeOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="输入描述" prop="input_description">
          <el-input v-model="formData.input_description" type="textarea" :rows="3" placeholder="请描述业务场景输入" />
        </el-form-item>
        <el-form-item label="输出描述">
          <el-input v-model="formData.output_description" type="textarea" :rows="3" placeholder="请描述期望输出" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="formData.status" placeholder="请选择状态" style="width: 100%">
            <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { getScenarios, createScenario, updateScenario, deleteScenario } from '../../api/scenario'

// ---------- 状态映射 ----------
const statusOptions = [
  { value: 'pending', label: '待处理' },
  { value: 'organized', label: '已整理' },
  { value: 'prompt_generated', label: '已生成提示词' },
  { value: 'skill_configured', label: '已配置技能' },
  { value: 'testing', label: '测试中' },
  { value: 'online', label: '已上线' },
  { value: 'needs_optimization', label: '需优化' },
  { value: 'paused', label: '已暂停' },
]

const statusTagType = (status) => {
  const map = {
    pending: 'info', organized: '', prompt_generated: 'warning', skill_configured: 'primary',
    testing: 'warning', online: 'success', needs_optimization: 'danger', paused: 'info',
  }
  return map[status] || ''
}
const statusLabel = (status) => {
  const map = {
    pending: '待处理', organized: '已整理', prompt_generated: '已生成提示词',
    skill_configured: '已配置技能', testing: '测试中', online: '已上线',
    needs_optimization: '需优化', paused: '已暂停',
  }
  return map[status] || status
}

const typeOptions = [
  { value: 'data_query', label: '数据查询' },
  { value: 'report_generation', label: '报表生成' },
  { value: 'workflow', label: '工作流' },
  { value: 'automation', label: '自动化' },
]
const typeLabel = (type) => {
  const map = { data_query: '数据查询', report_generation: '报表生成', workflow: '工作流', automation: '自动化' }
  return map[type] || type
}

// ---------- 筛选 ----------
const filters = reactive({
  user_id: '',
  status: '',
  scenario_type: '',
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
    const res = await getScenarios(params)
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
  Object.assign(filters, { user_id: '', status: '', scenario_type: '' })
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

// ---------- 对话框 ----------
const dialogVisible = ref(false)
const dialogMode = ref('create')
const submitting = ref(false)
const formRef = ref(null)
const editingId = ref(null)

const defaultForm = () => ({
  name: '',
  user_id: '',
  scenario_type: '',
  input_description: '',
  output_description: '',
  status: 'pending',
})

const formData = reactive(defaultForm())

const formRules = reactive({
  name: [{ required: true, message: '请输入场景名称', trigger: 'blur' }],
  user_id: [{ required: true, message: '请输入用户ID', trigger: 'blur' }],
  scenario_type: [{ required: true, message: '请选择场景类型', trigger: 'change' }],
  input_description: [{ required: true, message: '请输入输入描述', trigger: 'blur' }],
})

function openDialog(mode, row = null) {
  dialogMode.value = mode
  if (mode === 'edit' && row) {
    editingId.value = row.id
    Object.keys(defaultForm()).forEach((k) => {
      formData[k] = row[k] ?? defaultForm()[k]
    })
  } else {
    editingId.value = null
    Object.assign(formData, defaultForm())
  }
  dialogVisible.value = true
}

function resetForm() {
  Object.assign(formData, defaultForm())
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
    if (dialogMode.value === 'create') {
      await createScenario(payload)
      ElMessage.success('场景创建成功')
    } else {
      await updateScenario(editingId.value, payload)
      ElMessage.success('场景更新成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch {
    // 已由拦截器处理
  } finally {
    submitting.value = false
  }
}

// ---------- 删除 ----------
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除场景「${row.name}」吗？此操作不可恢复。`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteScenario(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {
    // 用户取消或请求失败
  }
}

// ---------- 初始化 ----------
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.scenario-list {
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
</style>
