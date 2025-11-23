# backend/Dockerfile

# 1. 使用官方 Python 3.10 镜像
FROM python:3.10-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 防止 Python 生成 .pyc 文件，并让日志直接输出
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. 安装系统依赖 (编译某些库可能需要)
RUN apt-get update && apt-get install -y netcat-openbsd gcc && rm -rf /var/lib/apt/lists/*

# 5. 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. 复制项目代码
COPY . .

# 7. 收集静态文件 (让 Whitenoise 可以服务它们)
# 注意：这里需要一个临时的 SECRET_KEY 来运行 collectstatic，不会真正用于生产
RUN SECRET_KEY=build-time-key python manage.py collectstatic --noinput

# 8. 暴露端口 (Daphne 默认 8000)
EXPOSE 8000

# 9. 启动命令 (使用 Daphne 启动 ASGI 应用)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "core.asgi:application"]