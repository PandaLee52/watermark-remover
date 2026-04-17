FROM python:3.11-slim

WORKDIR /app

# 设置 Debian 镜像源（加速下载）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

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
