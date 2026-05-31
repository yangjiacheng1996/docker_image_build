# 版本规划
根据whisper官方项目README.md中描述：
codebase is expected to be compatible with Python 3.8-3.11 and recent PyTorch versions.

因此我决定，运行whisper的基座包括python3.11， torch2.12.0, cuda13.0.3。为此，我构建了pytorch:2.12.0-cuda13.0.3-py311-ubuntu24.04容器镜像。

# Whisper包安装
启动基础容器
```
docker run -itd --name torch212 --gpus all pytorch:2.12.0-cuda13.0.3-cp311-ubuntu24.04

docker exec -it torch212 bash
```

安装 whisper、rust
```
pip install -U openai-whisper setuptools-rust 
# --extra-index-url https://mirrors.aliyun.com/pypi/simple/

安装其他
pip install fastapi uvicorn pydantic requests 
```

安装ffmpeg
```
apt update && apt install -y ffmpeg
```
# 模型下载
只有在第一次音频、视频转录文字时才会下载模型，所以需要向容器中复制音频文件，并执行转录。
我在目录中放了一个视频expired-mickey-mouse.mp4，关于米老鼠版权到期的。

```
# 宿主机执行
docker cp expired-mickey-mouse.mp4 torch212:/opt

# 容器中执行
cd /opt
whisper /opt/expired-mickey-mouse.mp4  --model turbo  --language Chinese
# 此时开始下载turbo模型，并转录。占用6GB显存。

# 删除转录结果
rm -f /opt/expired-mickey-mouse.*

# whisper路径
which whisper
/root/miniconda3/bin/whisper

# 退出容器
exit
```


# 镜像构建
先停止容器，然后提交成基础镜像
```
docker stop torch212
docker commit torch212 whisper:base
```

宿主机上在本项目src目录所在位置，编写一个Dockerfile ，
```
FROM whisper:base

WORKDIR /opt/

EXPOSE 8000

USER root

LABEL maintainer="github.com/yangjiacheng1996"

COPY  src/  /opt/

# 安装依赖
RUN /root/miniconda3/bin/pip install -r /opt/src/requirements.txt

# 启动
SHELL ["/bin/bash", "-c"]
ENTRYPOINT ["/root/miniconda3/bin/python"]
CMD ["/opt/src/whisper_server.py"]

```
构建
```
docker build . -t whisper:server-v0.0.1
```

# 测试
```
docker run -itd --name whisper-server --gpus all -p 8000:8000 whisper:server-v0.0.1
docker logs whisper-server -f 
python client_cli.py --ip 127.0.0.1 --port 8000 upload  expired-mickey-mouse.mp4
python client_cli.py --ip 127.0.0.1 --port 8000 files
python client_cli.py --ip 127.0.0.1 --port 8000 idle
python client_cli.py --ip 127.0.0.1 --port 8000 result
python client_cli.py --ip 127.0.0.1 --port 8000 download expired-mickey-mouse_mp4
python client_cli.py --ip 127.0.0.1 --port 8000 delete-all
python client_cli.py --ip 127.0.0.1 --port 8000 delete-all-transcriptions
docker rm -f whisper-server
```

# 上传阿里云
```
docker tag whisper:server-v0.0.1 registry.cn-shanghai.aliyuncs.com/yangjiacheng1996/whisper:server-v0.0.1

docker push registry.cn-shanghai.aliyuncs.com/yangjiacheng1996/whisper:server-v0.0.1

```


