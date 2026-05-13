# OpenClaw Center 前端风格开发手册

> 基于 OpenClaw UI 设计语言，将 Element Plus 默认风格改造为极简卡片式信息面板风格。

---

## 1. 设计原则

- **信息密度高**：一屏展示尽可能多的关键数据，减少翻页和跳转
- **卡片式布局**：所有内容按功能模块分组为白色圆角卡片
- **轻量扁平**：去除重阴影和渐变，用极细边框和极淡阴影区分层级
- **数据突出**：关键数字用大号粗体，辅助文字用小号灰色
- **操作隐式**：操作入口用文字 + 箭头（`→`），不喧宾夺主

---

## 2. 全局布局

### 2.1 整体结构

```
┌─────────────┬──────────────────────────────────────────┐
│  Logo       │  Breadcrumb   Search  [Btn] [Btn] [Btn] │  ← 顶栏 (64px)
──────┐      │                                          │
│ Nav  │      │                                          │
│ Menu │      │   主内容区 (卡片网格)                     │  ← 侧栏 (240px)
│      │      │                                          │
│      │      │                                          │
├──────┘      │                                          │
│ Version     │                                          │  ← 底栏 (48px)
─────────────┴──────────────────────────────────────────┘
```

### 2.2 侧边栏 (`el-menu`)

- 宽度：`240px`，固定不折叠
- 背景色：`#fafafa`（比主背景略浅）
- 菜单项高度：`40px`
- 激活态：左侧浅红色/珊瑚色指示条 + 浅粉背景 `rgba(220, 53, 69, 0.08)`
- 分组标题：小号灰色文字 `#9ca3af`，`text-transform: uppercase` 或加粗
- Logo：左上角，`24px` 高，旁边是品牌名
- 底部：版本号，灰色小字 + 绿色在线状态圆点

```css
.sidebar {
  width: 240px;
  background: #fafafa;
  border-right: 1px solid #e5e7eb;
}
.sidebar .el-menu-item.is-active {
  background: rgba(220, 53, 69, 0.08);
  color: #dc3545;
  border-left: 3px solid #dc3545;
}
.sidebar .menu-group-title {
  font-size: 11px;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 16px 20px 8px;
  font-weight: 600;
}
```

### 2.3 顶栏

- 高度：`64px`
- 左侧：面包屑导航 `el-breadcrumb`，红色高亮当前页
- 右侧：搜索框（圆角 pill 形状）+ 功能图标按钮
- 背景色：白色，底边框 `#e5e7eb`

```css
.topbar {
  height: 64px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.topbar .el-breadcrumb {
  font-size: 13px;
}
.topbar .el-breadcrumb__item:last-child .el-breadcrumb__inner {
  color: #dc3545;
  font-weight: 600;
}
.topbar .search-box {
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  padding: 6px 16px;
  font-size: 13px;
}
```

### 2.4 主内容区

- 背景色：`#f3f4f6`（浅灰）
- 内边距：`24px`
- 页面标题：`22px` 粗体，下方小号灰色描述文字

```css
.main-content {
  background: #f3f4f6;
  padding: 24px;
}
.page-header h1 {
  font-size: 22px;
  font-weight: 700;
  color: #dc3545;
  margin-bottom: 4px;
}
.page-header .subtitle {
  font-size: 13px;
  color: #6b7280;
}
```

---

## 3. 卡片组件 (`el-card`)

### 3.1 卡片样式

替换 Element Plus 默认卡片风格：

```css
.el-card {
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: none;
  background: #fff;
  margin-bottom: 16px;
}
.el-card__header {
  padding: 16px 20px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}
.el-card__body {
  padding: 20px;
}
```

### 3.2 卡片标题行

- 标题 + 图标（可选）在左侧
- 操作链接在右侧：小号文字 + `→` 箭头，颜色 `#dc3545`

```vue
<div class="card-header">
  <span><el-icon><Setting /></el-icon> Settings</span>
  <el-button link type="primary" size="small">Advanced →</el-button>
</div>
```

```css
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header .el-button--link {
  color: #dc3545;
  font-size: 12px;
}
```

### 3.3 卡片内数据行

Key-value 配对，行与行之间用极淡分割线：

```vue
<div class="card-row">
  <span class="card-row-label">Model</span>
  <span class="card-row-value">glm-5.1</span>
</div>
```

```css
.card-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
}
.card-row:last-child {
  border-bottom: none;
}
.card-row-label {
  font-size: 13px;
  color: #6b7280;
}
.card-row-value {
  font-size: 13px;
  color: #111827;
}
```

---

## 4. 数据指标卡片

用于 Dashboard 概览、统计数字展示：

### 4.1 大数字卡片

```vue
<el-card class="metric-card">
  <div class="metric-label">费用</div>
  <div class="metric-value">$0.00</div>
  <div class="metric-detail">0 tokens · 12 msgs</div>
</el-card>
```

```css
.metric-card {
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 20px;
  background: #fff;
}
.metric-card .metric-label {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 8px;
}
.metric-card .metric-value {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  line-height: 1.2;
}
.metric-card .metric-detail {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}
```

### 4.2 状态卡片

```vue
<el-card class="status-card">
  <div class="status-label">状态</div>
  <div class="status-value status-ok">正常</div>
</el-card>
```

```css
.status-card {
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 20px;
  background: #fff;
}
.status-card .status-label {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 8px;
}
.status-card .status-value {
  font-size: 22px;
  font-weight: 700;
}
.status-card .status-ok { color: #16a34a; }
.status-card .status-warn { color: #ea580c; }
.status-card .status-error { color: #dc2626; }
.status-card .status-info { color: #6b7280; }
```

### 4.3 指标网格布局

Dashboard 中多个指标卡片用 Grid 排列：

```vue
<div class="metrics-grid">
  <el-card class="metric-card">...</el-card>
  <el-card class="metric-card">...</el-card>
  <el-card class="metric-card">...</el-card>
  <el-card class="metric-card">...</el-card>
</div>
```

```css
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
@media (max-width: 1200px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .metrics-grid { grid-template-columns: 1fr; }
}
```

---

## 5. 表单与输入组件

### 5.1 输入框 (`el-input`)

```css
.el-input__wrapper {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: none;
  background: #fafafa;
}
.el-input__wrapper:hover {
  border-color: #d1d5db;
}
.el-input__wrapper.is-focus {
  border-color: #dc3545;
  box-shadow: 0 0 0 2px rgba(220, 53, 69, 0.1);
}
```

### 5.2 选择器 (`el-select`)

```css
.el-select .el-input__wrapper {
  border-radius: 8px;
}
```

### 5.3 按钮 (`el-button`)

替换 Element Plus 默认按钮风格：

```css
/* Primary - 品牌红 */
.el-button--primary {
  background: #dc3545;
  border-color: #dc3545;
  color: #fff;
  border-radius: 8px;
}
.el-button--primary:hover {
  background: #bb2d3b;
  border-color: #bb2d3b;
}

/* Default - 白色描边 */
.el-button--default {
  background: #fff;
  border: 1px solid #e5e7eb;
  color: #374151;
  border-radius: 8px;
}
.el-button--default:hover {
  border-color: #d1d5db;
  background: #f9fafb;
}

/* Link - 文字链接 */
.el-button--link {
  color: #dc3545;
  padding: 0;
  font-size: 12px;
}

/* Small size */
.el-button--small {
  padding: 4px 12px;
  font-size: 12px;
  border-radius: 6px;
}
```

### 5.4 标签/徽章 (`el-tag`)

```css
.el-tag {
  border-radius: 6px;
  border: none;
  font-weight: 500;
  font-size: 12px;
}
.el-tag--success {
  background: #dcfce7;
  color: #16a34a;
}
.el-tag--danger {
  background: #fee2e2;
  color: #dc2626;
}
.el-tag--warning {
  background: #fef3c7;
  color: #ea580c;
}
.el-tag--info {
  background: #f3f4f6;
  color: #6b7280;
}
.el-tag--primary {
  background: rgba(220, 53, 69, 0.08);
  color: #dc3545;
}
```

---

## 6. 表格组件 (`el-table`)

表格是数据密集页的核心（机器列表、任务列表等）：

```css
.el-table {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}
.el-table th.el-table__cell {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
  font-size: 13px;
  border-bottom: 1px solid #e5e7eb;
}
.el-table td.el-table__cell {
  font-size: 13px;
  color: #4b5563;
  border-bottom: 1px solid #f3f4f6;
}
.el-table--striped .el-table__body tr.el-table__row--striped td {
  background: #fafafa;
}
.el-table__row:hover td {
  background: #f9fafb;
}
.el-table {
  --el-table-border-color: #e5e7eb;
  --el-table-row-hover-bg-color: #f9fafb;
  --el-table-header-bg-color: #f9fafb;
}
```

---

## 7. 分页组件 (`el-pagination`)

```css
.el-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.el-pagination .el-pager .number {
  border-radius: 6px;
  font-size: 13px;
}
.el-pagination .el-pager .number.is-active {
  background: #dc3545;
  color: #fff;
}
.el-pagination .btn-next,
.el-pagination .btn-prev {
  border-radius: 6px;
}
```

---

## 8. 对话框 (`el-dialog`)

```css
.el-dialog {
  border-radius: 16px;
  border: none;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.12);
}
.el-dialog__header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #f3f4f6;
}
.el-dialog__title {
  font-size: 16px;
  font-weight: 700;
  color: #111827;
}
.el-dialog__body {
  padding: 20px 24px;
}
.el-dialog__footer {
  padding: 16px 24px 20px;
  border-top: 1px solid #f3f4f6;
}
```

---

## 9. 颜色系统

### 9.1 品牌色（珊瑚红）

```css
--brand: #dc3545;
--brand-hover: #bb2d3b;
--brand-light: rgba(220, 53, 69, 0.08);
```

### 9.2 文字色

```css
--text-primary: #111827;   /* 主文字 */
--text-secondary: #374151; /* 次要文字 */
--text-tertiary: #6b7280;  /* 标签/说明 */
--text-quaternary: #9ca3af;/* 占位/禁用 */
```

### 9.3 背景色

```css
--bg-base: #f3f4f6;      /* 主背景 */
--bg-sidebar: #fafafa;   /* 侧栏 */
--bg-card: #ffffff;      /* 卡片 */
--bg-hover: #f9fafb;     /* 悬停 */
--bg-input: #fafafa;     /* 输入框 */
```

### 9.4 边框色

```css
--border-default: #e5e7eb;
--border-light: #f3f4f6;
--border-focus: #dc3545;
```

### 9.5 状态色

```css
--status-success: #16a34a;  /* 在线/正常 */
--status-success-bg: #dcfce7;
--status-warning: #ea580c;  /* 警告/待初始化 */
--status-warning-bg: #fef3c7;
--status-danger: #dc2626;   /* 异常/错误 */
--status-danger-bg: #fee2e2;
--status-info: #6b7280;     /* 离线/信息 */
--status-info-bg: #f3f4f6;
```

---

## 10. 圆角系统

```css
--radius-sm: 6px;   /* Tag, 小按钮 */
--radius-md: 8px;   /* 按钮, 输入框 */
--radius-lg: 12px;  /* 卡片 */
--radius-xl: 16px;  /* 对话框 */
--radius-pill: 20px;/* 搜索框 */
--radius-full: 9999px; /* 头像 */
```

---

## 11. 阴影系统

```css
/* 卡片：默认无阴影，hover 时极淡 */
.el-card { box-shadow: none; }
.el-card:hover { box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06); }

/* 对话框：重阴影 */
--shadow-dialog: 0 20px 60px rgba(0, 0, 0, 0.12);

/* 下拉菜单：轻阴影 */
--shadow-dropdown: 0 4px 12px rgba(0, 0, 0, 0.08);

/* 按钮/输入框：无阴影，focus 时用 outline */
.el-input__wrapper.is-focus {
  box-shadow: 0 0 0 2px rgba(220, 53, 69, 0.1);
}
```

---

## 12. 字体系统

```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

--text-xs: 11px;   /* 分组标题 */
--text-sm: 12px;   /* 标签/辅助文字/按钮 */
--text-base: 13px; /* 正文/表格 */
--text-lg: 14px;   /* 卡片标题 */
--text-xl: 16px;   /* 对话框标题 */
--text-2xl: 22px;  /* 页面标题/状态数字 */
--text-3xl: 28px;  /* 指标大数字 */
```

---

## 13. 间距系统

```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
```

卡片内容：`padding: 20px`
卡片间距：`margin-bottom: 16px`
网格间距：`gap: 16px`
页面内边距：`padding: 24px`

---

## 14. 页面模板

### 14.1 Dashboard 概览页

```
[页面标题 + 描述]
──────┬──────┬──────┬──────┐
│ 指标1 │ 指标2 │ 指标3 │ 指标4 │  ← metrics-grid (4 列)
└────────────┴──────┴──────
[连接配置卡片]（WebSocket URL + 令牌 + 语言等，大卡片）
[快照卡片]（状态 + 运行时间 + 间隔 + 最近刷新，4 格内嵌）
[最近会话表格]（可选）
```

### 14.2 列表页（如机器列表）

```
[页面标题 + 描述]
[筛选卡片]（关键词输入 + 状态选择 + 部门输入 + 搜索/重置按钮 + 新增按钮）
[数据表格卡片]（el-table + 分页）
```

### 14.3 详情/配置页（如配置页面）

```
[页面标题 + 描述]
┌─────────────┬─────────────┬─────────────
│ 卡片A       │ 卡片B       │ 卡片C       │  ← 3 列网格
├──────────────────────────┴─────────────
│ 大卡片D（跨全宽）                          │
├─────────────┬─────────────┬─────────────┤
│ 卡片E       │ 卡片F       │ 卡片G       │
└─────────────┴─────────────┴─────────────┘
```

配置类卡片用 key-value 行：

```vue
<el-card>
  <template #header>
    <div class="card-header">
      <span>Model & Thinking</span>
      <el-button link type="primary" size="small">Configure →</el-button>
    </div>
  </template>
  <div class="card-row">
    <span class="card-row-label">Model</span>
    <el-select v-model="model" size="small" />
  </div>
  <div class="card-row">
    <span class="card-row-label">Thinking</span>
    <el-radio-group v-model="thinking" size="small">
      <el-radio-button label="Off">Off</el-radio-button>
      <el-radio-button label="Low">Low</el-radio-button>
      <el-radio-button label="Medium">Medium</el-radio-button>
    </el-radio-group>
  </div>
</el-card>
```

---

## 15. 响应式断点

```css
/* >= 1400px: 4 列网格 */
/* >= 1024px: 3 列网格 */
/* >= 768px:  2 列网格 */
/* < 768px:   1 列网格 */
```

---

## 16. 迁移指南

### 16.1 Element Plus 需要覆盖的变量

在 `main.js` 或 `App.vue` 中全局覆盖：

```css
:root {
  --el-color-primary: #dc3545;
  --el-color-primary-light-3: #e57373;
  --el-color-primary-light-5: #ef9a9a;
  --el-color-primary-light-7: #f8bbd0;
  --el-color-primary-light-8: #fce4ec;
  --el-color-primary-light-9: #ffebee;
  --el-color-primary-dark-2: #bb2d3b;

  --el-border-radius-base: 8px;
  --el-border-radius-small: 6px;
  --el-border-radius-round: 20px;
}
```

### 16.2 全局样式入口

建议新增 `frontend/src/assets/style.css` 作为全局样式覆盖入口：

```css
/* 全局样式：在 main.js 中 import */
@import './style/reset.css';      /* 重置 Element Plus 默认风格 */
@import './style/layout.css';     /* 布局：侧栏、顶栏、内容区 */
@import './style/components.css'; /* 组件覆盖：卡片、表格、按钮、表单 */
@import './style/utilities.css';  /* 工具类：间距、圆角、文字 */
```

### 16.3 逐步迁移优先级

1. **全局变量**：先覆盖 Element Plus CSS 变量（颜色、圆角）
2. **布局框架**：改造侧栏 + 顶栏 + 内容区结构
3. **Dashboard**：第一个完整改造的页面，建立模板
4. **列表页**：机器列表、任务列表等，改造表格和筛选
5. **详情页**：配置页、机器详情页，改造卡片式布局
6. **对话框/弹窗**：统一样式
7. **其余页面**：逐个适配

---

## 17. 禁止使用的样式

以下 Element Plus 默认风格**不应保留**：

- ❌ 蓝色主题色（`--el-color-primary` 默认蓝色）
- ❌ 重阴影卡片（`box-shadow: 0 2px 12px rgba(0,0,0,0.1)`）
- ❌ 渐变图标背景
- ❌ 表格斑马纹默认色
- ❌ 按钮圆角默认 4px（应改为 8px）
- ❌ 表单 label 右对齐（应改为左对齐或顶对齐）
- ❌ 弹窗圆角 4px（应改为 16px）
- ❌ 分页组件默认蓝色高亮

---

## 18. 推荐使用的样式

- ✅ 珊瑚红 `#dc3545` 作为唯一品牌色
- ✅ 白色卡片 + 极细边框 `#e5e7eb`
- ✅ 大号粗体数字（指标卡片）
- ✅ 文字 + `→` 操作链接
- ✅ 状态用彩色文字（不依赖 tag）
- ✅ 网格布局（`grid` + `gap`）
- ✅ 扁平、轻量、无多余装饰
