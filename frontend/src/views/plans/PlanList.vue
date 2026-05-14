<template>
  <div class="oc-page">
    <div class="oc-page-header">
      <h1 class="oc-page-header__title">套餐管理</h1>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        新增套餐
      </el-button>
    </div>

    <!-- Plan Table -->
    <el-card shadow="never" class="oc-table-card">
      <el-table v-loading="loading" :data="plans" stripe border style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="provider" label="服务商" width="120" show-overflow-tooltip />
        <el-table-column prop="plan_name" label="套餐名称" min-width="140" show-overflow-tooltip />
        <el-table-column label="月费用" width="100" align="right">
          <template #default="{ row }">
            {{ row.monthly_cost != null ? `¥${row.monthly_cost}` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="quota_type" label="额度类型" width="110" align="center" />
        <el-table-column prop="quota_limit" label="额度上限" width="110" align="right">
          <template #default="{ row }">
            {{ row.quota_limit != null ? row.quota_limit.toLocaleString() : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="quota_used" label="已用额度" width="110" align="right">
          <template #default="{ row }">
            {{ row.quota_used != null ? row.quota_used.toLocaleString() : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="使用率" width="180" align="center">
          <template #default="{ row }">
            <el-progress
              :percentage="calcUsagePercent(row)"
              :color="getUsageColor(row)"
              :stroke-width="14"
              :text-inside="true"
              :format="(pct) => `${pct}%`"
            />
          </template>
        </el-table-column>
        <el-table-column label="API" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.has_api_key" type="success" size="small">已绑定</el-tag>
            <el-tag v-else type="info" size="small">未绑定</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="模型数" width="80" align="center">
          <template #default="{ row }">
            {{ row.supported_models?.length || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showDetailDialog(row)">详情</el-button>
            <el-button type="danger" link size="small" @click="handleDeletePlan(row)">删除</el-button>
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
          @size-change="loadPlans"
          @current-change="loadPlans"
        />
      </div>
    </el-card>

    <!-- Add Plan Dialog — Two-step Wizard -->
    <el-dialog
      v-model="addDialogVisible"
      :title="addStep === 1 ? '新增套餐 — API 连接' : '新增套餐 — 套餐详情'"
      width="680px"
      destroy-on-close
      @closed="resetAddForm"
    >
      <!-- Step 1: API Connection -->
      <div v-show="addStep === 1">
        <el-form :model="apiForm" label-width="100px">
          <el-form-item label="服务商">
            <el-select v-model="apiForm.provider" placeholder="选择服务商" style="width: 100%" @change="onProviderChange">
              <el-option label="OpenAI" value="openai" />
              <el-option label="Anthropic" value="anthropic" />
              <el-option label="其他 (OpenAI 兼容)" value="other" />
            </el-select>
          </el-form-item>
          <el-form-item label="API 地址">
            <el-input v-model="apiForm.api_url" placeholder="如 https://api.openai.com/v1" />
          </el-form-item>
          <el-form-item label="API Key">
            <el-input v-model="apiForm.api_key" type="password" show-password placeholder="sk-..." />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="probeLoading" @click="handleProbe">
              测试连接
            </el-button>
          </el-form-item>
        </el-form>

        <!-- Probe Result -->
        <div v-if="probeResult">
          <el-alert
            :title="probeResult.success ? '连接成功' : '连接失败'"
            :type="probeResult.success ? 'success' : 'error'"
            :description="probeResult.error || ''"
            show-icon
            :closable="false"
            style="margin-bottom: 16px"
          />

          <template v-if="probeResult.success">
            <!-- Rate Limits / Balance -->
            <div v-if="probeResult.rate_limits || probeResult.balance_info" style="margin-bottom: 16px">
              <el-descriptions :column="2" border size="small" title="API 信息">
                <el-descriptions-item v-if="probeResult.rate_limits" label="速率限制">
                  <div v-for="(v, k) in probeResult.rate_limits" :key="k" style="font-size: 12px">
                    {{ k }}: {{ v }}
                  </div>
                </el-descriptions-item>
                <el-descriptions-item v-if="probeResult.balance_info" label="余额信息">
                  <div style="font-size: 12px">{{ JSON.stringify(probeResult.balance_info).slice(0, 200) }}</div>
                </el-descriptions-item>
                <el-descriptions-item v-if="probeResult.provider_detected" label="识别服务商">
                  {{ probeResult.provider_detected }}
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- Model Selection -->
            <div style="margin-bottom: 8px; font-weight: 600">
              可用模型 ({{ probeResult.models.length }}) — 勾选关联模型
            </div>
            <el-checkbox-group v-model="selectedModels" style="max-height: 240px; overflow-y: auto; border: 1px solid var(--oc-border-color); border-radius: 6px; padding: 12px;">
              <el-checkbox v-for="m in probeResult.models" :key="m.id" :value="m.id" style="width: 100%; margin-bottom: 4px">
                <span style="font-family: monospace; font-size: 13px">{{ m.id }}</span>
                <span v-if="m.owned_by" style="color: var(--oc-text-secondary); font-size: 12px; margin-left: 8px">{{ m.owned_by }}</span>
              </el-checkbox>
            </el-checkbox-group>
            <div style="margin-top: 8px; color: var(--oc-text-secondary); font-size: 12px">
              已选择 {{ selectedModels.length }} / {{ probeResult.models.length }} 个模型
            </div>
          </template>
        </div>
      </div>

      <!-- Step 2: Plan Details -->
      <div v-show="addStep === 2">
        <el-form ref="addFormRef" :model="addForm" :rules="addFormRules" label-width="100px">
          <el-form-item label="服务商">
            <el-input :model-value="providerLabel" disabled />
          </el-form-item>
          <el-form-item label="套餐名称" prop="plan_name">
            <el-input v-model="addForm.plan_name" placeholder="请输入套餐名称" />
          </el-form-item>
          <el-form-item label="月费用" prop="monthly_cost">
            <el-input-number v-model="addForm.monthly_cost" :min="0" :precision="2" controls-position="right" style="width: 100%" />
          </el-form-item>
          <el-form-item label="额度类型" prop="quota_type">
            <el-select v-model="addForm.quota_type" placeholder="请选择额度类型" style="width: 100%">
              <el-option label="调用次数" value="calls" />
              <el-option label="Token数量" value="tokens" />
              <el-option label="无限制" value="unlimited" />
            </el-select>
          </el-form-item>
          <el-form-item label="额度上限" prop="quota_limit">
            <el-input-number v-model="addForm.quota_limit" :min="1" controls-position="right" style="width: 100%" />
          </el-form-item>
          <el-form-item label="计费周期" prop="billing_cycle">
            <el-select v-model="addForm.billing_cycle" placeholder="请选择计费周期" style="width: 100%">
              <el-option label="月" value="monthly" />
              <el-option label="年" value="yearly" />
            </el-select>
          </el-form-item>
          <el-form-item label="预警阈值" prop="warning_threshold">
            <el-input-number v-model="addForm.warning_threshold" :min="0" :max="100" controls-position="right" style="width: 100%" />
          </el-form-item>
          <el-form-item v-if="selectedModels.length > 0" label="关联模型">
            <el-tag v-for="m in selectedModels" :key="m" size="small" style="margin: 2px">{{ m }}</el-tag>
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div style="display: flex; justify-content: space-between; width: 100%">
          <div>
            <el-button v-if="addStep === 2" @click="addStep = 1">上一步</el-button>
          </div>
          <div>
            <el-button @click="addDialogVisible = false">取消</el-button>
            <el-button v-if="addStep === 1" type="primary" :disabled="!canGoNext" @click="goToStep2">下一步</el-button>
            <el-button v-if="addStep === 2" type="primary" :loading="submitting" @click="handleAdd">确定</el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- Plan Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      title="套餐详情"
      width="900px"
      destroy-on-close
    >
      <div v-loading="detailLoading">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="服务商">{{ detailPlan.provider }}</el-descriptions-item>
          <el-descriptions-item label="套餐名称">{{ detailPlan.plan_name }}</el-descriptions-item>
          <el-descriptions-item label="月费用">
            {{ detailPlan.monthly_cost != null ? `¥${detailPlan.monthly_cost}` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="额度类型">{{ detailPlan.quota_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="额度上限">
            {{ detailPlan.quota_limit != null ? detailPlan.quota_limit.toLocaleString() : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="计费周期">{{ detailPlan.billing_cycle || '-' }}</el-descriptions-item>
          <el-descriptions-item label="预警阈值">
            {{ detailPlan.warning_threshold != null ? `${detailPlan.warning_threshold}%` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="API 绑定">
            <el-tag :type="detailPlan.has_api_key ? 'success' : 'info'" size="small">
              {{ detailPlan.has_api_key ? '已绑定' : '未绑定' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="API 地址">
            {{ detailPlan.api_url || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- Supported Models -->
        <div v-if="detailPlan.supported_models && detailPlan.supported_models.length > 0" style="margin-top: 16px">
          <h4 style="margin: 0 0 8px">关联模型 ({{ detailPlan.supported_models.length }})</h4>
          <div style="max-height: 120px; overflow-y: auto;">
            <el-tag v-for="m in detailPlan.supported_models" :key="m" size="small" style="margin: 2px">{{ m }}</el-tag>
          </div>
        </div>

        <!-- Rate Limits / Balance -->
        <div v-if="detailPlan.rate_limits || detailPlan.balance_info" style="margin-top: 16px">
          <h4 style="margin: 0 0 8px">API 信息</h4>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item v-if="detailPlan.rate_limits" label="速率限制">
              <div v-for="(v, k) in detailPlan.rate_limits" :key="k" style="font-size: 12px">{{ k }}: {{ v }}</div>
            </el-descriptions-item>
            <el-descriptions-item v-if="detailPlan.balance_info" label="余额信息">
              <div style="font-size: 12px">{{ JSON.stringify(detailPlan.balance_info).slice(0, 300) }}</div>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- Bindings Table -->
        <h4 style="margin: 20px 0 10px">绑定列表</h4>
        <el-table :data="bindings" stripe border size="small" style="width: 100%">
          <el-table-column prop="user_id" label="用户ID" width="100" align="center" />
          <el-table-column prop="machine_id" label="机器ID" min-width="140" show-overflow-tooltip />
          <el-table-column prop="weight" label="权重" width="80" align="center" />
          <el-table-column prop="start_date" label="开始日期" width="120" align="center" />
          <el-table-column prop="end_date" label="结束日期" width="120" align="center" />
        </el-table>

        <!-- Add Binding Form -->
        <h4 style="margin: 20px 0 10px">添加绑定</h4>
        <el-form ref="bindingFormRef" :model="bindingForm" :rules="bindingFormRules" label-width="80px" :inline="true">
          <el-form-item label="用户ID" prop="user_id">
            <el-input v-model="bindingForm.user_id" placeholder="用户ID" style="width: 120px" />
          </el-form-item>
          <el-form-item label="机器ID" prop="machine_id">
            <el-input v-model="bindingForm.machine_id" placeholder="机器ID" style="width: 160px" />
          </el-form-item>
          <el-form-item label="权重" prop="weight">
            <el-input-number v-model="bindingForm.weight" :min="1" :max="100" controls-position="right" style="width: 120px" />
          </el-form-item>
          <el-form-item label="开始日期" prop="start_date">
            <el-date-picker v-model="bindingForm.start_date" type="date" placeholder="开始日期" value-format="YYYY-MM-DD" style="width: 150px" />
          </el-form-item>
          <el-form-item label="结束日期" prop="end_date">
            <el-date-picker v-model="bindingForm.end_date" type="date" placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 150px" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="bindingSubmitting" @click="handleAddBinding">添加</el-button>
          </el-form-item>
        </el-form>

        <!-- Cost Stats -->
        <h4 style="margin: 20px 0 10px">费用统计</h4>
        <el-descriptions v-if="costStats" :column="2" border>
          <el-descriptions-item label="总调用次数">{{ costStats.total_calls != null ? costStats.total_calls.toLocaleString() : '-' }}</el-descriptions-item>
          <el-descriptions-item label="总Token数">{{ costStats.total_tokens != null ? costStats.total_tokens.toLocaleString() : '-' }}</el-descriptions-item>
          <el-descriptions-item label="使用率">
            <el-progress :percentage="costStats.usage_percentage ?? 0" :color="getCostStatsColor(costStats)" :stroke-width="14" :text-inside="true" :format="(pct) => `${pct}%`" />
          </el-descriptions-item>
          <el-descriptions-item label="预警状态">
            <el-tag :type="costStats.is_warning ? 'warning' : 'success'" size="small">{{ costStats.is_warning ? '已预警' : '正常' }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <el-empty v-else description="暂无费用统计数据" :image-size="60" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getPlans,
  createPlan,
  getPlanBindings,
  createPlanBinding,
  getPlanCostStats,
  deletePlan,
  probeApi,
} from '../../api/plan'

const loading = ref(false)
const plans = ref([])
const submitting = ref(false)

const pagination = reactive({ page: 1, size: 10, total: 0 })

// ---------- Add Plan Wizard ----------
const addDialogVisible = ref(false)
const addStep = ref(1)
const addFormRef = ref(null)

const apiForm = reactive({
  provider: 'openai',
  api_url: 'https://api.openai.com/v1',
  api_key: '',
})

const probeLoading = ref(false)
const probeResult = ref(null)
const selectedModels = ref([])

const addForm = reactive({
  plan_name: '',
  monthly_cost: 0,
  quota_type: 'tokens',
  quota_limit: 1000,
  billing_cycle: 'monthly',
  warning_threshold: 80,
})

const addFormRules = {
  plan_name: [{ required: true, message: '请输入套餐名称', trigger: 'blur' }],
  quota_type: [{ required: true, message: '请选择额度类型', trigger: 'change' }],
  quota_limit: [{ required: true, message: '请输入额度上限', trigger: 'blur' }],
}

const providerLabel = computed(() => {
  const map = { openai: 'OpenAI', anthropic: 'Anthropic', other: '其他' }
  return map[apiForm.provider] || apiForm.provider
})

const canGoNext = computed(() => {
  return apiForm.api_url && apiForm.api_key && probeResult.value?.success
})

function onProviderChange(val) {
  const urlMap = {
    openai: 'https://api.openai.com/v1',
    anthropic: 'https://api.anthropic.com/v1',
    other: '',
  }
  apiForm.api_url = urlMap[val] || ''
  probeResult.value = null
  selectedModels.value = []
}

async function handleProbe() {
  if (!apiForm.api_url || !apiForm.api_key) {
    ElMessage.warning('请先填写 API 地址和 Key')
    return
  }
  probeLoading.value = true
  probeResult.value = null
  try {
    const res = await probeApi({
      api_url: apiForm.api_url,
      api_key: apiForm.api_key,
      provider: apiForm.provider,
    })
    probeResult.value = res
    if (res.success) {
      ElMessage.success(`连接成功，发现 ${res.models?.length || 0} 个模型`)
    }
  } catch {
    probeResult.value = { success: false, error: '请求失败，请检查网络' }
  } finally {
    probeLoading.value = false
  }
}

function goToStep2() {
  // Auto-suggest plan name
  if (!addForm.plan_name) {
    const modelCount = selectedModels.value.length || probeResult.value?.models?.length || 0
    addForm.plan_name = `${providerLabel.value} - ${modelCount} 模型`
  }
  addStep.value = 2
}

function showAddDialog() {
  addStep.value = 1
  apiForm.provider = 'openai'
  apiForm.api_url = 'https://api.openai.com/v1'
  apiForm.api_key = ''
  probeResult.value = null
  selectedModels.value = []
  addForm.plan_name = ''
  addForm.monthly_cost = 0
  addForm.quota_type = 'tokens'
  addForm.quota_limit = 1000
  addForm.billing_cycle = 'monthly'
  addForm.warning_threshold = 80
  addDialogVisible.value = true
}

function resetAddForm() {
  addStep.value = 1
  probeResult.value = null
  selectedModels.value = []
}

async function handleAdd() {
  try {
    await addFormRef.value?.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    await createPlan({
      provider: apiForm.provider,
      plan_name: addForm.plan_name,
      monthly_cost: addForm.monthly_cost,
      quota_type: addForm.quota_type,
      quota_limit: addForm.quota_limit,
      billing_cycle: addForm.billing_cycle,
      warning_threshold: addForm.warning_threshold,
      api_url: apiForm.api_url,
      api_key: apiForm.api_key,
      supported_models: selectedModels.value.length > 0 ? selectedModels.value : null,
    })
    ElMessage.success('创建成功')
    addDialogVisible.value = false
    loadPlans()
  } catch {
    // handled by interceptor
  } finally {
    submitting.value = false
  }
}

// ---------- Detail Dialog ----------
const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const detailPlan = ref({})
const bindings = ref([])
const costStats = ref(null)

const bindingFormRef = ref(null)
const bindingSubmitting = ref(false)
const bindingForm = reactive({
  user_id: '',
  machine_id: '',
  weight: 1,
  start_date: '',
  end_date: '',
})

const bindingFormRules = {
  user_id: [{ required: true, message: '请输入用户ID', trigger: 'blur' }],
  weight: [{ required: true, message: '请输入权重', trigger: 'blur' }],
}

function calcUsagePercent(row) {
  if (!row.quota_limit || row.quota_limit === 0) return 0
  const pct = Math.round((row.quota_used / row.quota_limit) * 100)
  return Math.min(pct, 100)
}

function getUsageColor(row) {
  const pct = calcUsagePercent(row)
  if (pct >= 100) return '#F56C6C'
  const threshold = row.warning_threshold ?? 80
  if (pct >= threshold) return '#E6A23C'
  return '#dc3545'
}

function getCostStatsColor(stats) {
  if (!stats) return '#dc3545'
  const pct = stats.usage_percentage ?? 0
  if (pct >= 100) return '#F56C6C'
  if (stats.is_warning) return '#E6A23C'
  return '#dc3545'
}

async function loadPlans() {
  loading.value = true
  try {
    const params = { skip: (pagination.page - 1) * pagination.size, limit: pagination.size }
    const res = await getPlans(params)
    plans.value = Array.isArray(res) ? res : (res.items || res.data || [])
    pagination.total = res.total || plans.value.length
  } catch {} finally {
    loading.value = false
  }
}

async function handleDeletePlan(row) {
  try {
    await ElMessageBox.confirm(`确定要删除套餐「${row.plan_name}」吗？将同时删除关联的绑定和用量记录。`, '删除确认', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning',
    })
  } catch { return }
  try {
    await deletePlan(row.id)
    ElMessage.success('套餐已删除')
    loadPlans()
  } catch {}
}

async function showDetailDialog(row) {
  detailPlan.value = row
  bindings.value = []
  costStats.value = null
  detailDialogVisible.value = true
  detailLoading.value = true
  try {
    const [bindingsRes, statsRes] = await Promise.all([
      getPlanBindings(row.id),
      getPlanCostStats(row.id),
    ])
    bindings.value = bindingsRes.items || bindingsRes.data || bindingsRes || []
    costStats.value = statsRes || null
  } catch {} finally {
    detailLoading.value = false
  }
}

async function loadBindings(planId) {
  try {
    const res = await getPlanBindings(planId)
    bindings.value = Array.isArray(res) ? res : (res.items || res.data || [])
  } catch {}
}

async function handleAddBinding() {
  try { await bindingFormRef.value?.validate() } catch { return }
  bindingSubmitting.value = true
  try {
    await createPlanBinding(detailPlan.value.id, {
      user_id: bindingForm.user_id,
      machine_id: bindingForm.machine_id,
      weight: bindingForm.weight,
      start_date: bindingForm.start_date,
      end_date: bindingForm.end_date,
    })
    ElMessage.success('绑定添加成功')
    bindingForm.user_id = ''
    bindingForm.machine_id = ''
    bindingForm.weight = 1
    bindingForm.start_date = ''
    bindingForm.end_date = ''
    loadBindings(detailPlan.value.id)
  } catch {} finally {
    bindingSubmitting.value = false
  }
}

onMounted(() => { loadPlans() })
</script>

<style scoped>
</style>
