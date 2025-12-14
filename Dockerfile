# 使用官方 Python 基础镜像
FROM python:3.10-slim

# 安装编译 CityFlow 所需依赖：编译器 + CMake + git
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
 && rm -rf /var/lib/apt/lists/*

# 工作目录
WORKDIR /app

# 先安装 Python 依赖（DeepSeek HTTP 调用用到 requests）
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 从 GitHub 源码编译安装 CityFlow（关键一步）
RUN pip install --no-cache-dir "git+https://github.com/cityflow-project/CityFlow.git"

# 拷贝你的代码和配置
COPY config.json .
COPY controller_deepseek.py .
COPY run.py .

# 默认启动命令：运行仿真
CMD ["python", "run.py"]
