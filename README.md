# 去字幕/去水印工具

智能检测 + 手动框选，轻松去除视频水印和字幕。

## 功能特性

- **框选模式**：用户手动框选要去除的区域
- **智能检测**：自动检测水印/字幕位置（基于OpenCV边缘检测和形态学处理）
- **FFmpeg处理**：高效的服务器端视频处理
- **进度显示**：实时显示处理进度
- **直接下载**：处理完成后可直接下载

## 技术栈

- **前端**：Vue 3 + Canvas 框选
- **后端**：Flask + Flask-CORS
- **视频处理**：FFmpeg + OpenCV
- **部署**：Render (后端) + Vercel (前端)

## 项目结构

```
watermark-remover/
├── backend/
│   ├── app.py                  # Flask API
│   └── watermark_remover.py    # 核心处理逻辑
├── frontend/
│   └── index.html              # 单页前端
├── requirements.txt            # Python 依赖
├── Procfile                    # Render 部署配置
└── render.yaml                 # Render 配置
```

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/upload` | POST | 上传视频 |
| `/detect` | POST | 智能检测水印/字幕 |
| `/remove` | POST | 去除水印/字幕 |
| `/download/<task_id>` | GET | 下载处理后的视频 |
| `/status/<task_id>` | GET | 获取任务状态 |

## 本地运行

### 后端

```bash
cd backend
pip install -r ../requirements.txt
python app.py
```

### 前端

直接用浏览器打开 `frontend/index.html` 即可。

## 部署到 Render

### 方式一：自动部署（推荐）

1. 确保代码已推送到 GitHub
2. 访问 [Render Dashboard](https://dashboard.render.com)
3. 点击 "New +" → "Web Service"
4. 连接你的 GitHub 仓库
5. 配置设置：
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn backend.app:app --bind 0.0.0.0:$PORT`
6. 点击 "Create Web Service"
7. 等待部署完成，获取 API URL

### 方式二：使用 CLI

```bash
# 安装 Render CLI
npm install -g @render/cli

# 登录
render login

# 部署
render deploy
```

## 部署前端到 Vercel

1. 更新 `frontend/index.html` 中的 `API_BASE` 为你的 Render API 地址
2. 进入 frontend 目录
3. 使用 Vercel CLI 或 GitHub 连接部署

```bash
cd frontend
vercel --prod
```

## 使用说明

1. **上传视频**：点击上传区域或拖拽视频文件
2. **框选区域**：在视频上拖动鼠标框选要去除的区域
3. **智能检测**：点击"自动检测水印/字幕"使用AI检测
4. **处理视频**：点击"开始去除水印"处理视频
5. **下载结果**：处理完成后点击"下载处理后的视频"

## 工作原理

### 智能检测算法

1. **边缘检测**：使用 Canny 算子检测字幕边缘
2. **形态学操作**：闭操作连接相邻文字区域
3. **长宽比筛选**：过滤出横向长条形区域（字幕特征）
4. **区域合并**：合并重叠区域得到最终结果

### 去除算法

使用 FFmpeg delogo 滤镜，通过模糊和覆盖的方式去除水印区域。

## License

MIT
