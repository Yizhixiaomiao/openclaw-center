<template>
  <div class="template-list">
    <div class="page-header">
      <h2>Prompt模板管理</h2>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        新增模板
      </el-button>
    </div>

    <!-- Filters -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters" @submit.prevent="loadTemplates">
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="模板名称搜索"
            clearable
            @clear="loadTemplates"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.type" placeholder="全部类型" clearable @change="loadTemplates">
            <el-option label="通用" value="general" />
            <el-option label="岗位" value="position" />
            <el-option label="用户专属" value="user_specific" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable @change="loadTemplates">
            <el-option label="草稿" value="draft" />
            <el-option label="审核中" value="under_review" />
            <el-option label="已发布" value="published" />
            <el-option label="已废弃" value="deprecated" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTemplates">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Table -->
    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="templates"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="name" label="模板名称" min-width="160" show-overflow-tooltip />
        <el-table-column label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="typeTagMap[row.type]?.type" size="small">
              {{ typeTagMap[row.type]?.label || row.type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="position_type" label="适用岗位" width="110" show-overflow-tooltip />
        <el-table-column prop="scenario_type" label="适用场景" width="110" show-overflow-tooltip />
        <el-table-column prop="version" label="版本" width="80" align="center" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagMap[row.status]?.type" size="small">
              {{ statusTagMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" align="center">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)">
              查看详情
            </el-button>
            <el-button
              type="success"
              link
              size="small"
              :disabled="row.status === 'published'"
              @click="handlePublish(row)"
            >
              发布
            </el-button>
            <el-button type="warning" link size="small" @click="handleCopy(row)">
              复制
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadTemplates"
          @current-change="loadTemplates"
        />
      </div>
    </el-card>

    <!-- Add Template Dialog -->
    <el-dialog
      v-model="addDialogVisible"
      title="新增模板"
      width="640px"
      destroy-on-close
    >
      <el-form
        ref="addFormRef"
        :model="addForm"
        :rules="addFormRules"
        label-width="100px"
      >
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="addForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="addForm.type" placeholder="请选择类型" style="width: 100%">
            <el-option label="通用" value="general" />
            <el-option label="岗位" value="position" />
            <el-option label="用户专属" value="user_specific" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用岗位" prop="position_type">
          <el-input v-model="addForm.position_type" placeholder="请输入适用岗位" />
        </el-form-item>
        <el-form-item label="适用场景" prop="scenario_type">
          <el-input v-model="addForm.scenario_type" placeholder="请输入适用场景" />
        </el-form-item>
        <el-form-item label="模板内容" prop="content">
          <el-input
            v-model="addForm.content"
            type="textarea"
            :rows="8"
            placeholder="请输入Prompt模板内容"
          />
        </el-form-item>
        <el-form-item label="变量定义" prop="variables_json">
          <el-input
            v-model="addForm.variables_json"
            type="textarea"
            :rows="4"
            placeholder="请输入JSON格式变量定义"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleAdd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getTemplates,
  createTemplate,
  publishTemplate,
  copyTemplate,
} from '../../api/prompt'

const router = useRouter()

const typeTagMap = {
  general: { label: '通用', type: '' },
  position: { label: '岗位', type: 'warning' },
  user_specific: { label: '用户专属', type: 'danger' },
}

const statusTagMap = {
  draft: { label: '草稿', type: 'info' },
  under_review: { label: '审核中', type: 'warning' },
  published: { label: '已发布', type: 'success' },
  deprecated: { label: '已废弃', type: 'danger' },
}

const loading = ref(false)
const templates = ref([])
const submitting = ref(false)

const filters = reactive({
  keyword: '',
  type: '',
  status: '',
})

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0,
})

const addDialogVisible = ref(false)
const addFormRef = ref(null)

const addForm = reactive({
  name: '',
  type: '',
  position_type: '',
  scenario_type: '',
  content: '',
  variables_json: '',
})

const addFormRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  content: [{ required: true, message: '请输入模板内容', trigger: 'blur' }],
}

function formatTime(val) {
  if (!val) return '-'
  return new Date(val).toLocaleString('zh-CN')
}

async function loadTemplates() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      ...filters,
    }
    // Remove empty filters
    Object.keys(params).forEach((key) => {
      if (params[key] === '' || params[key] == null) delete params[key]
    })
    const res = await getTemplates(params)
    templates.value = res.items || res.data || []
    pagination.total = res.total || templates.value.length
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.keyword = ''
  filters.type = ''
  filters.status = ''
  pagination.page = 1
  loadTemplates()
}

function viewDetail(row) {
  router.push({ name: 'TemplateDetail', params: { id: row.id } })
}

async function handlePublish(row) {
  try {
    await ElMessageBox.confirm(
      `确定要发布模板「${row.name}」吗？`,
      '发布确认',
      { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
    )
    await publishTemplate(row.id)
    ElMessage.success('发布成功')
    loadTemplates()
  } catch {
    // cancelled or error
  }
}

async function handleCopy(row) {
  try {
    await ElMessageBox.confirm(
      `确定要复制模板「${row.name}」吗？`,
      '复制确认',
      { type: 'info', confirmButtonText: '确定', cancelButtonText: '取消' }
    )
    await copyTemplate(row.id)
    ElMessage.success('复制成功')
    loadTemplates()
  } catch {
    // cancelled or error
  }
}

function showAddDialog() {
  addForm.name = ''
  addForm.type = ''
  addForm.position_type = ''
  addForm.scenario_type = ''
  addForm.content = ''
  addForm.variables_json = ''
  addDialogVisible.value = true
}

async function handleAdd() {
  const form = addFormRef.value
  if (!form) return
  try {
    await form.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const data = {
      name: addForm.name,
      type: addForm.type,
      position_type: addForm.position_type,
      scenario_type: addForm.scenario_type,
      content: addForm.content,
    }
    // Parse variables JSON if provided
    if (addForm.variables_json.trim()) {
      try {
        data.variables = JSON.parse(addForm.variables_json)
      } catch {
        ElMessage.error('变量定义JSON格式错误')
        return
      }
    }
    await createTemplate(data)
    ElMessage.success('创建成功')
    addDialogVisible.value = false
    loadTemplates()
  } catch {
    // error handled by interceptor
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.template-list {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.filter-card {
  margin-bottom: 16px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
