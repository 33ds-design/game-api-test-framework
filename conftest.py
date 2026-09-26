"""
Pytest 配置 — 启动/关闭 Mock Server
"""
import os
import subprocess
import sys
import time

import pytest
import requests

from server_config import BASE_URL

REUSE_EXISTING = os.environ.get("MOCK_REUSE_EXISTING") == "1"


def _is_server_up() -> bool:
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=1)
        return r.status_code == 200
    except requests.RequestException:
        return False


@pytest.fixture(scope="session", autouse=True)
def mock_server():
    """Session 级 fixture: 独占启动 Mock Server，测试结束后回收。

    端口已被占用时不再静默复用——复用会让测试跑在旧代码/脏状态上，产出假绿。
    确需复用（本地手动起服务调试）时显式设置 MOCK_REUSE_EXISTING=1。
    """
    if _is_server_up():
        if not REUSE_EXISTING:
            pytest.exit(
                f"{BASE_URL} 已有服务在响应，但本测试要求独占该端口。\n"
                f"  · 可能原因：上次运行的 Mock Server 残留进程，或端口被其它程序占用\n"
                f"  · 处理方式：结束占用进程后重跑；或设置 MOCK_PORT=<空闲端口> 换端口\n"
                f"  · 确需复用该服务：显式设置 MOCK_REUSE_EXISTING=1",
                returncode=1,
            )
        print(
            f"\n[WARN] 复用已存在的服务 {BASE_URL}（MOCK_REUSE_EXISTING=1）。\n"
            f"       无法保证其代码版本与当前工作区一致，进程内状态也可能已被污染，\n"
            f"       本次结果不一定代表当前代码。"
        )
        yield
        return

    proc = subprocess.Popen(
        [sys.executable, os.path.join(os.path.dirname(__file__), "mock_server.py")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(30):
        if _is_server_up():
            break
        time.sleep(0.5)
    else:
        proc.terminate()
        proc.wait()
        raise RuntimeError("Mock server 启动失败")

    try:
        yield
    finally:
        proc.terminate()
        proc.wait()
