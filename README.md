# Game API Test Framework

[![CI](https://github.com/33ds-design/game-api-test-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/33ds-design/game-api-test-framework/actions/workflows/ci.yml)

游戏服务端 API 自动化测试框架 — 基于 FastAPI Mock Server + pytest，覆盖功能测试、白盒分支测试、并发性能压测三个维度。

## 项目简介

本项目模拟游戏服务端 API（登录/战斗/背包/商店四大模块共 8 个 API 端点），内置 6 处故意植入的缺陷（BUG-001 ~ BUG-006）。使用 pytest 自动化测试框架进行 API 级测试，包含功能验证、白盒分支覆盖和并发性能压测，自动检测并报告 Bug，产出 HTML / JSON 双格式测试报告。

## 技术栈

- **Mock Server**: FastAPI + Uvicorn (Python)
- **测试框架**: pytest + requests + pytest-html + pytest-json-report
- **覆盖率**: pytest-cov (代码覆盖率 + 分支覆盖率)
- **性能压测**: httpx.AsyncClient + asyncio (真实 HTTP 压测, 并发梯度 5/10/20/50)
- **测试用例总数**: 51 个 (功能测试 20 + 白盒分支测试 24 + 性能压测 7)

## 项目结构

```
game-api-test-framework/
├── mock_server.py              # 游戏服务端 Mock (含 5 类植入 Bug)
├── server_config.py            # HOST/PORT/BASE_URL 单一来源 (可用 MOCK_HOST/MOCK_PORT 覆盖)
├── conftest.py                 # pytest fixture (自动管理 Mock Server 生命周期)
├── pytest.ini                  # pytest 配置文件
├── requirements.txt            # Python 直接依赖 (下限约束)
├── requirements.lock           # 依赖版本锁定快照 (pip freeze 生成)
├── .python-version             # 声明的 Python 版本 (3.12.10)
├── LICENSE                     # MIT 许可证
├── run_tests.py                # 测试运行入口
├── generate_screenshots.py     # 测试报告截图生成脚本
├── .github/workflows/ci.yml    # GitHub Actions CI
└── tests/
    ├── test_login.py            # 登录系统测试 (功能 + 冒烟)
    ├── test_combat.py           # 战斗系统测试 (功能 + Bug 验证)
    ├── test_inventory_shop.py   # 背包+商店测试 (功能 + Bug 验证)
    ├── test_whitebox.py         # 白盒分支测试 (24 用例覆盖全部 if/else 分支)
    └── test_performance.py      # 并发性能压测 (7 场景, 5/10/20/50 并发梯度)
```

## 植入的缺陷清单

| Bug ID | 模块 | 描述 | 严重级别 | 检出状态 |
|--------|------|------|----------|----------|
| BUG-001 | 战斗 | MP 不足时仍可施法，MP 被扣成负值 | Critical | ✅ 检出（xfail 登记） |
| BUG-002 | 战斗 | 暴击系数 x1.5（应为 x2） | Medium | ✅ 检出（xfail 登记） |
| BUG-003 | 战斗 | 治疗技能 HP 方向 — 代码 `hp -= (-20)` 实际为回血，未复现 | — | ❌ 未复现 |
| BUG-004 | 背包 | 缺少 20 格容量上限校验 | High | ✅ 检出（xfail 登记） |
| BUG-005 | 商店 | 批量购买只扣单件价格 | High | ✅ 检出（xfail 登记） |
| BUG-006 | 商店 | 缺少金币充足性校验，金币不足仍返回 200 | High | ✅ 检出（xfail 登记） |

> 预期失败约定：缺陷用例统一标注 `@pytest.mark.xfail(strict=True)`。缺陷被修复后该用例会转为 XPASS 并导致测试失败，从而强制移除过期标记，避免"假绿"。

## 测试架构

### 三层测试结构
- **冒烟测试** (`-m smoke`, 11 个): 验证核心 API 可用性
- **功能测试** (20 个): 验证正常流程 + 边界条件
- **Bug 验证测试** (`-m bug`, 7 个): 验证植入缺陷的实际行为，其中 6 个以 `xfail` 登记为预期失败

### 白盒分支测试 (24 个)
- 使用 FastAPI TestClient + pytest-cov（in-process 直连，无网络开销）
- `mock_server.py` 共 8 个端点，白盒用例实际调用其中 6 个（`get_inventory`、`health` 未被调用）
- 语句覆盖率 95% (92/97 语句，未覆盖行 148-150 / 194 / 198)
- 分支覆盖率 91% (29/32，另有 1 个部分覆盖分支)
- 语句与分支合并口径下 `--cov-branch` 显示 94%

### 并发性能压测 (7 个)
- 使用 `httpx.AsyncClient` + `asyncio.gather` + `Semaphore` 发起真实 HTTP 请求，服务端由 `conftest.py` 拉起真实 Uvicorn 进程
- 吞吐量按墙钟时间计算 (`total_requests / wall_elapsed`)，而非按单次调用耗时倒推
- 覆盖 5/10/20/50 并发梯度，产出 P50/P95/P99 延迟分位、吞吐量 (RPS)、错误率
- 单场景最高吞吐 979.4 RPS（商店购买，10 并发）；扩展性测试 5 并发达 1354.0 RPS
- 包含混合场景测试 (登录→战斗x3→背包→商店, 15 并发 / 75 流程 / 450 请求 / 0 错误)
- 实测现象：并发升高吞吐反而下降（5 并发 1354.0 RPS → 50 并发 308.2 RPS）。被测 handler 为同步 `def`，受 anyio 默认 40 线程池上限约束，超限后只排队不提速

## 运行方式

项目依赖 Python 3.12，精确版本记录在 `.python-version`（当前 `3.12.10`）。若系统默认 `python` 是 3.10，直接运行会报 `ModuleNotFoundError`，
因此推荐在项目内建一个虚拟环境，后续所有命令都用 venv 里的解释器执行
（`run_tests.py` 与 `conftest.py` 均以 `sys.executable` 拉起 pytest 和 Mock Server，会自动沿用同一个解释器）。

```bash
# 1) 创建虚拟环境（只需一次）
py -3.12 -m venv .venv

# 2) 安装依赖（只需一次）
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2b) 需要与锁定快照完全一致的版本时，改装 lock 文件（可选）
.\.venv\Scripts\python.exe -m pip install -r requirements.lock

# 3) 运行全部测试
.\.venv\Scripts\python.exe run_tests.py

# 也可以先激活再运行，效果相同
.\.venv\Scripts\Activate.ps1   # PowerShell
python run_tests.py

# 或直接用 pytest
.\.venv\Scripts\python.exe -m pytest tests/ -v --html=test-report.html --self-contained-html

# 运行白盒测试 + 覆盖率
.\.venv\Scripts\python.exe -m pytest tests/test_whitebox.py --cov=mock_server --cov-report=html

# 运行性能压测
.\.venv\Scripts\python.exe -m pytest tests/test_performance.py -v

# 仅运行缺陷验证用例，并显示预期失败原因
.\.venv\Scripts\python.exe -m pytest tests/ -m bug -rx
```

> `requirements.txt` 里的 `sniffio` 不是可选装饰：`httpcore` 每次请求都会执行一次
> `import sniffio`（见 `httpcore/_synchronization.py`），缺包时该导入失败不会被
> `sys.modules` 缓存，每次请求都要重扫 `sys.path`，压测吞吐会掉一半（实测 314 → 166 RPS）。

## 工程化配置

| 项 | 文件 | 说明 |
|----|------|------|
| CI | `.github/workflows/ci.yml` | GitHub Actions，两个作业：`test` 跑功能/白盒/缺陷用例并统计覆盖率（阻塞门禁）；`performance` 单独跑压测，`continue-on-error: true` 非阻塞 |
| 许可证 | `LICENSE` | MIT |
| 依赖锁定 | `requirements.lock` | `pip freeze` 快照，固定 35 个包（含传递依赖）的精确版本 |
| Python 版本 | `.python-version` | `3.12.10`，CI 用 `actions/setup-python` 的 `python-version-file` 读取 |

**压测为何在 CI 里非阻塞**：压测的延迟断言（健康检查 `p95 < 1000ms`、登录 `p95 < 200ms`）强依赖 runner 的 CPU 与调度。
本机 50 并发健康检查实测 `p95` 已到 445ms，共享 runner 上更容易抖动。`error_rate` 断言稳定，延迟断言只用于拦截严重退化，
因此不设为阻塞门禁——失败仍会在 Actions 里以红叉暴露，只是不阻断合并。

**CI 为何装 `requirements.txt` 而非 `requirements.lock`**：lock 快照采集自 Windows + Python 3.12.10，含平台相关包（如 `colorama`）。
CI 跑在 ubuntu runner，用 `requirements.txt` 的版本区间解析更稳妥；lock 用于同平台（本地/开发机）精确复现。

## 测试结果

| 指标 | 数值 |
|------|------|
| 总测试用例 | 51 |
| 测试结果 | 45 passed / 6 xfailed |
| 缺陷复现 | 6/6 复现用例均以 xfail 显式登记 |
| 语句覆盖率 | 95% (92/97 语句) |
| 分支覆盖率 | 91% (29/32 分支) |
| 全场景错误率 | 0.0% |
| 最高吞吐量 | 1354.0 RPS (扩展性测试 5 并发) |
| 混合场景 | 15 并发 / 75 流程 / 450 请求 / 0 错误 |

## 端点覆盖率

`pytest tests/test_whitebox.py --cov=mock_server --cov-branch` 的实测结果：

| 端点 | 覆盖情况 |
|------|----------|
| login() | 全覆盖 |
| get_player() | 全覆盖 |
| combat() | 全覆盖 |
| add_item() | 全覆盖 |
| buy_item() | 全覆盖 |
| get_combat_log() | 全覆盖 |
| get_inventory() | 未覆盖（行 148-150） |
| health() | 未覆盖（行 194） |

未覆盖的 5 行 = `get_inventory()` 全部 3 行 + `health()` 返回行 + `__main__` 入口行（后者不计入有效覆盖）。
