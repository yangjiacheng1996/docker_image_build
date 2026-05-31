# 写作时间
2026年4月23日，周五。作者杨家成。

# 关键软件版本确定
截至4月20日，使用uv pip install mineru[all]命令安装mineru之后，pip list查看mineru版本是3.1.2，vllm的版本是0.11.2，torch版本2.9.0。
minerU详细的依赖关系可以查看源码https://github.com/opendatalab/MinerU/blob/master/pyproject.toml
以下是核心组件的版本要求
```
vlm = [
    "torch>=2.6.0,<3",
    "transformers>=4.57.3,<5.0.0",
    "accelerate>=1.5.1",
]
vllm = [
    "vllm>=0.10.1.1,<0.12",
]


vllm 0.11.2 requires torch==2.9.0, but you have torch 2.8.0+cu128 which is incompatible.
vllm==0.10.0 依赖python版本 >=3.9,<3.13;
minerU推荐python版本是3.10 、3.11、3.12 ！
```

另一个核心组件是Flash-attn，查找flash-attn的合适版本，网址https://github.com/Dao-AILab/flash-attention/releases 。目前最新版是v2.8.3，需要确保abiFalse，因为容器没有安装c++开发环境。满足abiFalse的目前最新版本是cu12torch2.8，torch2.8.0仅支持cuda12.8，python版本定死为3.12.x !
https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/flash_attn-2.8.3+cu12torch2.8cxx11abiFALSE-cp312-cp312-linux_x86_64.whl
最后，本次vllm可以是0.10.2或者0.11版本。注意0.11版本必须依赖cuda12.9，所以本次只能使用0.10.2
综上所述，汇总一下版本表格
|依赖项|版本号|
|-|-|
|ubuntu容器基座|24.04|
|cuda|12.8.1|
|Python|3.12.x|
|flash-attn|flash_attn-2.8.3+cu12torch2.8cxx11abiFALSE-cp312|
|torch|2.8.0+cu128|
|vllm|0.10.2|

# 启动一个pytorch基础容器
```
docker run -itd --name torch28 --gpus all pytorch:2.8.0-cuda12.8.1-cp312-ubuntu24.04

docker exec -it torch28 bash
```

# MinerU安装
以下操作在torch容器内完成。
```

# 安装flash-attn
wget https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/flash_attn-2.8.3+cu12torch2.8cxx11abiFALSE-cp312-cp312-linux_x86_64.whl

pip install ./flash_attn-2.8.3+cu12torch2.8cxx11abiFALSE-cp312-cp312-linux_x86_64.whl --extra-index-url https://download.pytorch.org/whl/cu128

rm -f ./flash_attn-2.8.3+cu12torch2.8cxx11abiFALSE-cp312-cp312-linux_x86_64.whl

# 安装minerU，需要带上torch版本，否则它会下载最新的2.9而不是2.8
uv pip install mineru[all] torch==2.8.0+cu128 vllm==0.10.2 --system


# 因为官方要求>0.10.1, <12 ，但是vllm==0.11.x需要cuda12.9，这与flash-attn版本要求相违背，所以降低版本到0.10.2
pip list | grep vllm
pip list | grep mineru
pip list | grep torch

# 设置系统环境变量，指向国内HuggingFace镜像站点
export HF_ENDPOINT=https://hf-mirror.com

# 启动 mineru llm server，第一次启动会下载模型
mineru-vllm-server --port 30000

# 默认使用当前剩余显存的50%显存，如果想要降低显存使用，可采用如下命令
mineru-vllm-server --port 30000 --gpu-memory-utilization 0.3

# 测试
docker cp xxx.pdf  torch28:/opt
docker exec -it torch28 bash
mineru -p /opt/xxx.pdf  -o /opt  -b vlm-http-client -u http://127.0.0.1:30000 -m ocr
rm -rf /opt/xxx/  /opt/xxx.pdf

# 编写启动脚本，智能识别显卡剩余显存，最多用12GB显存，适用于A100等大显存显卡。
vim /opt/entrypoint.sh
--------------------------------------------------
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

-----------------------------------------------------------------

# 添加脚本权限
chmod 777 /opt/entrypoint.sh

# 按ctrl+c关闭server。exit退出容器
exit
```


# 构建后端server镜像
```
docker stop torch28

# 将手动构建的容器提交为一个镜像
docker commit  torch28  mineru:base-3.2.1  
docker rm -f torch28 

# 编写一个Dockerfile
vim Dockerfile
-------------------------------------
FROM mineru:base-3.2.1  

USER root

WORKDIR /opt

LABEL maintainer="github.com/yangjiacheng1996"

SHELL ["/bin/bash", "-c"]

# 启动命令
ENTRYPOINT ["/opt/entrypoint.sh"]

CMD ["--port", "30000"]
-------------------------------------

# 构建镜像
docker build . -t mineru:vllm-server-3.2.1
docker rmi -f mineru:base-3.2.1

# 导出
docker save -o mineru__vllm-server-3.2.1.tar mineru:vllm-server-3.2.1

# 导入
docker load -i mineru__vllm-server-3.2.1.tar

# 启动
docker run -d --name mineru-vllm-server --restart always --gpus all -p 30000:30000 mineru:vllm-server-3.2.1

# 查看带外日志
docker logs mineru-vllm-server -f 

docker rm -f mineru-vllm-server
```

# 上传阿里云
```
docker tag mineru:vllm-server-3.2.1  registry.cn-shanghai.aliyuncs.com/yangjiacheng1996/mineru:vllm-server-3.2.1

docker push registry.cn-shanghai.aliyuncs.com/yangjiacheng1996/mineru:vllm-server-3.2.1
```

# 用户使用
```
# 安装uv
pip install uv 或者 
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
irm https://astral.sh/uv/install.ps1 | iex       # Windows (PowerShell)

# 安装minerU
uv pip install mineru

# 进行pdf转换
mineru -p /path/to/your.pdf  -o /path/to/output/dir  -b vlm-http-client -u http://127.0.0.1:30000 -m ocr
````



