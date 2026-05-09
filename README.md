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
- **Agent**: Python (可打包为 exe)
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
# 复制并编辑配置文件
copy config.yaml.example "C:\ProgramData\OpenClawCenterAgent\config.yaml"
# 运行
python -m agent
```

## 默认账号

- 用户名: `admin`
- 密码: `admin123`

## 功能模块

- 机器资产管理
- 用户职责与场景管理
- 提示词模板管理
- 企业技能库管理
- 配置分发与版本管理
- Coding Plan 与模型费用管理
- 日志监控与巡检
- Windows Agent 客户端

## Agent 打包

```bash
cd agent
pip install pyinstaller
python build.py
```

生成的 exe 在 `agent/dist/` 目录下。
