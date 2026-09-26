# 变更记录

记录本项目的显著变更。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。
项目尚未发布语义化版本号，变更按日期归档。

## [Unreleased]

### 新增

- 静态检查：ruff（lint）+ mypy（类型检查），配置集中在 `pyproject.toml`
- 提交前钩子 `.pre-commit-config.yaml`：文件末尾换行、行尾空格、YAML/TOML 语法、ruff check
- 任务入口 `Makefile`：`install` / `test` / `perf` / `lint` / `fmt` / `report`
- 容器化 `Dockerfile` + `.dockerignore`
- README 补充 CI、Python 版本、License 三个 badge

### 变更

- CI 新增 `lint` 作业，与本地共用 `make lint` 的同一套命令
- 覆盖率数字随 `mock_server.py` 行号变化同步（语句 91/96，未覆盖行 150-152 / 198 / 202）
- 依赖锁定快照重新采集，覆盖 51 个包

## [2026-09-26]

### 新增

- GitHub Actions CI：`test` 作业跑功能 / 白盒 / 缺陷用例并统计覆盖率，`performance` 作业单独跑压测且 `continue-on-error: true`
- `LICENSE`（MIT）、`.python-version`（3.12.10）、`requirements.lock` 依赖锁定快照
- `server_config.py`：`HOST` / `PORT` / `BASE_URL` 的单一来源，支持 `MOCK_HOST` / `MOCK_PORT` 环境变量覆盖
- 依赖补充 `Pillow` 与 `sniffio`

### 修复

- `conftest.py`：检测到目标端口已有服务在响应时不再静默复用，改为 fail-fast 并提示处理方式；确需复用需显式设置 `MOCK_REUSE_EXISTING=1`。此前静默复用会让测试跑在旧代码或脏状态上，产出假绿
- 截图脚本：输出目录改为命令行参数 / 环境变量 / 项目内默认目录三级优先级；字体改为跨平台候选表并支持降级；裸 `except` 改为捕获具体异常类型
- README 运行章节命令失效（改用 venv 解释器）

### 变更

- 压测弃用 `TestClient`，改为 `httpx.AsyncClient` 对真实 Uvicorn 进程发起 HTTP 请求
- 吞吐量改按墙钟时间计算（`total_requests / wall_elapsed`），弃用单请求耗时倒数
- 6 处植入缺陷统一登记为 `xfail(strict=True)` 并加 `bug` 标记；缺陷被修复后用例会转为 XPASS 导致失败，强制移除过期标记
- 测试报告与截图产物加入 `.gitignore`

## [2026-09-08]

### 新增

- 首个版本：FastAPI Mock Server（8 个端点，内置 BUG-001 ~ BUG-006）+ 51 个 pytest 用例（功能测试 / 白盒分支测试 / 并发性能压测）