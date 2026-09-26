FROM python:3.12-slim

WORKDIR /app

# 依赖单独一层：requirements.txt 不变时改代码不会触发重装
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# conftest.py 会用 subprocess 拉起 mock_server.py 并访问 127.0.0.1，
# 容器内回环地址即容器自身，无需额外网络配置。
# 默认只跑功能 / 白盒 / 缺陷用例；压测用 docker run <image> make perf 覆盖。
CMD ["python", "-m", "pytest", "tests/", "--ignore=tests/test_performance.py", "-v"]
