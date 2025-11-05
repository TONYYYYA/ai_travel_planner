FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（包括gcc用于编译pyaudio）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install -r backend/requirements.txt

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "backend/app.py"]