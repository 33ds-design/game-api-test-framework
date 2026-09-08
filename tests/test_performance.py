"""
性能测试 — 对游戏 Mock Server 进行并发压测
使用 FastAPI TestClient (ASGI 直连) 避免网络层瓶颈
覆盖: 登录 / 战斗 / 背包 / 商店 / 混合场景
"""
import json
import time
import statistics
import threading
import sys
import os
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from mock_server import app, players, inventory, combat_log
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def client():
    players.clear()
    inventory.clear()
    combat_log.clear()
    with TestClient(app) as c:
        yield c


def run_load_test(concurrency, total_requests, request_fn):
    latencies = []
    errors = 0
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(request_fn) for _ in range(total_requests)]
        for f in as_completed(futures):
            try:
                latency, ok = f.result()
                latencies.append(latency)
                if not ok:
                    errors += 1
            except Exception:
                errors += 1
    latencies.sort()
    n = len(latencies)
    if n == 0:
        return {"concurrency": concurrency, "total": total_requests, "errors": errors}
    return {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "success": n - errors,
        "errors": errors,
        "error_rate": f"{errors/total_requests*100:.1f}%",
        "min_ms": round(min(latencies), 2),
        "avg_ms": round(statistics.mean(latencies), 2),
        "max_ms": round(max(latencies), 2),
        "p50_ms": round(latencies[n // 2], 2),
        "p95_ms": round(latencies[int(n * 0.95)], 2),
        "p99_ms": round(latencies[int(n * 0.99)], 2),
        "throughput_rps": round(n / (sum(latencies) / 1000 / concurrency), 1) if sum(latencies) > 0 else 0,
    }


def test_health_check_performance(client):
    """健康检查基线 — 50 并发 / 500 请求"""
    def req():
        t = time.perf_counter()
        r = client.get("/api/health")
        return ((time.perf_counter() - t) * 1000, r.status_code == 200)
    result = run_load_test(50, 500, req)
    print(f"\n[健康检查] {json.dumps(result, ensure_ascii=False)}")
    assert result["error_rate"] == "0.0%"
    assert result["p95_ms"] < 50


def test_login_performance(client):
    """登录接口 — 20 并发 / 200 请求"""
    lock = threading.Lock()
    counter = [0]
    def req():
        with lock:
            counter[0] += 1
            uid = counter[0]
        t = time.perf_counter()
        r = client.post("/api/login", json={"username": f"perf_{uid}", "password": "123"})
        return ((time.perf_counter() - t) * 1000, r.status_code == 200)
    result = run_load_test(20, 200, req)
    print(f"\n[登录] {json.dumps(result, ensure_ascii=False)}")
    assert result["error_rate"] == "0.0%"
    assert result["p95_ms"] < 100


def test_combat_performance(client):
    """战斗接口 — 10 并发 / 100 请求"""
    r = client.post("/api/login", json={"username": "combat_perf", "password": "123"})
    pid = r.json()["data"]["player_id"]
    def req():
        t = time.perf_counter()
        r = client.post("/api/combat", json={"player_id": pid, "skill_id": "fireball"})
        return ((time.perf_counter() - t) * 1000, r.status_code == 200)
    result = run_load_test(10, 100, req)
    print(f"\n[战斗] {json.dumps(result, ensure_ascii=False)}")
    assert result["error_rate"] == "0.0%"


def test_inventory_query_performance(client):
    """背包查询 — 30 并发 / 300 请求"""
    r = client.post("/api/login", json={"username": "inv_perf", "password": "123"})
    pid = r.json()["data"]["player_id"]
    def req():
        t = time.perf_counter()
        r = client.get(f"/api/inventory/{pid}")
        return ((time.perf_counter() - t) * 1000, r.status_code == 200)
    result = run_load_test(30, 300, req)
    print(f"\n[背包查询] {json.dumps(result, ensure_ascii=False)}")
    assert result["error_rate"] == "0.0%"
    assert result["p95_ms"] < 100


def test_shop_buy_performance(client):
    """商店购买 — 10 并发 / 100 请求"""
    r = client.post("/api/login", json={"username": "shop_perf", "password": "123"})
    pid = r.json()["data"]["player_id"]
    def req():
        t = time.perf_counter()
        r = client.post("/api/shop/buy", json={"player_id": pid, "item_id": "potion", "quantity": 1})
        return ((time.perf_counter() - t) * 1000, r.status_code == 200)
    result = run_load_test(10, 100, req)
    print(f"\n[商店购买] {json.dumps(result, ensure_ascii=False)}")
    assert result["error_rate"] == "0.0%"


def test_mixed_scenario_performance(client):
    """混合场景 — 15 并发 / 75 玩家完整流程: 登录→战斗x3→背包→商店"""
    lock = threading.Lock()
    counter = [0]
    def player_flow():
        with lock:
            counter[0] += 1
            uid = counter[0]
        times = []
        t = time.perf_counter()
        r = client.post("/api/login", json={"username": f"mix_{uid}", "password": "123"})
        times.append((time.perf_counter() - t) * 1000)
        if r.status_code != 200:
            return times, False
        pid = r.json()["data"]["player_id"]
        for skill in ["fireball", "frostbolt", "heal"]:
            t = time.perf_counter()
            client.post("/api/combat", json={"player_id": pid, "skill_id": skill})
            times.append((time.perf_counter() - t) * 1000)
        t = time.perf_counter()
        client.get(f"/api/inventory/{pid}")
        times.append((time.perf_counter() - t) * 1000)
        t = time.perf_counter()
        client.post("/api/shop/buy", json={"player_id": pid, "item_id": "potion", "quantity": 1})
        times.append((time.perf_counter() - t) * 1000)
        return times, True

    all_times = []
    errors = 0
    with ThreadPoolExecutor(max_workers=15) as pool:
        futures = [pool.submit(player_flow) for _ in range(75)]
        for f in as_completed(futures):
            try:
                times, ok = f.result()
                all_times.extend(times)
                if not ok:
                    errors += 1
            except Exception:
                errors += 1

    all_times.sort()
    n = len(all_times)
    result = {
        "scenario": "login->combat x3->inventory->shop",
        "concurrent_users": 15,
        "total_flows": 75,
        "total_requests": n,
        "errors": errors,
        "error_rate": f"{errors/75*100:.1f}%",
        "min_ms": round(min(all_times), 2),
        "avg_ms": round(statistics.mean(all_times), 2),
        "max_ms": round(max(all_times), 2),
        "p50_ms": round(all_times[n // 2], 2),
        "p95_ms": round(all_times[int(n * 0.95)], 2),
        "p99_ms": round(all_times[int(n * 0.99)], 2),
    }
    print(f"\n[混合场景] {json.dumps(result, ensure_ascii=False)}")
    assert errors == 0


def test_concurrency_scalability(client):
    """并发可扩展性 — 测试 5/10/20/50 并发下吞吐量变化"""
    r = client.post("/api/login", json={"username": "scale_test", "password": "123"})
    pid = r.json()["data"]["player_id"]
    results = []
    for concurrency in [5, 10, 20, 50]:
        def req():
            t = time.perf_counter()
            client.get("/api/player/" + pid)
            return ((time.perf_counter() - t) * 1000, True)
        result = run_load_test(concurrency, concurrency * 20, req)
        results.append({
            "concurrency": concurrency,
            "rps": result["throughput_rps"],
            "p95_ms": result["p95_ms"],
            "avg_ms": result["avg_ms"],
        })
    print(f"\n[扩展性] {json.dumps(results, ensure_ascii=False)}")
    assert all(r["rps"] > 0 for r in results)
