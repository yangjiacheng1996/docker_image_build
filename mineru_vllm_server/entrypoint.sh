#!/bin/bash

# ===========================================
# NVIDIA GPU 全局变量定义
# ===========================================
# 获取总显存大小（单位：MiB）
NVIDIA_TOTAL_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits)
TOTAL_MEMORY=$(echo "$NVIDIA_TOTAL_MEMORY" | awk '{gsub(/^[ \t]+/, ""); print int($1)}')

# 获取剩余显存大小（单位：MiB）
NVIDIA_FREE_MEMORY=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits)
FREE_MEMORY=$(echo "$NVIDIA_FREE_MEMORY" | awk '{gsub(/^[ \t]+/, ""); print int($1)}')

# 计算已使用显存大小（单位：MiB）
USED_MEMORY=$((TOTAL_MEMORY - FREE_MEMORY))

# ===========================================
# 显存检查和计算逻辑
# ===========================================

# 检查是否存在 GPU_MEMORY_UTILIZATION 环境变量
if [ -n "$GPU_MEMORY_UTILIZATION" ]; then
    gpu_memory_utilization="$GPU_MEMORY_UTILIZATION"
    echo "检测到环境变量 GPU_MEMORY_UTILIZATION，使用自定义值: ${gpu_memory_utilization}"
else
    echo "GPU总显存: ${TOTAL_MEMORY} MiB"
    echo "GPU剩余显存: ${FREE_MEMORY} MiB"
    echo "GPU已使用显存: ${USED_MEMORY} MiB"

    # 判断逻辑
    if [ "$FREE_MEMORY" -lt 4096 ]; then
        echo "错误: 剩余显存不足4GB，无法启动minerU"
        echo "当前剩余显存: ${FREE_MEMORY} MiB, 要求至少: 4096 MiB"
        sleep 10
        exit 1
    elif [ "$FREE_MEMORY" -ge 4096 ] && [ "$FREE_MEMORY" -le 12288 ]; then
        # 剩余显存在4GB到12GB之间，计算显存使用比例：使用剩余显存的90%
        gpu_memory_utilization=$(awk "BEGIN {printf \"%.2f\", (${FREE_MEMORY} * 0.9) / ${TOTAL_MEMORY}}")
        echo "剩余显存在4GB-12GB范围内，使用剩余显存90%计算显存比例: ${gpu_memory_utilization}"
    else
        # 剩余显存大于12GB，固定预留12000MB，计算显存使用比例
        # 预留12000MB是为了防止显存使用波动
        gpu_memory_utilization=$(awk "BEGIN {printf \"%.2f\", 12000/${TOTAL_MEMORY}}")
        echo "剩余显存大于12GB，使用12000/${TOTAL_MEMORY}计算显存比例: ${gpu_memory_utilization}"
    fi
fi

# 启动mineru-vllm-server，传递所有参数并设置gpu-memory-utilization
exec /root/miniconda3/bin/mineru-vllm-server --gpu-memory-utilization "${gpu_memory_utilization}" "$@"