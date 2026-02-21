# Stage 1: Builder (构建依赖)
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制依赖文件
COPY requirements.txt .
COPY requirements_web.txt .

# 安装依赖 (优先使用 PyTorch CPU 版本)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements_web.txt

# Stage 2: Final (运行时环境)
FROM python:3.11-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=src/web/app.py \
    PATH="/opt/venv/bin:$PATH"

# 安装运行时系统依赖 (OpenCV/Open3D 需要)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制项目代码
COPY src/ src/
COPY cli.py .

# 创建必要的目录
RUN mkdir -p uploads results

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "src/web/app.py"]
