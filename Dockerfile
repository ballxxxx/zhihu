# 搭子参谋 FinalMate · CloudBase 云托管镜像
# 要点:python 3.12(onnxruntime 轮子兼容);opencv 换 headless 版(无 GUI 依赖);
# zhihu-cli 下载官方 linux-amd64 二进制(与本地 Windows 版同版本 0.6.3,代码零改动)。
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    ZHIHU_CLI=/usr/local/bin/zhihu-cli

WORKDIR /app

# curl 用于下载 zhihu-cli(debian slim 默认不带)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements-cloud.txt .
RUN pip install -r requirements-cloud.txt && \
    pip uninstall -y opencv-python && \
    pip install opencv-python-headless

# zhihu-cli linux-amd64 0.6.3(sha256 校验)
RUN curl -fsSL -o /tmp/zhihu-cli.tar.gz \
      https://developer-cdn.zhihu.com/zhihu-cli/releases/stable/cli/0.6.3/zhihu-cli-0.6.3-linux-amd64.tar.gz && \
    echo "3c1866334b82a88a2aebd3051b1225dd9b9b9b0d1ec600548706f752212db7d6  /tmp/zhihu-cli.tar.gz" | sha256sum -c - && \
    tar -xzf /tmp/zhihu-cli.tar.gz -C /usr/local/bin && \
    chmod +x /usr/local/bin/zhihu-cli && \
    rm /tmp/zhihu-cli.tar.gz

COPY app ./app
COPY data ./data

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
