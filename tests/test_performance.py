"""
性能测试 — 对游戏 Mock Server 进行并发压测
通过真实 HTTP 请求对 Uvicorn 服务施压，用墙钟时间计算吞吐量
覆盖: 登录 / 战斗 / 背包 / 商店 / 混合场景 / 并发可扩展性
"""
import asyncio
import itertools
import json
import statistics
import time

import httpx

from server_config import BASE_URL

# 延迟阈值基于本机实测基线设定，留约 2 倍余量。
# 绝对延迟强依赖运行环境与并发度（并发越高，被测服务的排队越严重），
# 换机器或在 CI 中运行需重新标定。
# error_rate 断言是稳定的验收项；延迟断言只用于拦截严重退化。


async def run_load_test(concurrency: int, total_requests: int, request_fn):
    latencies: list[float] = []
    errors = 0

    limits = httpx.Limits(
        max_connections=concurrency,
        max_keepalive_connections=concurrency,
    )
    sem = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(base_url=BASE_URL, limits=limits, timeout=10.0) as client:
        async def worker():
            nonlocal errors
            async with sem:
                t0 = time.perf_counter()
                try:
                    r = await request_fn(client)
                    ok = r.status_code == 200
                except httpx.HTTPError:
                    ok = False
                latencies.append((time.perf_counter() - t0) * 1000)
                if not ok:
                    errors += 1

        wall_start = time.perf_counter()
        await asyncio.gather(*(worker() for _ in range(total_requests)))
        wall_elapsed = time.perf_counter() - wall_start

    latencies.sort()
    n = len(latencies)
    return {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "errors": errors,
        "error_rate": f"{errors / total_requests * 100:.1f}%",
        "wall_seconds": round(wall_elapsed, 3),
        "rps": round(total_requests / wall_elapsed, 1),
        "theoretical_max_rps": round(concurrency / (statistics.mean(latencies) / 1000), 1),
        "min_ms": round(latencies[0], 2),
        "avg_ms": round(statistics.mean(latencies), 2),
        "max_ms": round(latencies[-1], 2),
        "p50_ms": round(latencies[n // 2], 2),
        "p95_ms": round(latencies[int(n * 0.95)], 2),
        "p99_ms": round(latencies[int(n * 0.99)], 2),
    }


async def test_health_check_performance():
    """健康检查基线 — 50 并发 / 500 请求"""
    async def req(client):
        return await client.get("/api/health")

    result = await run_load_test(50, 500, req)
    print(f"\n[健康检查] {json.dumps(result, ensure_ascii=False)}")
    assert result["error_rate"] == "0.0%"
    assert result["p95_ms"] < 1000


async def test_login_performance():
    """登录接口 — 20 并发 / 200 请求"""
    counter = itertools.count(1)

    async def req(client):
        uid = next(counter)
        return await client.post("/api/login", json={"username": f"perf_{uid}", "password": "123"})

    result = await run_load_test(20, 200, req)
    print(f"\n[登录] {json.dumps(result, ensure_ascii=False)}")
    assert result["error_rate"] == "0.0%"
    assert result["p95_ms"] < 200


async def test_combat_performance():
    """战斗接口 — 10 并发 / 100 请求"""
    async with httpx.AsyncClient(base_url=BASE_URL) as c:
        r = await c.post("/api/login", json={"username": "combat_perf", "password": "123"})
        pid = r.json()["data"]["player_id"]

    async def req(client):
        return await client.post("/api/combat", json={"player_id": pid, "skill_id": "fireball"})

    result = await run_load_test(10, 100, req)
    print(f"\n[战斗] {json.dumps(result, ensure_ascii=False)}")
    assert result["error_rate"] == "0.0%"


async def test_inventory_query_performance():
    """背包查询 — 30 并发 / 300 请求"""
    async with httpx.AsyncClient(base_url=BASE_URL) as c:
        r = await c.post("/api/login", json={"username": "inv_perf", "password": "123"})
        pid = r.json()["data"]["player_id"]

    async def req(client):
        return await client.get(f"/api/inventory/{pid}")

    result = await run_load_test(30, 300, req)
    print(f"\n[背包查询] {json.dumps(result, ensure_ascii=False)}")
    assert result["error_rate"] == "0.0%"
    assert result["p95_ms"] < 400


async def test_shop_buy_performance():
    """商店购买 — 10 并发 / 100 请求"""
    async with httpx.AsyncClient(base_url=BASE_URL) as c:
        r = await c.post("/api/login", json={"username": "shop_perf", "password": "123"})
        pid = r.json()["data"]["player_id"]

    async def req(client):
        return await client.post(
            "/api/shop/buy",
            json={"player_id": pid, "item_id": "potion", "quantity": 1},
        )

    result = await run_load_test(10, 100, req)
    print(f"\n[商店购买] {json.dumps(result, ensure_ascii=False)}")
    assert result["error_rate"] == "0.0%"


async def test_mixed_scenario_performance():
    """混合场景 — 15 并发 / 75 玩家完整流程: 登录→战斗x3→背包→商店"""
    counter = itertools.count(1)

    async def player_flow(client):
        uid = next(counter)
        times = []

        t0 = time.perf_counter()
        r = await client.post("/api/login", json={"username": f"mix_{uid}", "password": "123"})
        times.append((time.perf_counter() - t0) * 1000)
        if r.status_code != 200:
            return times, False

        pid = r.json()["data"]["player_id"]
        for skill in ["fireball", "frostbolt", "heal"]:
            t0 = time.perf_counter()
            await client.post("/api/combat", json={"player_id": pid, "skill_id": skill})
            times.append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        await client.get(f"/api/inventory/{pid}")
        times.append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        await client.post("/api/shop/buy", json={"player_id": pid, "item_id": "potion", "quantity": 1})
        times.append((time.perf_counter() - t0) * 1000)

        return times, True

    all_times, errors = [], 0
    limits = httpx.Limits(max_connections=15, max_keepalive_connections=15)
    sem = asyncio.Semaphore(15)

    async with httpx.AsyncClient(base_url=BASE_URL, limits=limits, timeout=10.0) as client:
        async def worker():
            nonlocal errors
            async with sem:
                times, ok = await player_flow(client)
                all_times.extend(times)
                if not ok:
                    errors += 1

        wall_start = time.perf_counter()
        await asyncio.gather(*(worker() for _ in range(75)))
        wall_elapsed = time.perf_counter() - wall_start

    all_times.sort()
    n = len(all_times)
    result = {
        "scenario": "login->combat x3->inventory->shop",
        "concurrent_users": 15,
        "total_flows": 75,
        "total_requests": n,
        "errors": errors,
        "error_rate": f"{errors / 75 * 100:.1f}%",
        "wall_seconds": round(wall_elapsed, 3),
        "flow_rps": round(75 / wall_elapsed, 1),
        "request_rps": round(n / wall_elapsed, 1),
        "min_ms": round(all_times[0], 2),
        "avg_ms": round(statistics.mean(all_times), 2),
        "max_ms": round(all_times[-1], 2),
        "p50_ms": round(all_times[n // 2], 2),
        "p95_ms": round(all_times[int(n * 0.95)], 2),
        "p99_ms": round(all_times[int(n * 0.99)], 2),
    }
    print(f"\n[混合场景] {json.dumps(result, ensure_ascii=False)}")
    assert errors == 0


async def test_concurrency_scalability():
    """并发可扩展性 — 测试 5/10/20/50 并发下吞吐量变化"""
    async with httpx.AsyncClient(base_url=BASE_URL) as c:
        r = await c.post("/api/login", json={"username": "scale_test", "password": "123"})
        pid = r.json()["data"]["player_id"]

    results = []
    for concurrency in [5, 10, 20, 50]:
        async def req(client):
            return await client.get(f"/api/player/{pid}")

        result = await run_load_test(concurrency, concurrency * 20, req)
        results.append({
            "concurrency": concurrency,
            "rps": result["rps"],
            "theoretical_max_rps": result["theoretical_max_rps"],
            "error_rate": result["error_rate"],
            "p95_ms": result["p95_ms"],
            "avg_ms": result["avg_ms"],
        })
    print(f"\n[扩展性] {json.dumps(results, ensure_ascii=False)}")
    # 实测现象：并发升高时吞吐反而下降（5 并发 1460 RPS → 50 并发 294 RPS）。
    # 原因是被测服务的 handler 是同步 def，受 anyio 默认 40 线程池上限约束，
    # 并发超过该上限后只会增加排队，不再提升吞吐。
    # 因此这里只设最低水位护栏，性能曲线本身作为观测数据记录，不作为通过条件。
    assert all(r["error_rate"] == "0.0%" for r in results)
    assert all(r["rps"] > 100 for r in results)
