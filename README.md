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


# mineru:vllm-server
## mineru:vllm-server-3.1.2
拉取镜像:
```
docker pull registry.cn-shanghai.aliyuncs.com/yangjiacheng1996/mineru:vllm-server-3.1.2
```
构建过程:
```
mineru_vllm_server/mineru_vllm_server_v3.1.2手动构建指南.md
```
容器启动：
```
docker run -d --name mineru-vllm-server --restart always --gpus 0 -p 30000:30000 mineru:vllm-server-3.1.2
```
使用方法：
```
mineru -p /path/to/your.pdf  -o /path/to/output/dir  -b vlm-http-client -u http://172.27.213.31:30000 -m ocr
```
