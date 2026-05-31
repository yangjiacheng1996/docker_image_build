FROM whisper:base

WORKDIR /opt/

EXPOSE 8000

USER root

LABEL maintainer="github.com/yangjiacheng1996"

COPY  src/  /opt/src/

# 安装依赖
RUN /root/miniconda3/bin/pip install -r /opt/src/requirements.txt

# 启动
SHELL ["/bin/bash", "-c"]
ENTRYPOINT ["/root/miniconda3/bin/python"]
CMD ["/opt/src/whisper_server.py"]