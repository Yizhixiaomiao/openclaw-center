# OpenClaw Center - 企业统一管理平台

面向独立 Windows 虚拟机模式的中心控制台、Agent 客户端、技能与提示词统一分发系统。

## 项目结构

```
openclaw-center/
├── backend/          # FastAPI 后端服务
├── frontend/         # Vue 3 + Element Plus 前端
├── agent/            # Windows Agent 客户端
└── docker-compose.yml
```

## 技术栈

- **后端**: FastAPI + Python 3.11+ + SQLAlchemy + MySQL 8
- **前端**: Vue 3 + Element Plus + Vite + Pinia
- **Agent**: Python (可打包为 Windows exe)
- **部署**: Docker Compose

## 快速开始

### 1. 使用 Docker Compose（推荐）

```bash
docker-compose up -d
```

启动后访问：
- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 2. 本地开发

#### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 前端

```bash
cd frontend
npm install
npm run dev
```

#### Agent

```bash
cd agent
pip install -r requirements.txt
python -m agent
```

**首次运行 Agent** 会自动在 `C:\ProgramData\OpenClawCenterAgent\` 创建默认配置文件，并交互式提示输入中心端 URL。机器码自动生成，自动注册到控制中心，无需手动创建机器。

## 默认账号

- 用户名: `admin`
- 密码: `admin123`

## 功能模块

- 机器资产管理（在线状态、资源监控、配置管理）
- 用户职责与场景管理
- 提示词模板管理（版本控制、一键发布）
- 企业技能库管理（审核发布、文件浏览、分发部署）
- 配置分发与版本管理（提示词/技能/配置/模型配置）
- Coding Plan 与模型费用管理
- 日志监控与巡检
- Windows Agent 客户端（自动注册、心跳上报、任务执行）

## Agent 特性

- **自动初始化**: 首次运行自动创建配置文件，提示输入中心端地址
- **自动注册**: 基于主机名自动生成机器码（格式 `OC-HOSTNAME-XXXX`），无需手动创建
- **远程配置管理**: 支持从控制台远程编辑 OpenClaw 配置和 Agent 配置并同步到目标机器
- **技能全量上报**: 自动打包技能目录（含 SKILL.md frontmatter 解析），支持文件树浏览和内容查看
- **后台任务执行**: 周期性心跳、资源上报、配置同步、任务拉取与执行

## Agent 打包

```bash
cd agent
pip install pyinstaller
python build.py
```

生成的 exe 在 `agent/dist/` 目录下。
