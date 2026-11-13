# syntax=docker/dockerfile:1
#
# Spider Bond 容器镜像（多阶段）。
#
# 三个阶段的划分原因：
#   1) 前端必须用 node 构建，运行镜像里不需要 node
#   2) Python 阶段要跑 build.py 准备资源（lab.css、图标 sprite、Pyodide 运行时）
#   3) 运行镜像只保留 server/，不带源码、node_modules 和构建工具
#
# 注意：Pyodide 运行时约 19MB，构建阶段会从 CDN 下载并缓存在层里。
# 想完全离线构建，可以先把 server/dist/pyodide 放好并在 prep 阶段跳过下载。

# ---------------------------------------------------------------- 阶段 1：前端
FROM node:22-alpine AS web
WORKDIR /src/web
COPY web/package.json web/package-lock.json* ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# ---------------------------------------------------------------- 阶段 2：准备产物
FROM python:3.12-slim AS prep
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SPIDERLAB_SKIP_WEB=1
WORKDIR /src
COPY server/ ./server/
COPY build.py prepare_pyodide.py ./
COPY --from=web /src/web/dist ./web/dist
RUN python build.py \
 && rm -f spiderlab.tar.gz

# ---------------------------------------------------------------- 阶段 3：运行
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SPIDERLAB_PORT=8080 \
    SPIDERLAB_DB=/data/spiderlab.db

# 非 root 运行：容器里被打穿时至少不会直接拿到 root
RUN useradd -r -u 10001 -s /usr/sbin/nologin app \
 && mkdir -p /data \
 && chown app:app /data

WORKDIR /app/server
COPY --from=prep --chown=app:app /src/server ./

USER app
EXPOSE 8080
VOLUME ["/data"]

# 用标准库做健康检查，不额外装 curl
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/', timeout=3).status==200 else 1)"

CMD ["python", "app.py"]
