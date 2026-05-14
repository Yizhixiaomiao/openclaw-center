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

#### Agent 安装（两种方式）

**方式一：远程下载（推荐）**：在目标机器上以管理员身份运行 PowerShell：

```powershell
Invoke-WebRequest -Uri "http://<中心端IP>:8000/api/agent/download" -OutFile "OpenClawCenterAgent.exe"; .\OpenClawCenterAgent.exe
```

Agent 会自动下载、运行、注册为 Windows 计划任务（开机自启）。前提是管理员已在「机器管理」页面上传了 Agent 程序。

**方式二：本地运行**：

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

- 机器资产管理（在线状态、资源监控、配置管理、远程访问链接、删除机器）
- 用户管理（CRUD、删除用户、职责画像）
- 业务场景管理（CRUD、删除场景）
- 提示词模板管理（AI辅助生成、版本控制、一键发布、删除模板）
- 企业技能库管理（审核发布、文件浏览、分发部署、删除技能、移除机器技能）
- 部署任务管理（创建、查看详情、删除任务）
- AI配置管理（配置AI大模型URL/APIKey、测试连接、激活切换）
- 日志监控与巡检（概览、告警、分页日志）
- Agent 远程下载与自动升级
- 配置分发与版本管理（提示词/技能/配置/模型配置）

## Agent 特性

- **远程下载安装**: 管理员上传 Agent 程序后，目标机器可通过 PowerShell 一行命令下载运行
- **自动升级**: Agent 心跳时检测新版本，自动下载升级
- **开机自启**: 首次运行自动注册为 Windows 计划任务，无需手动配置
- **自动初始化**: 首次运行自动创建配置文件，提示输入中心端地址
- **自动注册**: 基于主机名自动生成机器码（格式 `OC-HOSTNAME-XXXX`），无需手动创建
- **远程配置管理**: 支持从控制台远程编辑 OpenClaw 配置和 Agent 配置并同步到目标机器
- **技能全量上报**: 自动打包技能目录（含 SKILL.md frontmatter 解析），支持文件树浏览和内容查看
- **后台任务执行**: 周期性心跳、资源上报、配置同步、任务拉取与执行
- **即时同步**: 支持从控制台下发同步指令，Agent 立即上报配置和技能

## Agent 打包

```bash
cd agent
pip install pyinstaller
python build.py
```

生成的 exe 在 `agent/dist/` 目录下。打包后到「机器管理」页面点击「上传新版本」上传到中心端。
