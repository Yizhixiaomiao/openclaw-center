<template>
  <div class="deploy-task-list">
    <div class="page-header">
      <h2>部署任务</h2>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- Tab 1: Task List -->
      <el-tab-pane label="任务列表" name="list">
        <!-- Filters -->
        <el-form :inline="true" :model="filters" class="filter-form" @submit.prevent="loadTasks">
          <el-form-item label="任务类型">
            <el-select v-model="filters.task_type" placeholder="全部类型" clearable @change="loadTasks">
              <el-option label="Prompt" value="prompt" />
              <el-option label="技能" value="skill" />
              <el-option label="配置" value="config" />
              <el-option label="模型配置" value="model_config" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="filters.status" placeholder="全部状态" clearable @change="loadTasks">
              <el-option label="待执行" value="pending" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已完成" value="completed" />
              <el-option label="失败" value="failed" />
              <el-option label="部分成功" value="partial" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadTasks">查询</el-button>
            <el-button @click="resetFilters">重置</el-button>
          </el-form-item>
        </el-form>

        <!-- Task Table -->
        <el-table v-loading="listLoading" :data="tasks" stripe border style="width: 100%">
          <el-table-column prop="id" label="ID" width="70" align="center" />
          <el-table-column label="任务类型" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="taskTypeTagMap[row.task_type]?.type" size="small">
                {{ taskTypeTagMap[row.task_type]?.label || row.task_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="target_type" label="目标类型" width="120" align="center" />
          <el-table-column label="目标机器" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              {{ resolveTargetInfo(row) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="taskStatusTagMap[row.status]?.type" size="small">
                {{ taskStatusTagMap[row.status]?.label || row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="170" align="center">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="showTaskDetail(row)">
                查看
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
            @size-change="loadTasks"
            @current-change="loadTasks"
          />
        </div>
      </el-tab-pane>

      <!-- Tab 2: Create Task -->
      <el-tab-pane label="创建任务" name="create">
        <el-card shadow="never" style="max-width: 640px">
          <el-form
            ref="createFormRef"
            :model="createForm"
            :rules="createFormRules"
            label-width="100px"
          >
            <el-form-item label="任务类型" prop="task_type">
              <el-select v-model="createForm.task_type" placeholder="请选择任务类型" style="width: 100%">
                <el-option label="Prompt" value="prompt" />
                <el-option label="技能" value="skill" />
                <el-option label="配置" value="config" />
                <el-option label="模型配置" value="model_config" />
              </el-select>
            </el-form-item>
            <el-form-item label="目标类型" prop="target_type">
              <el-select v-model="createForm.target_type" placeholder="请选择目标类型" style="width: 100%">
                <el-option label="Prompt模板" value="prompt_template" />
                <el-option label="技能" value="skill" />
                <el-option label="配置" value="config" />
                <el-option label="模型配置" value="model_config" />
              </el-select>
            </el-form-item>
            <el-form-item label="目标ID" prop="target_id">
              <el-input v-model="createForm.target_id" placeholder="请输入目标ID" />
            </el-form-item>
            <el-form-item label="任务数据" prop="payload_json">
              <el-input
                v-model="createForm.payload_json"
                type="textarea"
                :rows="8"
                placeholder="请输入JSON格式任务数据（可选）"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="creating" @click="handleCreate">
                创建任务
              </el-button>
              <el-button @click="resetCreateForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- Task Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      title="任务详情"
      width="960px"
      destroy-on-close
    >
      <div v-loading="detailLoading">
        <el-descriptions :column="2" border class="detail-descriptions">
          <el-descriptions-item label="任务ID">{{ currentTask.id }}</el-descriptions-item>
          <el-descriptions-item label="任务类型">
            <el-tag :type="taskTypeTagMap[currentTask.task_type]?.type" size="small">
              {{ taskTypeTagMap[currentTask.task_type]?.label || currentTask.task_type }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="目标类型">{{ currentTask.target_type }}</el-descriptions-item>
          <el-descriptions-item label="目标机器">{{ resolveTargetInfo(currentTask) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="taskStatusTagMap[currentTask.status]?.type" size="small">
              {{ taskStatusTagMap[currentTask.status]?.label || currentTask.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(currentTask.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin: 20px 0 10px">部署明细</h4>
        <el-table
          :data="currentTask.items || []"
          stripe
          border
          size="small"
          style="width: 100%"
        >
          <el-table-column label="机器" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              {{ resolveMachineInfo(row.machine_id) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="itemStatusTagMap[row.status]?.type" size="small">
                {{ itemStatusTagMap[row.status]?.label || row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="消息" min-width="180" show-overflow-tooltip />
          <el-table-column prop="started_at" label="开始时间" width="170" align="center">
            <template #default="{ row }">
              {{ formatTime(row.started_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="finished_at" label="完成时间" width="170" align="center">
            <template #default="{ row }">
              {{ formatTime(row.finished_at) }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getDeployTasks,
  createDeployTask,
  getDeployTask,
} from '../../api/deploy'
import { getMachines } from '../../api/machine'

const taskTypeTagMap = {
  prompt: { label: 'Prompt', type: '' },
  skill: { label: '技能', type: 'success' },
  config: { label: '配置', type: 'warning' },
  model_config: { label: '模型配置', type: 'danger' },
}

const taskStatusTagMap = {
  pending: { label: '待执行', type: 'info' },
  in_progress: { label: '进行中', type: 'warning' },
  completed: { label: '已完成', type: 'success' },
  failed: { label: '失败', type: 'danger' },
  partial: { label: '部分成功', type: 'warning' },
}

const itemStatusTagMap = {
  pending: { label: '待执行', type: 'info' },
  in_progress: { label: '进行中', type: 'warning' },
  completed: { label: '已完成', type: 'success' },
  failed: { label: '失败', type: 'danger' },
  skipped: { label: '跳过', type: 'info' },
}

const activeTab = ref('list')
const listLoading = ref(false)
const tasks = ref([])

const filters = reactive({
  task_type: '',
  status: '',
})

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0,
})

const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const currentTask = ref({})

const createFormRef = ref(null)
const creating = ref(false)

const createForm = reactive({
  task_type: '',
  target_type: '',
  target_id: '',
  payload_json: '',
})

const createFormRules = {
  task_type: [{ required: true, message: '请选择任务类型', trigger: 'change' }],
  target_type: [{ required: true, message: '请选择目标类型', trigger: 'change' }],
  target_id: [{ required: true, message: '请输入目标ID', trigger: 'blur' }],
}

// ---------- 机器名解析 ----------
const machineMap = ref({})

async function loadMachineMap() {
  try {
    const res = await getMachines({ skip: 0, limit: 200 })
    const list = Array.isArray(res) ? res : (res.items || res.data || [])
    const map = {}
    list.forEach((m) => { map[m.id] = { hostname: m.hostname, ip: m.ip, code: m.code } })
    machineMap.value = map
  } catch { /* ignored */ }
}

function resolveMachineInfo(machineId) {
  if (!machineId) return '-'
  const m = machineMap.value[machineId]
  if (!m) return `#${machineId}`
  if (m.hostname && m.ip) return `${m.hostname} (${m.ip})`
  if (m.hostname) return m.hostname
  if (m.ip) return m.ip
  return m.code || `#${machineId}`
}

function resolveTargetInfo(task) {
  if (!task || !task.target_id) return '-'
  if (task.target_type === 'machine') {
    const id = parseInt(task.target_id)
    if (id) return resolveMachineInfo(id)
  }
  if (task.target_type === 'machines' || String(task.target_id).includes(',')) {
    const ids = String(task.target_id).split(',').map((s) => parseInt(s.trim())).filter(Boolean)
    return ids.map((id) => resolveMachineInfo(id)).join('、')
  }
  if (task.target_type === 'user') return `用户 #${task.target_id}`
  if (task.target_type === 'department') return `部门: ${task.target_id}`
  return task.target_id
}

function formatTime(val) {
  if (!val) return '-'
  return new Date(val).toLocaleString('zh-CN')
}

async function loadTasks() {
  listLoading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.size,
      limit: pagination.size,
      ...filters,
    }
    Object.keys(params).forEach((key) => {
      if (params[key] === '' || params[key] == null) delete params[key]
    })
    const res = await getDeployTasks(params)
    tasks.value = Array.isArray(res) ? res : (res.items || res.data || [])
    pagination.total = res.total || tasks.value.length
  } catch {
    // error handled by interceptor
  } finally {
    listLoading.value = false
  }
}

function resetFilters() {
  filters.task_type = ''
  filters.status = ''
  pagination.page = 1
  loadTasks()
}

async function showTaskDetail(row) {
  detailDialogVisible.value = true
  detailLoading.value = true
  currentTask.value = {}
  try {
    const res = await getDeployTask(row.id)
    // Backend returns {task: {...}, items: [...]}
    if (res && res.task) {
      currentTask.value = { ...res.task, items: res.items || [] }
    } else {
      currentTask.value = res || {}
    }
  } catch {
    // error handled by interceptor
  } finally {
    detailLoading.value = false
  }
}

async function handleCreate() {
  const form = createFormRef.value
  if (!form) return
  try {
    await form.validate()
  } catch {
    return
  }

  creating.value = true
  try {
    const data = {
      task_type: createForm.task_type,
      target_type: createForm.target_type,
      target_id: createForm.target_id,
    }
    if (createForm.payload_json.trim()) {
      try {
        data.payload = JSON.parse(createForm.payload_json)
      } catch {
        ElMessage.error('任务数据JSON格式错误')
        return
      }
    }
    await createDeployTask(data)
    ElMessage.success('任务创建成功')
    resetCreateForm()
    // Switch to list tab and refresh
    activeTab.value = 'list'
    loadTasks()
  } catch {
    // error handled by interceptor
  } finally {
    creating.value = false
  }
}

function resetCreateForm() {
  createForm.task_type = ''
  createForm.target_type = ''
  createForm.target_id = ''
  createForm.payload_json = ''
  createFormRef.value?.resetFields()
}

onMounted(() => {
  loadTasks()
  loadMachineMap()
})
</script>

<style scoped>
.deploy-task-list {
  padding: 0;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.filter-form {
  margin-bottom: 16px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.detail-descriptions {
  margin-bottom: 8px;
}
</style>
