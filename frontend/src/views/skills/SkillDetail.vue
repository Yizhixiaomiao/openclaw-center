<template>
  <div class="oc-page" v-loading="loading">
    <div class="oc-page-header">
      <div style="display: flex; align-items: center; gap: 12px;">
        <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
        <h1 class="oc-page-header__title">技能详情</h1>
      </div>
    </div>

    <!-- 基本信息 -->
    <el-card shadow="never" class="oc-table-card">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="技能ID">{{ skill.id }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ skill.name }}</el-descriptions-item>
        <el-descriptions-item label="编码">{{ skill.code }}</el-descriptions-item>
        <el-descriptions-item label="版本">{{ skill.version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="来源">
          <el-tag v-if="skill.source === 'clawhub'" type="warning" size="small">ClawHub</el-tag>
          <el-tag v-else type="info" size="small">本地</el-tag>
          <span v-if="skill.clawhub_slug" style="margin-left: 6px; color: var(--el-text-color-secondary);">({{ skill.clawhub_slug }})</span>
        </el-descriptions-item>
        <el-descriptions-item label="适用岗位">{{ (skill.applicable_positions || []).join('、') || '-' }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="3">{{ skill.description || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 标签页 -->
    <el-card shadow="never" class="oc-table-card">
      <el-tabs v-model="activeTab">
        <!-- 已安装机器 -->
        <el-tab-pane label="已安装机器" name="machines">
          <el-table :data="machines" border stripe style="width: 100%">
            <el-table-column prop="machine_code" label="机器码" min-width="160" />
            <el-table-column prop="ip" label="IP" min-width="140" />
            <el-table-column prop="hostname" label="主机名" min-width="140" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'installed' ? 'success' : 'info'" size="small">
                  {{ row.status === 'installed' ? '已安装' : row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-button link type="danger" size="small" @click="removeFromMachine(row)">移除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="machines.length === 0" description="暂无机器安装此技能" />
        </el-tab-pane>

        <!-- 文件浏览 -->
        <el-tab-pane label="文件浏览" name="files">
          <div class="file-browser">
            <div class="file-tree-panel">
              <el-tree
                v-if="skillFiles.length > 0"
                :data="skillFiles"
                :props="{ label: 'path', children: 'children' }"
                node-key="path"
                highlight-current
                default-expand-all
                @node-click="onFileNodeClick"
              >
                <template #default="{ node, data }">
                  <span class="file-tree-node">
                    <span>{{ data.type === 'dir' ? '📁' : '📄' }} {{ node.label.split('/').pop() }}</span>
                    <span v-if="data.type === 'file'" class="file-size">{{ formatSize(data.size) }}</span>
                  </span>
                </template>
              </el-tree>
              <el-empty v-else description="暂无文件" :image-size="60" />
            </div>
            <div class="file-content-panel">
              <div v-if="selectedFilePath" class="file-content-header">
                <span>{{ selectedFilePath }}</span>
              </div>
              <el-input
                v-if="fileContent !== null"
                v-model="fileContent"
                type="textarea"
                :rows="20"
                readonly
                style="font-family: monospace; font-size: 13px"
              />
              <div v-else-if="selectedFilePath" class="file-content-placeholder">
                点击左侧文件查看内容
              </div>
              <div v-else class="file-content-placeholder">
                选择文件以查看内容
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getSkillDetail, removeSkillFromMachine, getSkillFiles, getSkillFileContent } from '../../api/skill'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const skillId = route.params.id

const loading = ref(false)
const skill = ref({})
const machines = ref([])
const activeTab = ref('machines')

const skillFiles = ref([])
const selectedFilePath = ref('')
const fileContent = ref(null)

function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

async function loadData() {
  loading.value = true
  try {
    const [res, filesRes] = await Promise.all([
      getSkillDetail(skillId),
      getSkillFiles(skillId),
    ])
    skill.value = res.skill || {}
    machines.value = res.machines || []
    skillFiles.value = filesRes.files || []
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

async function onFileNodeClick(data) {
  if (data.type === 'dir') return
  selectedFilePath.value = data.path
  fileContent.value = null
  try {
    const res = await getSkillFileContent(skill.value.id, data.path)
    fileContent.value = res.content || ''
  } catch {
    fileContent.value = '（读取文件内容失败）'
  }
}

async function removeFromMachine(row) {
  try {
    await ElMessageBox.confirm(
      `确定从机器「${row.hostname || row.machine_code}」移除技能「${skill.value.name}」吗？`,
      '确认移除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await removeSkillFromMachine(skill.value.id, row.machine_id)
    ElMessage.success('技能已移除')
    loadData()
  } catch {
    // cancelled
  }
}

function goBack() {
  router.push('/skills')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.file-browser {
  display: flex;
  border: 1px solid var(--oc-border-color);
  border-radius: var(--oc-radius-base);
  min-height: 400px;
}
.file-tree-panel {
  width: 260px;
  border-right: 1px solid var(--oc-border-color);
  overflow-y: auto;
  padding: 8px;
}
.file-content-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.file-content-header {
  padding: 8px 12px;
  border-bottom: 1px solid var(--oc-border-color);
  font-size: var(--oc-font-base);
  color: var(--oc-text-secondary);
  font-family: monospace;
}
.file-content-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--oc-text-placeholder);
  font-size: var(--oc-font-md);
}
.file-tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  font-size: var(--oc-font-base);
}
.file-size {
  color: var(--oc-text-secondary);
  font-size: var(--oc-font-sm);
  margin-left: 8px;
}
</style>
