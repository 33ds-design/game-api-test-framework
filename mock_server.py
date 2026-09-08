"""
Game Server Mock — 模拟游戏服务端 API
包含故意植入的 Bug，供自动化测试发现
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import random
import uvicorn

app = FastAPI(title="Game Server Mock", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ---- In-memory game state ----
players = {}
inventory = {}
combat_log = []

class LoginRequest(BaseModel):
    username: str
    password: str

class CombatRequest(BaseModel):
    player_id: str
    skill_id: str
    target_id: Optional[str] = "monster_001"

class TradeRequest(BaseModel):
    player_id: str
    item_id: str
    quantity: int

# ---- API Endpoints ----

@app.post("/api/login")
def login(req: LoginRequest):
    """玩家登录"""
    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    player_id = f"player_{hash(req.username) % 10000}"
    players[player_id] = {
        "username": req.username,
        "level": 1,
        "hp": 100,
        "mp": 50,
        "atk": 10,
        "def": 5,
        "gold": 1000,
    }
    inventory[player_id] = []
    return {"code": 0, "msg": "success", "data": {"player_id": player_id, "token": f"token_{player_id}"}}

@app.get("/api/player/{player_id}")
def get_player(player_id: str):
    """获取玩家信息"""
    if player_id not in players:
        raise HTTPException(status_code=404, detail="玩家不存在")
    return {"code": 0, "data": players[player_id]}

@app.post("/api/combat")
def combat(req: CombatRequest):
    """战斗系统 — 植入了 3 个 Bug"""
    if req.player_id not in players:
        raise HTTPException(status_code=404, detail="玩家不存在")

    player = players[req.player_id]
    skill_id = req.skill_id

    # 技能定义
    skills = {
        "fireball":      {"mp_cost": 10, "damage": 30, "cooldown": 3},
        "frostbolt":     {"mp_cost": 8,  "damage": 25, "cooldown": 2},
        "heal":          {"mp_cost": 15, "damage": -20, "cooldown": 5},
        "power_strike":  {"mp_cost": 12, "damage": 40, "cooldown": 4},
    }

    if skill_id not in skills:
        raise HTTPException(status_code=400, detail="技能不存在")

    skill = skills[skill_id]

    # Bug #1: MP 检查遗漏 — MP 不足时仍可施法（应该返回 403）
    # 正确逻辑: if player["mp"] < skill["mp_cost"]: return error
    # 当前逻辑: 只打印警告但不拦截
    if player["mp"] < skill["mp_cost"]:
        pass  # BUG: 应该 raise HTTPException(403, "MP 不足")

    # 扣除 MP
    player["mp"] -= skill["mp_cost"]

    # Bug #2: 伤害计算错误 — 暴击时伤害应该 x2，但这里用了 x1.5
    is_crit = random.random() < 0.2
    if is_crit:
        actual_damage = int(skill["damage"] * 1.5)  # BUG: 应该 * 2
    else:
        actual_damage = skill["damage"]

    # Bug #3: 治疗技能伤害方向错误 — heal 的 damage 是 -20（负值代表治疗）
    # 但战斗系统对负值伤害的处理不正确
    if skill["damage"] < 0:
        player["hp"] -= skill["damage"]  # 正确: hp += 20
        actual_damage = 0
        result_text = f"施放 {skill_id}，恢复 HP {abs(skill['damage'])}"
    else:
        result_text = f"施放 {skill_id}，造成伤害 {actual_damage}{' (暴击!)' if is_crit else ''}"

    combat_log.append({
        "player_id": req.player_id,
        "skill_id": skill_id,
        "damage": actual_damage,
        "is_crit": is_crit,
        "mp_remaining": player["mp"],
    })

    return {
        "code": 0,
        "data": {
            "skill_id": skill_id,
            "damage": actual_damage,
            "is_crit": is_crit,
            "mp_remaining": player["mp"],
            "hp_remaining": player["hp"],
            "message": result_text,
        }
    }

@app.post("/api/inventory/add")
def add_item(req: TradeRequest):
    """添加物品到背包"""
    if req.player_id not in players:
        raise HTTPException(status_code=404, detail="玩家不存在")

    # Bug #4: 背包容量检查遗漏 — 超过 20 格仍可添加
    if len(inventory[req.player_id]) >= 20:
        pass  # BUG: 应该 raise HTTPException(400, "背包已满")

    for _ in range(req.quantity):
        inventory[req.player_id].append({"item_id": req.item_id, "uid": f"{req.item_id}_{len(inventory[req.player_id])}"})

    return {"code": 0, "data": {"current_count": len(inventory[req.player_id])}}

@app.get("/api/inventory/{player_id}")
def get_inventory(player_id: str):
    """获取背包"""
    if player_id not in players:
        raise HTTPException(status_code=404, detail="玩家不存在")
    return {"code": 0, "data": {"items": inventory[player_id], "count": len(inventory[player_id])}}

@app.post("/api/shop/buy")
def buy_item(req: TradeRequest):
    """商店购买"""
    if req.player_id not in players:
        raise HTTPException(status_code=404, detail="玩家不存在")

    player = players[req.player_id]
    item_prices = {"potion": 50, "sword": 500, "shield": 300, "gem": 100}

    if req.item_id not in item_prices:
        raise HTTPException(status_code=400, detail="物品不存在")

    total_cost = item_prices[req.item_id] * req.quantity

    # Bug #5: 金币扣除错误 — 批量购买时只扣一件的钱
    if req.quantity > 1:
        player["gold"] -= item_prices[req.item_id]  # BUG: 应该 -= total_cost
    else:
        player["gold"] -= total_cost

    # 添加物品到背包
    for _ in range(req.quantity):
        inventory[req.player_id].append({"item_id": req.item_id, "uid": f"{req.item_id}_{len(inventory[req.player_id])}"})

    return {
        "code": 0,
        "data": {
            "item_id": req.item_id,
            "quantity": req.quantity,
            "total_cost": total_cost,
            "gold_remaining": player["gold"],
        }
    }

@app.get("/api/combat/log")
def get_combat_log():
    """获取战斗日志"""
    return {"code": 0, "data": combat_log[-20:]}

@app.get("/api/health")
def health():
    """健康检查"""
    return {"code": 0, "status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=18080)
