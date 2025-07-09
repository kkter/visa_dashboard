#!/bin/bash

# 设置项目在容器内的绝对路径
APP_DIR="/app"
# 标记文件也存放在持久化的 data 目录中
FLAG_DIR="${APP_DIR}/data"

# 获取当前年份和周数，作为本周任务的唯一标识
CURRENT_WEEK=$(date +%Y-%U)
FLAG_FILE="${FLAG_DIR}/run_success_week_${CURRENT_WEEK}.flag"

# 1. 检查本周任务是否已经成功完成
if [ -f "$FLAG_FILE" ]; then
    echo "[$(date)] 本周任务 (Week ${CURRENT_WEEK}) 已完成，跳过。"
    exit 0
fi

echo "[$(date)] 开始为 Week ${CURRENT_WEEK} 执行更新任务..."
cd ${APP_DIR}

# 2. 运行下载脚本
# 假设 download_visas.py 在成功下载后返回 exit code 0
python3 download_visas.py
DOWNLOAD_STATUS=$?

# 3. 检查下载结果
if [ ${DOWNLOAD_STATUS} -eq 0 ]; then
    echo "[$(date)] 数据下载成功。开始执行解析..."
    
    # 4. 如果下载成功，运行解析脚本
    python3 parse_pdfs.py
    PARSE_STATUS=$?

    if [ ${PARSE_STATUS} -eq 0 ]; then
        echo "[$(date)] 数据解析成功。"
        # 5. 创建成功标记文件，并记录完成时间
        date > "$FLAG_FILE"
        echo "[$(date)] 任务流程全部成功，已创建标记文件: ${FLAG_FILE}"
    else
        echo "[$(date)] 错误：数据解析失败！"
        exit 1
    fi
else
    echo "[$(date)] 未发现新数据，本次不执行解析。"
fi

echo "[$(date)] 任务执行完毕。"