FROM mineru:base-3.1.2

USER root

WORKDIR /opt

LABEL maintainer="github.com/yangjiacheng1996"

SHELL ["/bin/bash", "-c"]

# 启动命令
ENTRYPOINT ["/opt/entrypoint.sh"]

CMD ["--port", "30000"]