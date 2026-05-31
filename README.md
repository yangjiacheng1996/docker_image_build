# docker_image_build
这个项目用于记录一些docker镜像的构建方法和使用方法。


# pytorch
pytorch容器作为其他cuda生态应用容器镜像的构建基座。
## pytorch:2.8.0-cuda12.8.1-cp312-ubuntu24.04
拉取镜像（pull image）:
```
docker pull registry.cn-shanghai.aliyuncs.com/yangjiacheng1996/pytorch:2.8.0-cuda12.8.1-cp312-ubuntu24.04
```
构建过程:
```
pytorch/pytorch_2.8.0_cuda12.8.1_py312_ubuntu24.04手动构建指南.md
```
## pytorch:2.12.0-cuda13.0.3-cp311-ubuntu24.04
```
docker pull registry.cn-shanghai.aliyuncs.com/yangjiacheng1996/pytorch:2.12.0-cuda13.0.3-cp311-ubuntu24.04
```
构建过程:
```
pytorch/pytorch_2.12.0_cuda13.0.3_py311_ubuntu24.04手动构建指南.md
```


# mineru
## mineru:vllm-server-3.2.1
拉取镜像:
```
docker pull registry.cn-shanghai.aliyuncs.com/yangjiacheng1996/mineru:vllm-server-3.2.1
```
构建过程:
```
mineru_vllm_server/mineru_vllm_server_v3.2.1手动构建指南.md
```
容器启动：
```
docker run -d --name mineru-vllm-server --restart always --gpus 0 -p 30000:30000 mineru:vllm-server-3.2.1
```
使用方法：
```
mineru -p /path/to/your.pdf  -o /path/to/output/dir  -b vlm-http-client -u http://172.27.213.31:30000 -m ocr
```

# whisper
后端容器
## whisper:server-v0.0.1
拉取镜像：
```
docker pull registry.cn-shanghai.aliyuncs.com/yangjiacheng1996/whisper:server-v0.0.1 
```
构建过程：
```
whisper/whisper容器手动构建指南.md
```
容器启动
```
docker run -itd --name whisper-server --gpus all -p 8000:8000 whisper:server-v0.0.1
```
使用方法
```
python client_cli.py --ip <ip> --port <port> upload <file_path> [language]
python client_cli.py --ip <ip> --port <port> files
python client_cli.py --ip <ip> --port <port> delete <filename>
python client_cli.py --ip <ip> --port <port> delete-all
python client_cli.py --ip <ip> --port <port> idle
python client_cli.py --ip <ip> --port <port> transcribe <filename> [language]
python client_cli.py --ip <ip> --port <port> result
python client_cli.py --ip <ip> --port <port> result-file <filename>
python client_cli.py --ip <ip> --port <port> download <filename>
python client_cli.py --ip <ip> --port <port> delete-transcription <transcription_dir>
python client_cli.py --ip <ip> --port <port> delete-all-transcriptions
python client_cli.py --ip <ip> --port <port> cleanup-zips
```

