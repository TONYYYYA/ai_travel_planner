FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（包括gcc用于编译pyaudio，以及网络工具确保API访问）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    portaudio19-dev \
    alsa-utils \
    pulseaudio \
    pulseaudio-utils \
    libpulse0 \
    curl \
    wget \
    dnsutils \
    iputils-ping \
    # 添加必要的音频库
    libasound2-dev \
    libportaudio2 \
    # 添加其他工具
    sudo \
    && rm -rf /var/lib/apt/lists/*

RUN apt update && apt install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# 创建音频组并设置权限（使用-f参数避免组已存在的错误）
RUN groupadd -r -f audio && \
    groupadd -r -f pulse && \
    groupadd -r -f pulse-access && \
    # 创建通用的PulseAudio运行时目录
    mkdir -p /run/pulse && \
    chmod 775 /run/pulse && \
    # 创建用户目录模板
    mkdir -p /app/temp \
    chmod 777 /app/temp

# 设置ALSA和PulseAudio配置环境变量
ENV ALSA_CONFIG_PATH=/usr/share/alsa/alsa.conf
ENV ALSA_CARD=default
ENV PULSE_SERVER=unix:/run/user/${USER_ID:-1000}/pulse/native
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/pulseaudio:/usr/lib/x86_64-linux-gnu/alsa-lib
ENV PULSE_COOKIE=/tmp/pulse.cookie
ENV PULSE_DATA=/tmp/pulse
ENV PULSE_RUNTIME_PATH=/run/user/${USER_ID:-1000}/pulse

# 创建PulseAudio配置目录
RUN mkdir -p /etc/pulse && \
    echo 'default-server = unix:/run/user/${USER_ID:-1000}/pulse/native' > /etc/pulse/client.conf && \
    echo 'autospawn = no' >> /etc/pulse/client.conf && \
    echo 'daemon-binary = /bin/true' >> /etc/pulse/client.conf && \
    echo 'enable-shm = false' >> /etc/pulse/client.conf

# 设置地图API访问优化环境变量
ENV HTTP_PROXY=""
ENV HTTPS_PROXY=""
ENV NO_PROXY="localhost,127.0.0.1"

# 注释掉直接修改resolv.conf的部分（现代Docker中此文件通常是只读的）
# 如需配置DNS，可以在docker run命令中使用--dns参数
# 或者让Docker使用宿主机的DNS配置

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install -r backend/requirements.txt

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "backend/app.py"]