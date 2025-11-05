# AI 旅行规划师

## 概述

AI 旅行规划师是一款基于人工智能的旅行辅助工具，旨在帮助用户轻松规划旅行行程、管理旅行费用，并提供智能化的旅行建议。该应用结合了语音识别、AI 行程生成、地图集成和费用管理等功能，为用户打造一站式的旅行规划体验。

## 项目结构

```
├── ai-travel-planner.tar # 项目打包文件
├── ai旅游规划师windows中start.bat可以使用/ # Windows环境完整项目
│   ├── backend/           # 后端 Python Flask 应用
│   │   ├── app.py         # 主应用入口
│   │   ├── config.py      # 配置文件
│   │   ├── llm_service.py # AI 语言模型服务
│   │   ├── map_service.py # 地图服务集成
│   │   ├── speech_service.py # 语音识别服务
│   │   ├── requirements.txt # 项目依赖
│   │   └── resources/     # 资源文件
│   ├── static/            # 静态资源
│   │   ├── css/           # CSS 样式文件
│   │   └── js/            # JavaScript 脚本文件
│   ├── templates/         # HTML 模板文件
│   │   ├── welcome.html   # 欢迎页面
│   │   ├── login.html     # 登录页面
│   │   ├── register.html  # 注册页面
│   │   ├── planner.html   # 行程规划页面
│   │   ├── expenses.html  # 费用管理页面
│   │   ├── guide.html     # 使用指南页面
│   │   └── sync.html      # 同步页面
│   ├── Dockerfile         # Docker 构建文件
│   ├── start.bat          # Windows 启动脚本
│   └── build_docker.bat   # Docker 构建脚本
├── ai旅行规划师 ffmpeg/   # 包含 ffmpeg 的项目版本
│   ├── backend/           # 后端应用（结构同上）
│   ├── static/            # 静态资源（结构同上）
│   ├── templates/         # HTML 模板（结构同上）
│   └── ffmpeg/            # ffmpeg 可执行文件及相关文件
└── README.md              # 项目说明文档
```

## 快速开始

本项目提供了两个主要版本，您可以根据自己的需求选择：

### 1. 包含 ffmpeg 的完整版本

进入 `ai旅行规划师 ffmpeg/` 目录，该版本已包含 ffmpeg 可执行文件，无需额外安装：

1. 确保已安装 Python 3.8 或更高版本
2. 双击运行 `ai旅行规划师 ffmpeg/start.bat`
3. 脚本将自动安装依赖并启动应用
4. 浏览器将自动打开 `http://127.0.0.1:5000`

### 2. Windows 环境标准版本

进入 `ai旅游规划师windows中start.bat可以使用/` 目录：

1. 确保已安装 Python 3.8 或更高版本
2. 双击运行 `ai旅行规划师 ffmpeg/start.bat`
3. 脚本将自动安装依赖并启动应用
4. 浏览器将自动打开 `http://127.0.0.1:5000`

### 3. Docker镜像
1. 下载ai-travel-planner.tar镜像
2.  将tar镜像文件加载到本地的Docker `sudo docker load -i /path/to/ai-travel-planner.tar`
3. `运行命令行docker run -d -p 5000:5000 --name ai-travel-planner-app ai-travel-planner 或者在容器中指定Host Post为5000`

### 4. 手动安装与配置

如果您希望手动配置项目，可以按照以下步骤操作：

1. 确保已安装 Python 3.8 或更高版本
2. 进入任意版本的 backend 目录
3. 安装项目依赖：
   ```
   pip install -r requirements.txt
   ```
4. 运行应用：
   ```
   python app.py
   ```
5. 在浏览器中访问 `http://127.0.0.1:5000`

## 功能特性

### 行程规划
- 支持文本和语音输入旅行需求（目的地、天数、预算、偏好等）
- AI 自动生成详细行程，包括每日安排、景点推荐、餐饮建议等
- 行程可视化展示，包含预算明细、注意事项等信息
- 百度地图集成，在地图上标记行程中的景点位置并显示路线
- 行程保存与加载功能，方便用户管理多个旅行计划

### 费用管理
- 为每个行程记录各项开销，支持多种费用类别（交通、住宿、餐饮等）
- 自动计算总费用，实时展示花费情况
- 预算分析功能，对比实际花费与原始预算
- AI 提供预算使用建议，帮助用户优化支出
- 支持语音输入费用备注信息

### 用户管理
- 用户注册与登录功能，保障数据安全
- 个人行程和费用数据云端存储（通过 Supabase）
- 多设备访问支持

## 技术架构

### 前端
- HTML5/CSS3 构建用户界面
- JavaScript 实现交互逻辑
- 百度地图 API 实现地图展示与标记功能
- 响应式设计，适配不同设备

### 后端
- Python Flask 框架构建 RESTful API
- Supabase 用于数据存储和用户认证
- 集成讯飞语音识别服务处理语音输入
- OpenAI API 用于行程生成和预算分析

## 主要页面

- **欢迎页** (`/`) - 应用入口，提供导航到各功能页面
- **登录页** (`/login`) - 用户登录界面
- **注册页** (`/register`) - 新用户注册界面
- **行程规划页** (`/planner`) - AI 行程生成和管理
- **费用管理页** (`/expenses`) - 旅行费用记录和预算分析
- **使用指南页** (`/guide`) - 应用使用说明

## API 接口概述

### 用户相关
- `POST /api/register` - 用户注册
- `POST /api/login` - 用户登录
- `POST /api/logout` - 用户登出

### 行程相关
- `POST /api/generate-itinerary` - 生成新行程
- `GET /api/itineraries` - 获取用户所有行程
- `POST /api/itineraries` - 保存新行程
- `GET /api/itineraries/<itinerary_id>` - 获取单个行程详情
- `DELETE /api/itineraries/<itinerary_id>` - 删除行程

### 费用相关
- `POST /api/expenses` - 添加费用记录
- `GET /api/expenses/<itinerary_id>` - 获取行程费用记录
- `POST /api/analyze-budget` - 预算分析

### 其他服务
- `POST /api/speech-to-text` - 语音转文字
- `GET /api/location-info` - 获取地理位置信息
- `GET /api/route-plan` - 获取路线规划
- `POST /api/schema/personal-map` - 生成百度地图 URI

## 注意事项

1. 使用前请确保 ffmpeg 已正确安装并添加到环境变量
2. 应用需要网络连接以访问 AI 服务和地图 API
3. 首次使用时可能需要配置 `.env` 文件中的相关服务密钥
4. 语音识别功能依赖讯飞开放平台的 SDK，确保相关配置正确

## 使用流程

### 行程规划
1. 登录后进入行程规划页面
2. 输入目的地、天数、预算等旅行需求
3. 点击"生成行程"按钮，等待 AI 生成详细行程
4. 查看并调整生成的行程内容
5. 保存行程以便后续使用

### 费用管理
1. 在费用管理页面选择一个行程
2. 添加各项旅行开销记录
3. 系统自动汇总并分析费用情况
4. 查看预算使用建议

## 配置要求

### 基本要求
- Python 3.8+
- ffmpeg 4.0+（使用语音功能时需要）
- 浏览器支持：Chrome 90+、Firefox 88+、Safari 14+、Edge 90+
- 网络连接：稳定的互联网连接

### 其他要求
- 使用语音功能需要浏览器授权麦克风访问
- 地图功能需要网络连接
- 部分功能需要用户登录才能使用
- 确保在 config.py 中正确配置 API 密钥和服务地址

## Docker支持

项目提供了Docker支持，可以使用以下方式在容器环境中运行：

### Windows环境Docker使用
1. 确保已安装Docker Desktop
2. 进入任意项目版本目录
3. 运行 `build_docker.bat` 构建Docker镜像
4. 运行 `start_docker.bat` 启动Docker容器

### Ubuntu/Linux环境Docker使用
1. 确保已安装Docker
2. 解压项目打包文件 `ai-travel-planner.tar`
3. 运行 `chmod +x build_docker_ubuntu.sh` 赋予执行权限
4. 执行 `./build_docker_ubuntu.sh` 构建镜像
5. 运行 `./start_docker_ubuntu.sh` 启动容器（支持音频设备）

### Docker注意事项
- 容器默认映射端口5000
- Ubuntu环境中支持音频设备访问（需要PulseAudio服务）
- 建议在运行Docker前关闭防火墙或允许5000端口访问

## 页面说明

- **welcome.html**：应用欢迎页面，提供导航入口
- **login.html**：用户登录页面，用于身份验证
- **register.html**：新用户注册页面，创建账户
- **planner.html**：行程规划主页面，用于输入需求、生成和管理行程
- **expenses.html**：费用管理页面，用于记录和分析旅行开销
- **sync.html**：云端数据同步页面，管理用户数据
- **guide.html**：旅行导航辅助页面，提供位置信息和路线规划
- **录音按钮.html**：语音输入测试页面，用于调试语音识别功能

希望 AI 旅行规划师能为您的旅行带来便利和乐趣！