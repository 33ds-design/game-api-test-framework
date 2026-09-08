"""
Pytest 配置 — 启动/关闭 Mock Server
"""
import pytest
import subprocess
import sys
import time
import requests
import os


def _is_server_up():
    try:
        r = requests.get("http://127.0.0.1:18080/api/health", timeout=1)
        return r.status_code == 200
    except:
        return False


@pytest.fixture(scope="session", autouse=True)
def mock_server():
    """Session 级 fixture: 启动 mock server，测试结束后关闭"""
    if _is_server_up():
        yield
        return

    proc = subprocess.Popen(
        [sys.executable, os.path.join(os.path.dirname(__file__), "mock_server.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    for _ in range(30):
        if _is_server_up():
            break
        time.sleep(0.5)
    else:
        proc.terminate()
        proc.wait()
        raise RuntimeError("Mock server 启动失败")

    yield

    proc.terminate()
    proc.wait()
