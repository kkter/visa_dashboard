FROM python:3.9-slim

WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有项目文件到工作目录
# 这会包括 run_pipeline.sh
COPY . .

# 确保自动化脚本有执行权限
RUN chmod +x /app/run_pipeline.sh

# Gunicorn 启动命令已在 docker-compose.yml 中定义