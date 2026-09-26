"""
背包系统 + 商店系统 API 测试
覆盖: 物品添加 / 背包容量 / 商店购买 / 金币扣除
"""
import pytest
import requests

from server_config import BASE_URL as BASE


@pytest.fixture(scope="class")
def player():
    r = requests.post(f"{BASE}/api/login", json={"username": "inv_tester", "password": "123456"})
    data = r.json()["data"]
    return {"player_id": data["player_id"], "token": data["token"]}


@pytest.mark.smoke
class TestInventorySmoke:
    """背包系统冒烟测试"""

    def test_empty_inventory(self, player):
        """新玩家背包应为空"""
        r = requests.get(f"{BASE}/api/inventory/{player['player_id']}")
        data = r.json()["data"]
        assert data["count"] == 0

    def test_add_item(self, player):
        """添加物品到背包"""
        r = requests.post(f"{BASE}/api/inventory/add", json={
            "player_id": player["player_id"],
            "item_id": "potion",
            "quantity": 3
        })
        assert r.status_code == 200
        assert r.json()["data"]["current_count"] == 3


@pytest.mark.inventory
@pytest.mark.bug
class TestInventoryBugs:
    """背包系统 Bug 验证"""

    @pytest.mark.xfail(strict=True, reason="BUG-004: 背包缺少 20 格上限校验")
    def test_bug_inventory_capacity(self, player):
        """BUG #4: 背包超过 20 格应拒绝添加但实际没有"""
        pid = player["player_id"]

        # 添加 25 个物品（超过 20 格上限）
        requests.post(f"{BASE}/api/inventory/add", json={
            "player_id": pid,
            "item_id": "gem",
            "quantity": 25
        })

        r2 = requests.get(f"{BASE}/api/inventory/{pid}")
        count = r2.json()["data"]["count"]

        # 预期: 背包最多 20 格
        # 实际: 没有容量限制 (BUG #4)
        assert count <= 20, f"BUG #4: 背包数量 {count} 超过上限 20"


@pytest.mark.shop
class TestShopSystem:
    """商店系统测试"""

    def test_buy_single_item(self, player):
        """购买单件物品 — 金币正确扣除"""
        pid = player["player_id"]
        r = requests.get(f"{BASE}/api/player/{pid}")
        gold_before = r.json()["data"]["gold"]

        r = requests.post(f"{BASE}/api/shop/buy", json={
            "player_id": pid,
            "item_id": "potion",
            "quantity": 1
        })
        assert r.status_code == 200
        assert gold_before - r.json()["data"]["gold_remaining"] == 50

    @pytest.mark.bug
    @pytest.mark.xfail(strict=True, reason="BUG-005: 批量购买只扣单件价格（5 件扣 50 而非 250）")
    def test_buy_multiple_items(self, player):
        """购买多件物品 — 金币应按总价扣除"""
        pid = player["player_id"]
        r = requests.get(f"{BASE}/api/player/{pid}")
        gold_before = r.json()["data"]["gold"]

        r = requests.post(f"{BASE}/api/shop/buy", json={
            "player_id": pid,
            "item_id": "potion",
            "quantity": 5
        })
        actual_cost = gold_before - r.json()["data"]["gold_remaining"]

        # 5 瓶药水 = 250 金币
        # BUG #5: 批量购买只扣一件的钱 (50)
        assert actual_cost == 250, f"BUG #5: 批量购买 5 件应扣 250 金币，实际扣除 {actual_cost}"

    @pytest.mark.bug
    @pytest.mark.xfail(strict=True, reason="BUG-006: 商店缺少金币充足性校验，金币不足仍返回 200")
    def test_insufficient_gold(self, player):
        """金币不足时应返回错误"""
        pid = player["player_id"]

        # 尝试购买大量物品耗尽金币
        r = requests.post(f"{BASE}/api/shop/buy", json={
            "player_id": pid,
            "item_id": "sword",
            "quantity": 100
        })
        # 金币不足应被拦截
        assert r.status_code in [400, 403], "金币不足时应返回错误"
