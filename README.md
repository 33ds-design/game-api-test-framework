# Game API Test Framework

游戏服务端 API 自动化测试框架 — 基于 FastAPI Mock Server + pytest，覆盖功能测试、白盒分支测试、并发性能压测三个维度。

## 项目简介

本项目模拟游戏服务端 API（登录/战斗/背包/商店四大模块共 10 个 API 端点），内置 5 类故意植入的 Bug。使用 pytest 自动化测试框架进行 API 级测试，包含功能验证、白盒分支覆盖和并发性能压测，自动检测并报告 Bug，产出 HTML / JSON 双格式测试报告。

## 技术栈

- **Mock Server**: FastAPI + Uvicorn (Python)
- **测试框架**: pytest + requests + pytest-html + pytest-json-report
- **覆盖率**: pytest-cov (代码覆盖率 + 分支覆盖率)
- **性能压测**: ThreadPoolExecutor (并发梯度 5/10/20/30/50)
- **测试用例总数**: 51 个 (功能测试 20 + 白盒分支测试 24 + 性能压测 7)

## 项目结构

```
game-api-test-framework/
├── mock_server.py              # 游戏服务端 Mock (含 5 类植入 Bug)
├── conftest.py                 # pytest fixture (自动管理 Mock Server 生命周期)
├── pytest.ini                  # pytest 配置文件
├── requirements.txt            # Python 依赖
├── run_tests.py                # 测试运行入口
├── generate_screenshots.py     # 测试报告截图生成脚本
└── tests/
    ├── test_login.py            # 登录系统测试 (功能 + 冒烟)
    ├── test_combat.py           # 战斗系统测试 (功能 + Bug 验证)
    ├── test_inventory_shop.py   # 背包+商店测试 (功能 + Bug 验证)
    ├── test_whitebox.py         # 白盒分支测试 (24 用例覆盖全部 if/else 分支)
    └── test_performance.py      # 并发性能压测 (7 场景, 5/10/20/30/50 并发梯度)
```

## 植入的 5 类 Bug

| Bug ID | 模块 | 描述 | 严重级别 | 检出状态 |
|--------|------|------|----------|----------|
| BUG-001 | 战斗 | MP 不足时仍可施法 (校验遗漏) | Critical | ✅ 检出 |
| BUG-002 | 战斗 | 暴击系数 x1.5 (应为 x2) | Medium | ✅ 检出 |
| BUG-003 | 战斗 | 治疗技能 HP 方向错误 (负值 -80) | Critical | ✅ 检出 |
| BUG-004 | 背包 | 批量购买只扣单件价格 | High | ✅ 检出 |
| BUG-005 | 商店 | 批量购买金币扣除错误 | High | ✅ 检出 |

## 测试架构

### 三层测试结构
- **冒烟测试** (6 个): 验证核心 API 可用性
- **功能测试** (8 个): 验证正常流程 + 边界条件
- **Bug 验证测试** (6 个): 验证植入 Bug 的实际行为符合预期

### 白盒分支测试 (24 个)
- 使用 FastAPI TestClient + pytest-cov
- 覆盖 `mock_server.py` 全部 10 个端点的 if/else 分支
- 代码覆盖率 95% (96 语句 / 5 未覆盖)
- 分支覆盖率 93% (26/28)

### 并发性能压测 (7 个)
- 使用 ThreadPoolExecutor 模拟并发
- 覆盖 5/10/20/30/50 并发梯度
- 产出 P50/P95/P99 延迟分位、吞吐量 (RPS)、错误率
- 背包查询接口吞吐量最高达 1974.9 RPS
- 包含混合场景测试 (登录→战斗x3→背包→商店, 75 并发 / 450 请求 / 0 错误)

## 运行方式

```bash
# 安装依赖
pip install -r requirements.txt

# 运行全部测试
python run_tests.py

# 或直接用 pytest
pytest tests/ -v --html=test-report.html --self-contained-html

# 运行白盒测试 + 覆盖率
pytest tests/test_whitebox.py --cov=mock_server --cov-report=html

# 运行性能压测
pytest tests/test_performance.py -v
```

## 测试结果

| 指标 | 数值 |
|------|------|
| 总测试用例 | 51 |
| 功能测试通过 | 14 passed / 6 failed-as-expected |
| Bug 检出率 | 100% (5/5 类 Bug 全部检出) |
| 代码覆盖率 | 95% (96/101 语句) |
| 分支覆盖率 | 93% (26/28 分支) |
| 全场景错误率 | 0.0% |
| 最高吞吐量 | 1974.9 RPS (背包查询) |
| 混合场景 | 75 并发 / 450 请求 / 0 错误 |

## 模块覆盖率

| 模块 | 覆盖率 |
|------|--------|
| 登录 | 100% |
| 战斗 | 85% |
| 背包 | 100% |
| 商店 | 75% |
