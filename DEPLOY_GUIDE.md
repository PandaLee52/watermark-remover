# Watermark Remover - 部署指南

## 方案一：手动部署到 Render（推荐）

### 步骤 1: 访问 Render 并登录
1. 打开浏览器访问 https://dashboard.render.com
2. 点击 "Sign in with GitHub" 完成登录

### 步骤 2: 创建 Web Service
1. 点击右上角 **"New +"** 按钮
2. 选择 **"Web Service"**

### 步骤 3: 连接 GitHub 仓库
1. 在 "Connect a repository" 页面
2. 点击 "Configure account" 连接 GitHub（如果未连接）
3. 在仓库列表中找到 **"watermark-remover"**
4. 点击该仓库

### 步骤 4: 配置部署
在配置页面填写以下信息：

| 配置项 | 值 |
|--------|-----|
| **Name** | `watermark-remover-api` |
| **Region** | Singapore |
| **Branch** | master |
| **Runtime** | Python 3.11 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn backend.app:app --bind 0.0.0.0:$PORT` |
| **Plan** | Free |

### 步骤 5: 创建并等待
1. 点击 **"Create Web Service"**
2. 等待构建完成（大约 2-3 分钟）
3. 部署成功后，记录 API URL（如：`https://watermark-remover-api.onrender.com`）

---

## 方案二：使用 Render CLI

```bash
# 安装 Render CLI
npm install -g @render/cli

# 登录
render login

# 部署
cd watermark-remover
render deploy
```

---

## 方案三：本地运行

### 后端
```bash
cd watermark-remover/backend
pip install -r ../requirements.txt
python app.py
```

### 前端
直接用浏览器打开 `frontend/index.html`

---

## 验证部署

部署完成后，访问 API 地址测试：

```bash
curl https://watermark-remover-api.onrender.com/health
```

预期返回：
```json
{"status": "healthy", "service": "watermark-remover", "version": "1.0.0"}
```

---

## 更新前端 API 地址

部署成功后，编辑 `frontend/index.html`，将 `API_BASE` 更新为实际的 API 地址：

```javascript
const API_BASE = 'https://your-actual-api-url.onrender.com';
```

---

## 项目文件结构

```
watermark-remover/
├── backend/
│   ├── app.py                  # Flask API 服务
│   └── watermark_remover.py    # 水印检测和处理核心
├── frontend/
│   └── index.html              # Vue3 单页应用
├── requirements.txt            # Python 依赖
├── Procfile                    # Render 入口
└── README.md                   # 项目说明
```

---

## API 端点说明

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/upload` | POST | 上传视频文件 |
| `/detect` | POST | 智能检测水印位置 |
| `/remove` | POST | 去除水印并处理 |
| `/download/<task_id>` | GET | 下载处理完成的视频 |
| `/status/<task_id>` | GET | 查询任务状态 |
