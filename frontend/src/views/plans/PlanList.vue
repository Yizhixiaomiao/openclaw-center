<template>
  <div class="plan-list">
    <div class="page-header">
      <h2>套餐管理</h2>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        新增套餐
      </el-button>
    </div>

    <!-- Plan Table -->
    <el-card shadow="never">
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
        <el-table-column label="预警阈值" width="90" align="center">
          <template #default="{ row }">
            {{ row.warning_threshold != null ? `${row.warning_threshold}%` : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active !== false ? 'success' : 'info'" size="small">
              {{ row.is_active !== false ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showDetailDialog(row)">
              详情
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
          @size-change="loadPlans"
          @current-change="loadPlans"
        />
      </div>
    </el-card>

    <!-- Add Plan Dialog -->
    <el-dialog
      v-model="addDialogVisible"
      title="新增套餐"
      width="560px"
      destroy-on-close
    >
      <el-form
        ref="addFormRef"
        :model="addForm"
        :rules="addFormRules"
        label-width="100px"
      >
        <el-form-item label="服务商" prop="provider">
          <el-input v-model="addForm.provider" placeholder="请输入服务商名称" />
        </el-form-item>
        <el-form-item label="套餐名称" prop="plan_name">
          <el-input v-model="addForm.plan_name" placeholder="请输入套餐名称" />
        </el-form-item>
        <el-form-item label="月费用" prop="monthly_cost">
          <el-input-number
            v-model="addForm.monthly_cost"
            :min="0"
            :precision="2"
            controls-position="right"
            placeholder="月费用"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="额度类型" prop="quota_type">
          <el-select v-model="addForm.quota_type" placeholder="请选择额度类型" style="width: 100%">
            <el-option label="调用次数" value="calls" />
            <el-option label="Token数量" value="tokens" />
            <el-option label="金额" value="amount" />
          </el-select>
        </el-form-item>
        <el-form-item label="额度上限" prop="quota_limit">
          <el-input-number
            v-model="addForm.quota_limit"
            :min="1"
            controls-position="right"
            placeholder="额度上限"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="计费周期" prop="billing_cycle">
          <el-select v-model="addForm.billing_cycle" placeholder="请选择计费周期" style="width: 100%">
            <el-option label="月" value="monthly" />
            <el-option label="年" value="yearly" />
          </el-select>
        </el-form-item>
        <el-form-item label="预警阈值" prop="warning_threshold">
          <el-input-number
            v-model="addForm.warning_threshold"
            :min="0"
            :max="100"
            controls-position="right"
            placeholder="预警阈值(%)"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleAdd">确定</el-button>
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
        <!-- Plan Info -->
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
          <el-descriptions-item label="状态">
            <el-tag :type="detailPlan.is_active !== false ? 'success' : 'info'" size="small">
              {{ detailPlan.is_active !== false ? '启用' : '停用' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- Bindings Table -->
        <h4 style="margin: 20px 0 10px">绑定列表</h4>
        <el-table
          :data="bindings"
          stripe
          border
          size="small"
          style="width: 100%"
        >
          <el-table-column prop="user_id" label="用户ID" width="100" align="center" />
          <el-table-column prop="machine_id" label="机器ID" min-width="140" show-overflow-tooltip />
          <el-table-column prop="weight" label="权重" width="80" align="center" />
          <el-table-column prop="start_date" label="开始日期" width="120" align="center" />
          <el-table-column prop="end_date" label="结束日期" width="120" align="center" />
        </el-table>

        <!-- Add Binding Form -->
        <h4 style="margin: 20px 0 10px">添加绑定</h4>
        <el-form
          ref="bindingFormRef"
          :model="bindingForm"
          :rules="bindingFormRules"
          label-width="80px"
          :inline="true"
        >
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
            <el-date-picker
              v-model="bindingForm.start_date"
              type="date"
              placeholder="开始日期"
              value-format="YYYY-MM-DD"
              style="width: 150px"
            />
          </el-form-item>
          <el-form-item label="结束日期" prop="end_date">
            <el-date-picker
              v-model="bindingForm.end_date"
              type="date"
              placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="width: 150px"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="bindingSubmitting" @click="handleAddBinding">
              添加
            </el-button>
          </el-form-item>
        </el-form>

        <!-- Cost Stats -->
        <h4 style="margin: 20px 0 10px">费用统计</h4>
        <el-descriptions v-if="costStats" :column="2" border>
          <el-descriptions-item label="总调用次数">
            {{ costStats.total_calls != null ? costStats.total_calls.toLocaleString() : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="总Token数">
            {{ costStats.total_tokens != null ? costStats.total_tokens.toLocaleString() : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="使用率">
            <el-progress
              :percentage="costStats.usage_percentage ?? 0"
              :color="getCostStatsColor(costStats)"
              :stroke-width="14"
              :text-inside="true"
              :format="(pct) => `${pct}%`"
            />
          </el-descriptions-item>
          <el-descriptions-item label="预警状态">
            <el-tag
              :type="costStats.is_warning ? 'warning' : 'success'"
              size="small"
            >
              {{ costStats.is_warning ? '已预警' : '正常' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <el-empty v-else description="暂无费用统计数据" :image-size="60" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getPlans,
  createPlan,
  getPlanBindings,
  createPlanBinding,
  getPlanCostStats,
} from '../../api/plan'

const loading = ref(false)
const plans = ref([])
const submitting = ref(false)

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0,
})

// Add Plan
const addDialogVisible = ref(false)
const addFormRef = ref(null)

const addForm = reactive({
  provider: '',
  plan_name: '',
  monthly_cost: 0,
  quota_type: '',
  quota_limit: 1000,
  billing_cycle: 'monthly',
  warning_threshold: 80,
})

const addFormRules = {
  provider: [{ required: true, message: '请输入服务商', trigger: 'blur' }],
  plan_name: [{ required: true, message: '请输入套餐名称', trigger: 'blur' }],
  quota_type: [{ required: true, message: '请选择额度类型', trigger: 'change' }],
  quota_limit: [{ required: true, message: '请输入额度上限', trigger: 'blur' }],
}

// Detail Dialog
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
  machine_id: [{ required: true, message: '请输入机器ID', trigger: 'blur' }],
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
  return '#409EFF'
}

function getCostStatsColor(stats) {
  if (!stats) return '#409EFF'
  const pct = stats.usage_percentage ?? 0
  if (pct >= 100) return '#F56C6C'
  if (stats.is_warning) return '#E6A23C'
  return '#409EFF'
}

async function loadPlans() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
    }
    const res = await getPlans(params)
    plans.value = res.items || res.data || []
    pagination.total = res.total || plans.value.length
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

function showAddDialog() {
  addForm.provider = ''
  addForm.plan_name = ''
  addForm.monthly_cost = 0
  addForm.quota_type = ''
  addForm.quota_limit = 1000
  addForm.billing_cycle = 'monthly'
  addForm.warning_threshold = 80
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
    await createPlan({
      provider: addForm.provider,
      plan_name: addForm.plan_name,
      monthly_cost: addForm.monthly_cost,
      quota_type: addForm.quota_type,
      quota_limit: addForm.quota_limit,
      billing_cycle: addForm.billing_cycle,
      warning_threshold: addForm.warning_threshold,
    })
    ElMessage.success('创建成功')
    addDialogVisible.value = false
    loadPlans()
  } catch {
    // error handled by interceptor
  } finally {
    submitting.value = false
  }
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
  } catch {
    // error handled by interceptor
  } finally {
    detailLoading.value = false
  }
}

async function loadBindings(planId) {
  try {
    const res = await getPlanBindings(planId)
    bindings.value = res.items || res.data || res || []
  } catch {
    // error handled by interceptor
  }
}

async function handleAddBinding() {
  const form = bindingFormRef.value
  if (!form) return
  try {
    await form.validate()
  } catch {
    return
  }

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
    // Reset form
    bindingForm.user_id = ''
    bindingForm.machine_id = ''
    bindingForm.weight = 1
    bindingForm.start_date = ''
    bindingForm.end_date = ''
    // Reload bindings
    loadBindings(detailPlan.value.id)
  } catch {
    // error handled by interceptor
  } finally {
    bindingSubmitting.value = false
  }
}

onMounted(() => {
  loadPlans()
})
</script>

<style scoped>
.plan-list {
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

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
