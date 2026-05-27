# PyTorch镜像构建
Pytorch容器镜像是一个高复用的运行环境，AI软件开发和各种依赖显卡的软件运行环境都是基于Pytorch镜像构建的。
我不相信官方Pytorch镜像，我想自己构建才安心，方便后期修改和定制。构建过程如下：

```
docker pull nvidia/cuda:12.8.1-cudnn-devel-ubuntu24.04

# 基础容器
docker run -itd --name cuda128 --gpus all nvidia/cuda:12.8.1-cudnn-devel-ubuntu24.04

docker exec -it cuda128 bash

# 容器内查看显卡驱动，防止基座异常
nvidia-smi

# apt换源
mv /etc/apt/sources.list.d/cuda.list /etc/apt/sources.list.d/cuda.list.bak
apt update
apt install -y vim
mv /etc/apt/sources.list.d/ubuntu.sources  /etc/apt/sources.list.d/ubuntu.sources.bak
vim /etc/apt/sources.list.d/ubuntu.sources
---------------------------------------------------------
# 清华大学 Ubuntu 24.04 (noble) 镜像源
# 常规软件包更新（使用清华源）
Types: deb
URIs: https://mirrors.tuna.tsinghua.edu.cn/ubuntu
Suites: noble noble-updates noble-backports
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg

# 安全更新（建议保留官方源以确保及时性）
Types: deb
URIs: https://security.ubuntu.com/ubuntu
Suites: noble-security
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg

# 如需源码仓库，可取消以下注释
# Types: deb-src
# URIs: https://mirrors.tuna.tsinghua.edu.cn/ubuntu
# Suites: noble noble-updates noble-backports noble-security
# Components: main restricted universe multiverse
# Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
---------------------------------------------------------------

# 系统包
apt update && apt upgrade -y
apt install -y vim git python3-pip python3-venv curl net-tools wget sudo
apt install -y gcc g++ build-essential cmake ninja-build patchelf
apt install -y libgobject-2.0-0 libpango-1.0-0 libpangoft2-1.0-0 
apt install -y libgl1 libglib2.0-0t64 libsm6 libxext6 libxrender-dev
apt install -y libtbb-dev libssl-dev libcurl4-openssl-dev libaio-dev libgflags-dev zlib1g-dev libfmt-dev libnuma-dev libblis-dev
apt install -y software-properties-common
add-apt-repository -y ppa:ubuntu-toolchain-r/test
apt update
apt install -y --only-upgrade libstdc++6
# 验证libstdc++版本(应包含3.4.32)
strings /usr/lib/x86_64-linux-gnu/libstdc++.so.6 | grep GLIBCXX | tail
apt install -y numactl


# 安装miniconda
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh
source ~/miniconda3/bin/activate    # 进入base环境
conda init --all
conda install python=3.12   # 默认python版本是最新，可以降级base环境的python到指定版本

# 退出容器，重新进入
exit
docker exec -it cuda128 bash

# 虚拟环境
mkdir ~/.pip
vim ~/.pip/pip.conf
---------------------------------------
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
--------------------------------------

# 直接将包安装到base环境，不要单独创建虚拟环境，学习vllm的做法
# conda create -n pytorch python=3.13
# conda activate pytorch

# conda环境配置
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
conda update -n base -c defaults conda
conda install -y -c conda-forge libstdcxx-ng gcc_impl_linux-64
conda install -y -c nvidia/label/cuda-11.8.0 cuda-runtime  # cuda11.8的动态库

# 安装uv
pip install -U pip setuptools wheel
pip install uv

# 安装cuda 12.8.1对应版本的pytorch2.8.0
pip install torch==2.8.0+cu128 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

pip install packaging ninja cpufeature numpy openai

# 验证 torch 版本
python -c "import torch; print(torch.__version__)"
# 验证 torchvision 版本
python -c "import torchvision; print(torchvision.__version__)"

exit

```

# 镜像制作

```
docker commit cuda128  pytorch:2.8.0-cuda12.8.1-cp312-ubuntu24.04

```

# 测试
```
docker rm -f cuda128
docker run -itd --name cuda128 --gpus all pytorch:2.8.0-cuda12.8.1-cp312-ubuntu24.04
docker exec -it cuda128 bash
python -c "import torch; print(torch.__version__)"
python -c "import torchvision; print(torchvision.__version__)"
exit
docker rm -f cuda128
```

将镜像上传到阿里云

```
# 加标签
docker tag pytorch:2.8.0-cuda12.8.1-cp312-ubuntu24.04 registry.cn-shanghai.aliyuncs.com/yangjiacheng1996/pytorch:2.8.0-cuda12.8.1-cp312-ubuntu24.04

# 上传镜像
docker push registry.cn-shanghai.aliyuncs.com/yangjiacheng1996/pytorch:2.8.0-cuda12.8.1-cp312-ubuntu24.04
```

# 保存为tar包
```
docker save -o pytorch__2.8.0-cuda12.8.1-cp312-ubuntu24.04.tar pytorch:2.8.0-cuda12.8.1-cp312-ubuntu24.04

```