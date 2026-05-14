<template>
  <div class="oc-page">
    <div class="oc-page-header">
      <h1 class="oc-page-header__title">AI配置</h1>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        新增配置
      </el-button>
    </div>

    <!-- Config Cards -->
    <el-row :gutter="16">
      <el-col :span="12" v-for="cfg in configs" :key="cfg.id">
        <el-card
          shadow="never"
          class="config-card"
          :class="{ 'config-card--active': cfg.is_active }"
        >
          <div class="config-card__header">
            <div class="config-card__title">
              <span>{{ cfg.name }}</span>
              <el-tag v-if="cfg.is_active" type="danger" size="small" effect="dark">当前使用</el-tag>
            </div>
            <el-tag :type="providerTag[cfg.provider]?.type" size="small">
              {{ providerTag[cfg.provider]?.label || cfg.provider }}
            </el-tag>
          </div>
          <div class="config-card__body">
            <div class="config-card__row">
              <span class="config-card__label">API地址</span>
              <span class="config-card__value">{{ cfg.api_url }}</span>
            </div>
            <div class="config-card__row">
              <span class="config-card__label">模型</span>
              <span class="config-card__value">{{ cfg.model_name || '-' }}</span>
            </div>
            <div class="config-card__row">
              <span class="config-card__label">API Key</span>
              <span class="config-card__value">{{ cfg.has_api_key ? '已配置' : '未配置' }}</span>
            </div>
          </div>
          <div class="config-card__actions">
            <el-button v-if="!cfg.is_active" type="primary" size="small" @click="handleSetActive(cfg)">
              设为激活
            </el-button>
            <el-button size="small" @click="handleTestConnection(cfg)">测试连接</el-button>
            <el-button size="small" @click="showEditDialog(cfg)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(cfg)">删除</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="!loading && configs.length === 0" description="暂无AI配置，请点击新增" />

    <!-- Add/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑AI配置' : '新增AI配置'"
      width="560px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="form.name" placeholder="如：OpenAI GPT-4o" />
        </el-form-item>
        <el-form-item label="服务商" prop="provider">
          <el-select v-model="form.provider" placeholder="请选择" style="width: 100%" @change="onProviderChange">
            <el-option label="OpenAI 兼容" value="openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="API 地址" prop="api_url">
          <el-input v-model="form.api_url" placeholder="如：https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            :placeholder="isEditing ? '留空则保持原值' : '请输入 API Key'"
          />
        </el-form-item>
        <el-form-item label="模型名称" prop="model_name">
          <el-input v-model="form.model_name" placeholder="如：gpt-4o / claude-sonnet-4-20250514" />
        </el-form-item>
        <el-form-item>
          <el-button :loading="testing" @click="handleTestInDialog">测试连接</el-button>
          <span v-if="testResult" :style="{ color: testResult.success ? '#16a34a' : '#dc2626', marginLeft: '8px', fontSize: '13px' }">
            {{ testResult.success ? '连接成功 ' + (testResult.model_info || '') : testResult.error }}
          </span>
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
import { Plus } from '@element-plus/icons-vue'
import {
  getAIConfigs,
  createAIConfig,
  updateAIConfig,
  deleteAIConfig,
  testConnection,
  testConfigConnection,
  setActiveConfig,
} from '../../api/aiConfig'

const providerTag = {
  openai: { label: 'OpenAI', type: '' },
  anthropic: { label: 'Anthropic', type: 'warning' },
  other: { label: '其他', type: 'info' },
}

const loading = ref(false)
const configs = ref([])
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const testing = ref(false)
const testResult = ref(null)
const formRef = ref(null)

const form = reactive({
  name: '',
  provider: 'openai',
  api_url: '',
  api_key: '',
  model_name: '',
})

const formRules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择服务商', trigger: 'change' }],
  api_url: [{ required: true, message: '请输入API地址', trigger: 'blur' }],
}

const providerDefaults = {
  openai: 'https://api.openai.com/v1',
  anthropic: 'https://api.anthropic.com',
  other: '',
}

function onProviderChange(val) {
  if (!form.api_url || Object.values(providerDefaults).includes(form.api_url)) {
    form.api_url = providerDefaults[val]
  }
}

async function loadConfigs() {
  loading.value = true
  try {
    const res = await getAIConfigs()
    configs.value = res.items || []
  } catch {} finally {
    loading.value = false
  }
}

function showAddDialog() {
  isEditing.value = false
  editingId.value = null
  form.name = ''
  form.provider = 'openai'
  form.api_url = providerDefaults.openai
  form.api_key = ''
  form.model_name = ''
  testResult.value = null
  dialogVisible.value = true
}

function showEditDialog(cfg) {
  isEditing.value = true
  editingId.value = cfg.id
  form.name = cfg.name
  form.provider = cfg.provider
  form.api_url = cfg.api_url
  form.api_key = ''
  form.model_name = cfg.model_name || ''
  testResult.value = null
  dialogVisible.value = true
}

async function handleTestInDialog() {
  if (!form.api_url || !form.api_key) {
    ElMessage.warning('请先填写 API 地址和 API Key')
    return
  }
  testing.value = true
  testResult.value = null
  try {
    testResult.value = await testConnection({
      api_url: form.api_url,
      api_key: form.api_key,
      provider: form.provider,
      model_name: form.model_name || undefined,
    })
  } catch {
    testResult.value = { success: false, error: '请求失败' }
  } finally {
    testing.value = false
  }
}

async function handleTestConnection(cfg) {
  try {
    const res = await testConfigConnection(cfg.id)
    if (res.success) {
      ElMessage.success('连接成功' + (res.model_info ? ` (${res.model_info})` : ''))
    } else {
      ElMessage.error(res.error || '连接失败')
    }
  } catch {
    ElMessage.error('测试请求失败')
  }
}

async function handleSubmit() {
  const formEl = formRef.value
  if (!formEl) return
  try { await formEl.validate() } catch { return }

  submitting.value = true
  try {
    const data = { ...form }
    if (isEditing.value) {
      await updateAIConfig(editingId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createAIConfig(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadConfigs()
  } catch {} finally {
    submitting.value = false
  }
}

async function handleSetActive(cfg) {
  try {
    await setActiveConfig(cfg.id)
    ElMessage.success('已设为激活')
    loadConfigs()
  } catch {}
}

async function handleDelete(cfg) {
  try {
    await ElMessageBox.confirm(
      `确定要删除AI配置「${cfg.name}」吗？`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    await deleteAIConfig(cfg.id)
    ElMessage.success('已删除')
    loadConfigs()
  } catch {}
}

onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.config-card {
  margin-bottom: 16px;
  transition: border-color 0.2s;
}

.config-card--active {
  border-left: 4px solid var(--oc-color-primary);
}

.config-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.config-card__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--oc-text-primary);
}

.config-card__body {
  margin-bottom: 12px;
}

.config-card__row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 13px;
}

.config-card__label {
  color: var(--oc-text-secondary);
}

.config-card__value {
  color: var(--oc-text-primary);
  font-weight: 500;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.config-card__actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--oc-border-color-light);
}
</style>
