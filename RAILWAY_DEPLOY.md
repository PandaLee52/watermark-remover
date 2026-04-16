# Railway 部署指南

## 快速部署（推荐）

### 步骤 1: 安装 Railway CLI
```bash
npm install -g @railway/cli
```

### 步骤 2: 登录
```bash
railway login
```

### 步骤 3: 部署
```bash
cd watermark-remover
railway init
railway up
```

### 步骤 4: 配置环境变量
在 Railway 控制台设置：
- `PORT`: 5000

### 步骤 5: 获取 URL
部署完成后，Railway 会提供公共 URL。

---

## Docker 部署

如果你有 Docker 环境，可以直接运行：

```bash
cd watermark-remover
docker build -t watermark-remover .
docker run -p 5000:5000 watermark-remover
```

---

## 使用已有的 Render 服务

如果你有现有的 Render 服务，可以将代码部署到现有服务上。

---

## 部署后配置前端

1. 获取后端 API 的公共 URL
2. 编辑 `frontend/index.html`，更新 `API_BASE`：
```javascript
const API_BASE = 'https://your-api-url.railway.app';
```
3. 将前端部署到 Vercel、Netlify 或任何静态托管服务

---

## 验证部署

```bash
curl https://your-api-url.railway.app/health
```

预期返回：
```json
{"status": "healthy", "service": "watermark-remover", "version": "1.0.0"}
```
