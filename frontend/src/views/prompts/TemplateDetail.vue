<template>
  <div class="oc-page">
    <div class="oc-page-header">
      <h1 class="oc-page-header__title">模板详情</h1>
      <el-button @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回列表
      </el-button>
    </div>

    <div v-loading="loading">
      <!-- Basic Info -->
      <el-card shadow="never" class="oc-table-card">
        <template #header>
          <span>基本信息</span>
        </template>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="模板名称">{{ template.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="typeTagMap[template.type]?.type" size="small">
              {{ typeTagMap[template.type]?.label || template.type || '-' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="适用岗位">{{ template.position_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="适用场景">{{ template.scenario_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="版本">{{ template.version ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagMap[template.status]?.type" size="small">
              {{ statusTagMap[template.status]?.label || template.status || '-' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建者">{{ template.created_by || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(template.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatTime(template.updated_at) }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- Prompt Content -->
      <el-card shadow="never" class="oc-table-card">
        <template #header>
          <div class="card-header-row">
            <span>Prompt内容</span>
            <el-button
              v-if="!editing"
              type="primary"
              link
              size="small"
              @click="startEdit"
            >
              编辑
            </el-button>
            <div v-else>
              <el-button type="success" link size="small" @click="saveContent">保存</el-button>
              <el-button link size="small" @click="cancelEdit">取消</el-button>
            </div>
          </div>
        </template>
        <div v-if="!editing">
          <pre class="prompt-content">{{ template.content || '-' }}</pre>
        </div>
        <div v-else>
          <el-input
            v-model="editContent"
            type="textarea"
            :rows="16"
            placeholder="请输入Prompt内容"
          />
        </div>
      </el-card>

      <!-- Variables -->
      <el-card shadow="never" class="oc-table-card">
        <template #header>
          <span>变量定义</span>
        </template>
        <div v-if="parsedVariables.length > 0">
          <el-table :data="parsedVariables" stripe border size="small">
            <el-table-column prop="name" label="变量名" min-width="140" />
            <el-table-column prop="type" label="类型" width="120" />
            <el-table-column prop="description" label="描述" min-width="200" />
            <el-table-column prop="default" label="默认值" min-width="140" />
          </el-table>
        </div>
        <el-empty v-else description="暂无变量定义" :image-size="60" />
      </el-card>

      <!-- Version Info -->
      <el-card shadow="never" class="oc-table-card">
        <template #header>
          <span>版本信息</span>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="当前版本">{{ template.version ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagMap[template.status]?.type" size="small">
              {{ statusTagMap[template.status]?.label || template.status || '-' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- Action Buttons -->
      <el-card shadow="never" class="oc-table-card">
        <template #header>
          <span>操作</span>
        </template>
        <div class="action-buttons">
          <el-button
            type="primary"
            :disabled="editing || template.status === 'published'"
            @click="handlePublish"
          >
            发布
          </el-button>
          <el-button type="warning" @click="showRollbackDialog">回滚</el-button>
          <el-button @click="goBack">返回列表</el-button>
        </div>
      </el-card>
    </div>

    <!-- Rollback Dialog -->
    <el-dialog
      v-model="rollbackDialogVisible"
      title="回滚版本"
      width="400px"
      destroy-on-close
    >
      <el-form label-width="80px">
        <el-form-item label="目标版本">
          <el-input-number
            v-model="rollbackVersion"
            :min="1"
            :max="template.version || 1"
            controls-position="right"
            placeholder="请输入目标版本号"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rollbackDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="rollbackLoading" @click="handleRollback">
          确定回滚
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import {
  getTemplate,
  updateTemplate,
  publishTemplate,
  rollbackTemplate,
} from '../../api/prompt'

const route = useRoute()
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
const template = ref({})
const editing = ref(false)
const editContent = ref('')

const rollbackDialogVisible = ref(false)
const rollbackVersion = ref(1)
const rollbackLoading = ref(false)

const parsedVariables = computed(() => {
  const vars = template.value.variables
  if (!vars) return []
  if (Array.isArray(vars)) return vars
  if (typeof vars === 'object') {
    return Object.entries(vars).map(([name, val]) => {
      if (typeof val === 'object' && val !== null) {
        return { name, ...val }
      }
      return { name, type: typeof val, default: val }
    })
  }
  try {
    const parsed = JSON.parse(vars)
    if (Array.isArray(parsed)) return parsed
    return Object.entries(parsed).map(([name, val]) => {
      if (typeof val === 'object' && val !== null) {
        return { name, ...val }
      }
      return { name, type: typeof val, default: val }
    })
  } catch {
    return []
  }
})

function formatTime(val) {
  if (!val) return '-'
  return new Date(val).toLocaleString('zh-CN')
}

async function loadDetail() {
  const id = route.params.id
  if (!id) return
  loading.value = true
  try {
    const res = await getTemplate(id)
    template.value = res
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push({ name: 'Prompts' })
}

function startEdit() {
  editContent.value = template.value.content || ''
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  editContent.value = ''
}

async function saveContent() {
  const id = route.params.id
  try {
    await updateTemplate(id, { content: editContent.value })
    ElMessage.success('保存成功')
    template.value.content = editContent.value
    editing.value = false
  } catch {
    // error handled by interceptor
  }
}

async function handlePublish() {
  try {
    await ElMessageBox.confirm(
      `确定要发布模板「${template.value.name}」吗？`,
      '发布确认',
      { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
    )
    await publishTemplate(route.params.id)
    ElMessage.success('发布成功')
    loadDetail()
  } catch {
    // cancelled or error
  }
}

function showRollbackDialog() {
  rollbackVersion.value = 1
  rollbackDialogVisible.value = true
}

async function handleRollback() {
  if (!rollbackVersion.value) {
    ElMessage.warning('请输入目标版本号')
    return
  }
  rollbackLoading.value = true
  try {
    await rollbackTemplate(route.params.id, rollbackVersion.value)
    ElMessage.success('回滚成功')
    rollbackDialogVisible.value = false
    loadDetail()
  } catch {
    // error handled by interceptor
  } finally {
    rollbackLoading.value = false
  }
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.prompt-content {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: Consolas, Monaco, 'Courier New', monospace;
  font-size: var(--oc-font-base);
  line-height: 1.6;
  margin: 0;
  padding: var(--oc-space-3);
  background-color: var(--oc-bg-input);
  border-radius: var(--oc-radius-base);
  max-height: 500px;
  overflow-y: auto;
}

.action-buttons {
  display: flex;
  gap: 12px;
}
</style>
