"""Mock Server 连接参数的唯一来源，可用环境变量覆盖。

    MOCK_HOST   默认 127.0.0.1
    MOCK_PORT   默认 18080

测试、conftest、mock_server 三处都从这里取，避免端口散落在多个文件里。
"""
import os

HOST = os.environ.get("MOCK_HOST", "127.0.0.1")
PORT = int(os.environ.get("MOCK_PORT", "18080"))
BASE_URL = f"http://{HOST}:{PORT}"
