<template>
  <div class="skill-list">
    <!-- 搜索筛选区 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="filters" inline>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="名称/编码" clearable style="width: 180px" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="审核状态">
          <el-select v-model="filters.audit_status" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="a in auditStatusOptions" :key="a.value" :label="a.label" :value="a.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="发布状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="s in publishStatusOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
      <el-button type="success" :icon="Plus" @click="openDialog">新增技能</el-button>
    </el-card>

    <!-- 数据表格 -->
    <el-card shadow="never" class="table-card">
      <el-table v-loading="loading" :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="code" label="编码" min-width="140" show-overflow-tooltip />
        <el-table-column prop="version" label="版本" width="90" align="center" />
        <el-table-column prop="applicable_positions" label="适用岗位" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            {{ formatPositions(row.applicable_positions) }}
          </template>
        </el-table-column>
        <el-table-column prop="audit_status" label="审核状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="auditTagType(row.audit_status)">{{ auditLabel(row.audit_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="发布状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="publishTagType(row.status)">{{ publishLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.audit_status === 'pending'" link type="success" size="small" @click="handleAudit(row.id, 'approved')">通过</el-button>
            <el-button v-if="row.audit_status === 'pending'" link type="danger" size="small" @click="handleAudit(row.id, 'rejected')">拒绝</el-button>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { getSkills, createSkill, auditSkill } from '../../api/skill'

// ---------- 状态映射 ----------
const auditStatusOptions = [
  { value: 'pending', label: '待审核' },
  { value: 'approved', label: '已通过' },
  { value: 'rejected', label: '已拒绝' },
]

const publishStatusOptions = [
  { value: 'draft', label: '草稿' },
  { value: 'published', label: '已发布' },
  { value: 'deprecated', label: '已下架' },
]

const auditTagType = (status) => {
  const map = { pending: 'warning', approved: 'success', rejected: 'danger' }
  return map[status] || ''
}
const auditLabel = (status) => {
  const map = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
  return map[status] || status
}

const publishTagType = (status) => {
  const map = { draft: 'info', published: 'success', deprecated: 'danger' }
  return map[status] || ''
}
const publishLabel = (status) => {
  const map = { draft: '草稿', published: '已发布', deprecated: '已下架' }
  return map[status] || status
}

const positionOptions = ['工程师', '产品经理', '设计师', '运营', '主管', '经理', '数据分析师']

function formatPositions(val) {
  if (Array.isArray(val)) return val.join('、')
  return val || '-'
}

// ---------- 筛选 ----------
const filters = reactive({
  keyword: '',
  audit_status: '',
  status: '',
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
  Object.assign(filters, { keyword: '', audit_status: '', status: '' })
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

// ---------- 审核 ----------
async function handleAudit(id, auditStatus) {
  const actionLabel = auditStatus === 'approved' ? '通过' : '拒绝'
  try {
    await ElMessageBox.confirm(`确定将此技能审核状态设为「${actionLabel}」吗？`, '审核确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await auditSkill(id, auditStatus)
    ElMessage.success(`审核操作成功：${actionLabel}`)
    fetchData()
  } catch {
    // 用户取消或请求失败
  }
}

// ---------- 跳转详情 ----------
function goDetail(id) {
  // 预留详情页路由，后续可实现
  console.log('navigate to skill detail', id)
}

// ---------- 初始化 ----------
onMounted(() => {
  fetchData()
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
</style>
