"""
白盒测试 — 基于代码结构的分支/路径覆盖测试
直接导入 mock_server 模块，测试内部逻辑分支
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient

from mock_server import app, combat_log, inventory, players


@pytest.fixture(autouse=True)
def client():
    """使用 TestClient 直接测试 FastAPI app（无网络开销），每个测试前重置全局状态"""
    players.clear()
    inventory.clear()
    combat_log.clear()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def fresh_player(client):
    """创建一个新玩家"""
    r = client.post("/api/login", json={"username": "whitebox_test", "password": "123456"})
    return r.json()["data"]["player_id"]


class TestLoginBranchCoverage:
    """登录接口分支覆盖"""

    def test_empty_username(self, client):
        """分支: username 为空"""
        r = client.post("/api/login", json={"username": "", "password": "123"})
        assert r.status_code == 400

    def test_empty_password(self, client):
        """分支: password 为空"""
        r = client.post("/api/login", json={"username": "test", "password": ""})
        assert r.status_code == 400

    def test_both_empty(self, client):
        """分支: 两个字段都为空"""
        r = client.post("/api/login", json={"username": "", "password": ""})
        assert r.status_code == 400

    def test_normal_login_creates_player_state(self, client):
        """分支: 正常登录 — 验证内部状态初始化"""
        r = client.post("/api/login", json={"username": "state_check", "password": "abc"})
        pid = r.json()["data"]["player_id"]
        assert pid in players
        assert players[pid]["level"] == 1
        assert players[pid]["hp"] == 100
        assert players[pid]["mp"] == 50
        assert players[pid]["gold"] == 1000
        assert pid in inventory
        assert inventory[pid] == []


class TestCombatBranchCoverage:
    """战斗接口分支覆盖 — 覆盖所有 skill 分支和 crit/non-crit 分支"""

    def test_fireball_non_crit_path(self, client, fresh_player):
        """路径: fireball + 非暴击"""
        r = client.post("/api/combat", json={"player_id": fresh_player, "skill_id": "fireball"})
        data = r.json()["data"]
        assert r.status_code == 200
        assert data["mp_remaining"] == 40

    def test_frostbolt_path(self, client, fresh_player):
        """路径: frostbolt"""
        r = client.post("/api/combat", json={"player_id": fresh_player, "skill_id": "frostbolt"})
        assert r.status_code == 200
        assert r.json()["data"]["mp_remaining"] == 42

    def test_heal_negative_damage_path(self, client, fresh_player):
        """路径: heal — damage < 0 分支"""
        r = client.post("/api/combat", json={"player_id": fresh_player, "skill_id": "heal"})
        data = r.json()["data"]
        assert r.status_code == 200
        assert data["damage"] == 0
        assert "恢复" in data["message"]

    def test_power_strike_path(self, client, fresh_player):
        """路径: power_strike"""
        r = client.post("/api/combat", json={"player_id": fresh_player, "skill_id": "power_strike"})
        assert r.status_code == 200
        assert r.json()["data"]["mp_remaining"] == 38

    def test_invalid_skill_branch(self, client, fresh_player):
        """分支: skill_id 不在 skills 字典中"""
        r = client.post("/api/combat", json={"player_id": fresh_player, "skill_id": "unknown"})
        assert r.status_code == 400

    def test_nonexistent_player_branch(self, client):
        """分支: player_id 不存在"""
        r = client.post("/api/combat", json={"player_id": "ghost", "skill_id": "fireball"})
        assert r.status_code == 404

    def test_mp_insufficient_branch(self, client, fresh_player):
        """分支: MP < cost — Bug #1: pass 而非 raise"""
        for _ in range(5):
            client.post("/api/combat", json={"player_id": fresh_player, "skill_id": "fireball"})
        r = client.post("/api/combat", json={"player_id": fresh_player, "skill_id": "fireball"})
        assert r.status_code == 200  # Bug: 应为 403

    def test_mp_goes_negative_branch(self, client, fresh_player):
        """分支: MP 扣到负值 — Bug #3 的延伸"""
        for _ in range(10):
            client.post("/api/combat", json={"player_id": fresh_player, "skill_id": "fireball"})
        r = client.get(f"/api/player/{fresh_player}")
        mp = r.json()["data"]["mp"]
        assert mp < 0, f"预期 MP 为负值（Bug），实际 {mp}"


class TestInventoryBranchCoverage:
    """背包接口分支覆盖"""

    def test_add_single_item(self, client, fresh_player):
        """分支: quantity=1"""
        r = client.post("/api/inventory/add", json={
            "player_id": fresh_player, "item_id": "potion", "quantity": 1
        })
        assert r.status_code == 200
        assert r.json()["data"]["current_count"] == 1

    def test_add_multiple_items(self, client, fresh_player):
        """分支: quantity>1"""
        r = client.post("/api/inventory/add", json={
            "player_id": fresh_player, "item_id": "sword", "quantity": 5
        })
        assert r.status_code == 200
        assert r.json()["data"]["current_count"] == 5

    def test_add_exceeds_capacity(self, client, fresh_player):
        """分支: 超过 20 格容量 — Bug #4: pass 而非 raise"""
        client.post("/api/inventory/add", json={
            "player_id": fresh_player, "item_id": "junk", "quantity": 20
        })
        r = client.post("/api/inventory/add", json={
            "player_id": fresh_player, "item_id": "overflow", "quantity": 1
        })
        assert r.status_code == 200  # Bug: 应为 400
        assert r.json()["data"]["current_count"] == 21

    def test_nonexistent_player(self, client):
        """分支: player_id 不存在"""
        r = client.post("/api/inventory/add", json={
            "player_id": "ghost", "item_id": "potion", "quantity": 1
        })
        assert r.status_code == 404


class TestShopBranchCoverage:
    """商店接口分支覆盖"""

    def test_buy_single_item(self, client, fresh_player):
        """分支: quantity=1 — 正常扣费"""
        r = client.post("/api/shop/buy", json={
            "player_id": fresh_player, "item_id": "potion", "quantity": 1
        })
        assert r.status_code == 200
        assert r.json()["data"]["gold_remaining"] == 950

    def test_buy_multiple_items_bug(self, client, fresh_player):
        """分支: quantity>1 — Bug #5: 只扣单件价"""
        r = client.post("/api/shop/buy", json={
            "player_id": fresh_player, "item_id": "potion", "quantity": 3
        })
        data = r.json()["data"]
        assert r.status_code == 200
        assert data["total_cost"] == 150
        assert data["gold_remaining"] == 950  # Bug: 应扣 150 但实际只扣 50

    def test_buy_invalid_item(self, client, fresh_player):
        """分支: item_id 不在 item_prices 中"""
        r = client.post("/api/shop/buy", json={
            "player_id": fresh_player, "item_id": "legendary_sword", "quantity": 1
        })
        assert r.status_code == 400

    def test_buy_nonexistent_player(self, client):
        """分支: player_id 不存在"""
        r = client.post("/api/shop/buy", json={
            "player_id": "ghost", "item_id": "potion", "quantity": 1
        })
        assert r.status_code == 404


class TestCombatLogBranch:
    """战斗日志分支覆盖"""

    def test_empty_log(self, client, fresh_player):
        """分支: combat_log 为空"""
        r = client.get("/api/combat/log")
        assert r.status_code == 200
        assert r.json()["data"] == []

    def test_log_after_combat(self, client, fresh_player):
        """分支: combat_log 有记录"""
        client.post("/api/combat", json={"player_id": fresh_player, "skill_id": "fireball"})
        r = client.get("/api/combat/log")
        assert r.status_code == 200
        log = r.json()["data"]
        assert len(log) == 1
        assert log[0]["skill_id"] == "fireball"


class TestGetPlayerBranch:
    """玩家查询分支覆盖"""

    def test_existing_player(self, client, fresh_player):
        """分支: player_id 存在"""
        r = client.get(f"/api/player/{fresh_player}")
        assert r.status_code == 200
        assert "username" in r.json()["data"]

    def test_nonexistent_player(self, client):
        """分支: player_id 不存在"""
        r = client.get("/api/player/ghost")
        assert r.status_code == 404
