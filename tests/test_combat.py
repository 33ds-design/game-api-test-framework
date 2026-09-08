"""
战斗系统 API 测试
覆盖: 技能施放 / MP 消耗 / 暴击伤害 / 治疗逻辑
"""
import pytest
import requests

BASE = "http://127.0.0.1:18080"


@pytest.fixture(scope="class")
def player():
    """创建测试玩家"""
    r = requests.post(f"{BASE}/api/login", json={"username": "combat_tester", "password": "123456"})
    assert r.status_code == 200
    data = r.json()["data"]
    return {"player_id": data["player_id"], "token": data["token"]}


@pytest.mark.smoke
class TestCombatSmoke:
    """冒烟测试: 基础战斗功能"""

    def test_fireball_basic(self, player):
        """施放火球术 — 基础伤害验证 (考虑暴击可能)"""
        r = requests.post(f"{BASE}/api/combat", json={
            "player_id": player["player_id"],
            "skill_id": "fireball"
        })
        data = r.json()["data"]
        assert r.status_code == 200
        # 非暴击 30，暴击 45 (BUG: 应为 60)
        assert data["damage"] in [30, 45, 60]
        assert data["mp_remaining"] == 40  # 50 - 10

    def test_frostbolt_basic(self, player):
        """施放冰霜箭 — 基础伤害验证"""
        r = requests.post(f"{BASE}/api/combat", json={
            "player_id": player["player_id"],
            "skill_id": "frostbolt"
        })
        data = r.json()["data"]
        assert r.status_code == 200
        assert data["damage"] == 25

    def test_invalid_skill(self, player):
        """无效技能 ID 应返回 400"""
        r = requests.post(f"{BASE}/api/combat", json={
            "player_id": player["player_id"],
            "skill_id": "meteor"
        })
        assert r.status_code == 400


@pytest.mark.combat
class TestMPSystem:
    """MP 消耗系统测试"""

    def test_mp_cost_fireball(self, player):
        """火球术消耗 10 MP"""
        r = requests.get(f"{BASE}/api/player/{player['player_id']}")
        initial_mp = r.json()["data"]["mp"]

        requests.post(f"{BASE}/api/combat", json={
            "player_id": player["player_id"],
            "skill_id": "fireball"
        })

        r = requests.get(f"{BASE}/api/player/{player['player_id']}")
        current_mp = r.json()["data"]["mp"]
        assert initial_mp - current_mp == 10

    def test_mp_insufficient_should_fail(self, player):
        """MP 不足时应返回错误 (BUG #1)"""
        pid = player["player_id"]

        # 连续施放火球术直到 MP 耗尽 (50 / 10 = 5 次)
        for i in range(5):
            requests.post(f"{BASE}/api/combat", json={
                "player_id": pid, "skill_id": "fireball"
            })

        # 第 6 次施放 — MP 已为 0，应该被拦截
        r = requests.post(f"{BASE}/api/combat", json={
            "player_id": pid, "skill_id": "fireball"
        })

        # 预期: 应该返回 403 (MP 不足)
        # 实际: 返回 200 (BUG #1 — MP 检查被跳过)
        assert r.status_code == 403, f"BUG #1: MP 不足时仍可施法, got status {r.status_code}"

    def test_mp_not_negative(self, player):
        """MP 不应为负值"""
        pid = player["player_id"]

        # 耗尽 MP
        for _ in range(5):
            requests.post(f"{BASE}/api/combat", json={
                "player_id": pid, "skill_id": "fireball"
            })

        # 继续施放
        requests.post(f"{BASE}/api/combat", json={
            "player_id": pid, "skill_id": "fireball"
        })

        r = requests.get(f"{BASE}/api/player/{pid}")
        mp = r.json()["data"]["mp"]
        assert mp >= 0, f"BUG: MP 为负值 {mp}"


@pytest.mark.combat
@pytest.mark.bug
class TestCombatBugs:
    """已知 Bug 验证测试"""

    def test_bug_crit_damage_multiplier(self, player):
        """BUG #2: 暴击伤害应为 x2 但实际为 x1.5"""
        pid = player["player_id"]
        crit_damage = None

        # 多次施放火球术尝试触发暴击
        for _ in range(50):
            r = requests.post(f"{BASE}/api/combat", json={
                "player_id": pid, "skill_id": "fireball"
            })
            data = r.json()["data"]
            if data["is_crit"]:
                crit_damage = data["damage"]
                break

        if crit_damage is not None:
            # 火球术基础伤害 30，暴击应为 60
            assert crit_damage == 60, f"BUG #2: 暴击伤害 {crit_damage} != 预期 60 (实际为 {crit_damage}, 疑似 x1.5 而非 x2)"
        else:
            pytest.skip("50 次施放未触发暴击，概率问题")

    def test_bug_heal_direction(self, player):
        """BUG #3: 治疗技能应增加 HP 而非减少"""
        pid = player["player_id"]

        r = requests.get(f"{BASE}/api/player/{pid}")
        hp_before = r.json()["data"]["hp"]

        requests.post(f"{BASE}/api/combat", json={
            "player_id": pid, "skill_id": "heal"
        })

        r = requests.get(f"{BASE}/api/player/{pid}")
        hp_after = r.json()["data"]["hp"]

        # 治疗应增加 HP
        assert hp_after > hp_before, f"BUG #3: 治疗后 HP {hp_after} <= 治疗前 {hp_before}，治疗方向错误"
