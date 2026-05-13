<template>
  <div class="oc-page">
    <!-- 搜索筛选区 -->
    <el-card class="oc-filter-card" shadow="never">
      <el-form :model="filters" inline>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="姓名/用户名" clearable style="width: 180px" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="filters.department" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="d in departmentOptions" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="岗位">
          <el-select v-model="filters.position" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="p in positionOptions" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="filters.role" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="r in roleOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
      <el-button type="primary" :icon="Plus" @click="openDialog('create')">新增用户</el-button>
    </el-card>

    <!-- 数据表格 -->
    <el-card shadow="never" class="oc-table-card">
      <el-table v-loading="loading" :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="name" label="姓名" min-width="100" />
        <el-table-column prop="username" label="用户名" min-width="110" />
        <el-table-column prop="company" label="公司" min-width="120" />
        <el-table-column prop="department" label="部门" min-width="100" />
        <el-table-column prop="position" label="岗位" min-width="100" />
        <el-table-column prop="role" label="角色" min-width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)">{{ roleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
              {{ row.status === 'active' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDialog('edit', row)">编辑</el-button>
            <el-button link type="primary" size="small" style="margin-left: 8px" @click="goDetail(row.id)">查看</el-button>
            <el-button link type="danger" size="small" style="margin-left: 8px" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="oc-pagination">
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
      :title="dialogMode === 'create' ? '新增用户' : '编辑用户'"
      width="560px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="90px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="formData.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" placeholder="请输入用户名" :disabled="dialogMode === 'edit'" />
        </el-form-item>
        <el-form-item v-if="dialogMode === 'create'" label="密码" prop="password">
          <el-input v-model="formData.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="公司" prop="company">
          <el-input v-model="formData.company" placeholder="请输入公司" />
        </el-form-item>
        <el-form-item label="部门" prop="department">
          <el-input v-model="formData.department" placeholder="请输入部门" />
        </el-form-item>
        <el-form-item label="岗位" prop="position">
          <el-input v-model="formData.position" placeholder="请输入岗位" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="formData.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="运维负责人" prop="support_owner">
          <el-input v-model="formData.support_owner" placeholder="请输入运维负责人" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="formData.role" placeholder="请选择角色" style="width: 100%">
            <el-option v-for="r in roleOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="disabled" />
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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { getUsers, createUser, updateUser, deleteUser } from '../../api/user'

const router = useRouter()

// ---------- 筛选 ----------
const filters = reactive({
  keyword: '',
  department: '',
  position: '',
  role: '',
  status: '',
})

const departmentOptions = ['研发部', '产品部', '设计部', '市场部', '运维部', '行政部']
const positionOptions = ['工程师', '产品经理', '设计师', '运营', '主管', '经理']
const roleOptions = [
  { value: 'admin', label: '管理员' },
  { value: 'support', label: '运维' },
  { value: 'ops', label: '运营' },
  { value: 'manager', label: '经理' },
  { value: 'user', label: '普通用户' },
]

const roleTagType = (role) => {
  const map = { admin: 'danger', support: 'warning', ops: 'info', manager: 'success', user: '' }
  return map[role] || ''
}
const roleLabel = (role) => {
  const map = { admin: '管理员', support: '运维', ops: '运营', manager: '经理', user: '普通用户' }
  return map[role] || role
}

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
    const res = await getUsers(params)
    tableData.value = Array.isArray(res) ? res : (res.items || res.data || [])
    pagination.total = res.total || tableData.value.length
  } catch {
    // 错误已由 request 拦截器处理
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchData()
}

function handleReset() {
  Object.assign(filters, { keyword: '', department: '', position: '', role: '', status: '' })
  pagination.page = 1
  fetchData()
}

// ---------- 对话框 ----------
const dialogVisible = ref(false)
const dialogMode = ref('create')
const submitting = ref(false)
const formRef = ref(null)

const defaultForm = () => ({
  name: '',
  username: '',
  password: '',
  company: '',
  department: '',
  position: '',
  phone: '',
  support_owner: '',
  role: 'user',
  status: 'active',
})

const formData = reactive(defaultForm())

const formRules = reactive({
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
})

function openDialog(mode, row = null) {
  dialogMode.value = mode
  if (mode === 'edit' && row) {
    Object.keys(defaultForm()).forEach((k) => {
      formData[k] = row[k] ?? defaultForm()[k]
    })
    delete formData.password
  } else {
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
    if (dialogMode.value === 'create') {
      const payload = { ...formData }
      await createUser(payload)
      ElMessage.success('用户创建成功')
    } else {
      const payload = { ...formData }
      delete payload.password
      delete payload.username
      await updateUser(payload.id || formData.id, payload)
      ElMessage.success('用户更新成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch {
    // 已由拦截器处理
  } finally {
    submitting.value = false
  }
}

// ---------- 跳转详情 ----------
function goDetail(id) {
  router.push(`/users/${id}`)
}

// ---------- 删除 ----------
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除用户「${row.name}」吗？此操作不可恢复。`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteUser(row.id)
    ElMessage.success('用户已删除')
    fetchData()
  } catch {
    // handled by interceptor
  }
}

// ---------- 初始化 ----------
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
</style>
