FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖，包括一些PDF处理和OCR所需的包
RUN apt-get update && apt-get install -y \
    build-essential \
    libpoppler-cpp-dev \
    pkg-config \
    python3-dev \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    ghostscript \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 确保安装gunicorn
RUN pip install --no-cache-dir gunicorn uvicorn

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动应用，使用gunicorn和uvicorn worker，设置3个worker进程提高并发能力
CMD ["gunicorn", "app:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "1", "--timeout", "600", "--bind", "0.0.0.0:8000"]
