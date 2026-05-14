<template>
  <div class="oc-page oc-page--scrollable">
    <div class="oc-page-header">
      <h1 class="oc-page-header__title">提示词模板</h1>
    </div>

    <!-- AI Generation Section -->
    <el-card shadow="never" class="ai-generate-card">
      <template #header>
        <div class="ai-generate-card__header">
          <span>AI 生成提示词</span>
          <el-tag v-if="!hasActiveAI" type="danger" size="small">未配置AI，请先到AI配置页面添加</el-tag>
        </div>
      </template>

      <div class="ai-generate-form">
        <el-input
          v-model="generateForm.description"
          type="textarea"
          :rows="4"
          placeholder="描述你需要的提示词模板，如：生成一个用于代码审查的提示词模板，要求能检测常见的安全漏洞和代码规范问题"
          :disabled="generating"
        />
        <div class="ai-generate-options">
          <el-select v-model="generateForm.type" placeholder="模板类型" clearable style="width: 140px">
            <el-option label="通用" value="general" />
            <el-option label="岗位" value="position" />
            <el-option label="用户专属" value="user_specific" />
          </el-select>
          <el-input v-model="generateForm.position_type" placeholder="适用岗位（可选）" style="width: 180px" />
          <el-input v-model="generateForm.scenario_type" placeholder="适用场景（可选）" style="width: 180px" />
          <el-button
            type="primary"
            :loading="generating"
            :disabled="!hasActiveAI || !generateForm.description.trim()"
            @click="handleGenerate"
          >
            {{ generating ? '生成中...' : '生成提示词' }}
          </el-button>
          <el-button v-if="generatedContent" @click="handleDiscard">丢弃</el-button>
        </div>
      </div>

      <!-- Generated Result -->
      <div v-if="generatedContent || generating" class="ai-generate-result">
        <div class="ai-generate-result__label">
          {{ generating ? '正在生成...' : '生成结果（可编辑）' }}
        </div>
        <el-input
          v-model="generatedContent"
          type="textarea"
          :rows="12"
          :placeholder="generating ? '等待AI响应...' : ''"
          :readonly="generating"
          class="ai-generate-result__textarea"
        />
        <div v-if="!generating && generatedContent" class="ai-generate-result__actions">
          <el-button type="primary" @click="showSaveDialog">保存为模板</el-button>
          <el-button @click="handleDiscard">丢弃</el-button>
        </div>
      </div>
    </el-card>

    <!-- Template List Section -->
    <el-card shadow="never">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>已有模板</span>
          <el-button type="primary" size="small" @click="showAddDialog">手动新增</el-button>
        </div>
      </template>

      <!-- Filters -->
      <el-form :inline="true" :model="filters" @submit.prevent="loadTemplates" style="margin-bottom: 12px;">
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="搜索" clearable @clear="loadTemplates" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable @change="loadTemplates">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTemplates">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="templates" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column prop="name" label="模板名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="typeTagMap[row.type]?.type" size="small">
              {{ typeTagMap[row.type]?.label || row.type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="70" align="center" />
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagMap[row.status]?.type" size="small">
              {{ statusTagMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" align="center">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)">查看</el-button>
            <el-button
              type="success" link size="small"
              :disabled="row.status === 'published'"
              @click="handlePublish(row)"
            >发布</el-button>
            <el-button type="warning" link size="small" @click="handleCopy(row)">复制</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="oc-pagination">
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

    <!-- Save Generated as Template Dialog -->
    <el-dialog v-model="saveDialogVisible" title="保存为提示词模板" width="560px" destroy-on-close>
      <el-form ref="saveFormRef" :model="saveForm" :rules="saveFormRules" label-width="100px">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="saveForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="saveForm.type" style="width: 100%">
            <el-option label="通用" value="general" />
            <el-option label="岗位" value="position" />
            <el-option label="用户专属" value="user_specific" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用岗位">
          <el-input v-model="saveForm.position_type" placeholder="可选" />
        </el-form-item>
        <el-form-item label="适用场景">
          <el-input v-model="saveForm.scenario_type" placeholder="可选" />
        </el-form-item>
        <el-form-item label="模板内容">
          <el-input v-model="saveForm.content" type="textarea" :rows="6" readonly />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saveSubmitting" @click="handleSaveTemplate">保存</el-button>
      </template>
    </el-dialog>

    <!-- Manual Add Template Dialog -->
    <el-dialog v-model="addDialogVisible" title="新增模板" width="640px" destroy-on-close>
      <el-form ref="addFormRef" :model="addForm" :rules="addFormRules" label-width="100px">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="addForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="addForm.type" style="width: 100%">
            <el-option label="通用" value="general" />
            <el-option label="岗位" value="position" />
            <el-option label="用户专属" value="user_specific" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板内容" prop="content">
          <el-input v-model="addForm.content" type="textarea" :rows="10" placeholder="请输入Prompt模板内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addSubmitting" @click="handleAdd">确定</el-button>
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
  deleteTemplate,
  aiGeneratePrompt,
} from '../../api/prompt'
import { getActiveConfig } from '../../api/aiConfig'

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

// --- AI Generation ---
const hasActiveAI = ref(false)
const generating = ref(false)
const generatedContent = ref('')

const generateForm = reactive({
  description: '',
  type: '',
  position_type: '',
  scenario_type: '',
})

async function checkActiveAI() {
  try {
    const res = await getActiveConfig()
    hasActiveAI.value = !!res.item
  } catch {
    hasActiveAI.value = false
  }
}

function handleGenerate() {
  if (!generateForm.description.trim()) return
  generating.value = true
  generatedContent.value = ''

  const data = {
    description: generateForm.description,
    type: generateForm.type || 'general',
    position_type: generateForm.position_type || undefined,
    scenario_type: generateForm.scenario_type || undefined,
  }

  aiGeneratePrompt(
    data,
    (chunk) => {
      generatedContent.value += chunk
    },
    () => {
      generating.value = false
    },
    (error) => {
      generating.value = false
      ElMessage.error(error || '生成失败')
    }
  )
}

function handleDiscard() {
  generatedContent.value = ''
}

// --- Save Generated ---
const saveDialogVisible = ref(false)
const saveSubmitting = ref(false)
const saveFormRef = ref(null)

const saveForm = reactive({
  name: '',
  type: 'general',
  position_type: '',
  scenario_type: '',
  content: '',
})

const saveFormRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
}

function showSaveDialog() {
  saveForm.name = ''
  saveForm.type = generateForm.type || 'general'
  saveForm.position_type = generateForm.position_type || ''
  saveForm.scenario_type = generateForm.scenario_type || ''
  saveForm.content = generatedContent.value
  saveDialogVisible.value = true
}

async function handleSaveTemplate() {
  const formEl = saveFormRef.value
  if (!formEl) return
  try { await formEl.validate() } catch { return }

  saveSubmitting.value = true
  try {
    await createTemplate({
      name: saveForm.name,
      type: saveForm.type,
      position_type: saveForm.position_type || null,
      scenario_type: saveForm.scenario_type || null,
      content: saveForm.content,
    })
    ElMessage.success('模板已保存')
    saveDialogVisible.value = false
    generatedContent.value = ''
    loadTemplates()
  } catch {} finally {
    saveSubmitting.value = false
  }
}

// --- Template List ---
const loading = ref(false)
const templates = ref([])
const filters = reactive({ keyword: '', status: '' })
const pagination = reactive({ page: 1, size: 10, total: 0 })

function formatTime(val) {
  if (!val) return '-'
  return new Date(val).toLocaleString('zh-CN')
}

async function loadTemplates() {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.size,
      limit: pagination.size,
      ...filters,
    }
    Object.keys(params).forEach((key) => {
      if (params[key] === '' || params[key] == null) delete params[key]
    })
    const res = await getTemplates(params)
    templates.value = Array.isArray(res) ? res : (res.items || res.data || [])
    pagination.total = res.total || templates.value.length
  } catch {} finally {
    loading.value = false
  }
}

function viewDetail(row) {
  router.push({ name: 'TemplateDetail', params: { id: row.id } })
}

async function handlePublish(row) {
  try {
    await ElMessageBox.confirm(`确定要发布模板「${row.name}」吗？`, '发布确认', { type: 'warning' })
    await publishTemplate(row.id)
    ElMessage.success('发布成功')
    loadTemplates()
  } catch {}
}

async function handleCopy(row) {
  try {
    await ElMessageBox.confirm(`确定要复制模板「${row.name}」吗？`, '复制确认', { type: 'info' })
    await copyTemplate(row.id)
    ElMessage.success('复制成功')
    loadTemplates()
  } catch {}
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除模板「${row.name}」吗？`, '删除确认', { type: 'warning' })
    await deleteTemplate(row.id)
    ElMessage.success('模板已删除')
    loadTemplates()
  } catch {}
}

// --- Manual Add ---
const addDialogVisible = ref(false)
const addSubmitting = ref(false)
const addFormRef = ref(null)

const addForm = reactive({
  name: '',
  type: '',
  content: '',
})

const addFormRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  content: [{ required: true, message: '请输入模板内容', trigger: 'blur' }],
}

function showAddDialog() {
  addForm.name = ''
  addForm.type = ''
  addForm.content = ''
  addDialogVisible.value = true
}

async function handleAdd() {
  const formEl = addFormRef.value
  if (!formEl) return
  try { await formEl.validate() } catch { return }

  addSubmitting.value = true
  try {
    await createTemplate({
      name: addForm.name,
      type: addForm.type,
      content: addForm.content,
    })
    ElMessage.success('创建成功')
    addDialogVisible.value = false
    loadTemplates()
  } catch {} finally {
    addSubmitting.value = false
  }
}

onMounted(() => {
  checkActiveAI()
  loadTemplates()
})
</script>

<style scoped>
.ai-generate-card {
  margin-bottom: 16px;
}

.ai-generate-card__header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-generate-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ai-generate-options {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.ai-generate-result {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--oc-border-color-light);
}

.ai-generate-result__label {
  font-size: 13px;
  color: var(--oc-text-secondary);
  margin-bottom: 8px;
}

.ai-generate-result__textarea :deep(.el-textarea__inner) {
  font-family: Consolas, Monaco, 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.ai-generate-result__actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
</style>
