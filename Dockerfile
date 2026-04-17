FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（ffmpeg 用于视频处理）
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --upgrade pip setuptools wheel && pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY backend/ ./backend/
COPY main.py .

# 创建上传目录
RUN mkdir -p /tmp/watermark_uploads /tmp/watermark_outputs

# 暴露端口
EXPOSE 5000

# 环境变量
ENV PORT=5000

# 启动命令
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:5000"]
