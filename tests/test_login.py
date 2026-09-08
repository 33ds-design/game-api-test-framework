"""
登录系统 API 测试
覆盖: 正常登录 / 空值校验 / 玩家信息查询
"""
import pytest
import requests

BASE = "http://127.0.0.1:18080"


@pytest.mark.smoke
class TestLoginSmoke:
    """登录系统冒烟测试"""

    def test_login_success(self):
        """正常登录"""
        r = requests.post(f"{BASE}/api/login", json={
            "username": "test_user_01",
            "password": "password123"
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert "player_id" in data
        assert "token" in data

    def test_login_empty_username(self):
        """空用户名应返回 400"""
        r = requests.post(f"{BASE}/api/login", json={
            "username": "",
            "password": "123456"
        })
        assert r.status_code == 400

    def test_login_empty_password(self):
        """空密码应返回 400"""
        r = requests.post(f"{BASE}/api/login", json={
            "username": "test_user",
            "password": ""
        })
        assert r.status_code == 400

    def test_login_missing_fields(self):
        """缺少字段应返回 422"""
        r = requests.post(f"{BASE}/api/login", json={"username": "test_user"})
        assert r.status_code == 422


@pytest.mark.smoke
class TestPlayerInfo:
    """玩家信息查询测试"""

    def test_get_player_info(self):
        """查询玩家信息"""
        # 先登录
        r = requests.post(f"{BASE}/api/login", json={
            "username": "info_tester",
            "password": "123456"
        })
        pid = r.json()["data"]["player_id"]

        # 查询信息
        r = requests.get(f"{BASE}/api/player/{pid}")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["level"] == 1
        assert data["hp"] == 100
        assert data["mp"] == 50
        assert data["gold"] == 1000

    def test_get_nonexistent_player(self):
        """查询不存在的玩家应返回 404"""
        r = requests.get(f"{BASE}/api/player/player_nonexistent")
        assert r.status_code == 404
