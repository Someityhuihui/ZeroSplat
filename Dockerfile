# 强制使用 Python 3.11 作为基础环境！
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 把依赖文件复制进去
COPY requirements.txt /app/requirements.txt

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 把你的代码复制进去
COPY . /app

# 启动命令（确保监听 7860 端口）
CMD ["python", "app.py"]