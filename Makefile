# 常用命令入口。先激活虚拟环境，或显式传入解释器：make test PYTHON=.venv/bin/python
PYTHON ?= python

.PHONY: help install test perf lint fmt report

help:
	@echo install  安装依赖
	@echo test     功能 / 白盒 / 缺陷测试，带覆盖率，不含压测
	@echo perf     并发压测，勿加 --cov，覆盖率插桩会拖慢同进程的压测客户端
	@echo lint     ruff + mypy 静态检查
	@echo fmt      ruff 格式化，既有代码尚未整体格式化
	@echo report   运行测试并生成报告与截图

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m pytest tests/ --ignore=tests/test_performance.py \
		--cov=mock_server --cov-branch --cov-report=term-missing

perf:
	$(PYTHON) -m pytest tests/test_performance.py -v -s

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m mypy

fmt:
	$(PYTHON) -m ruff format .

report:
	$(PYTHON) run_tests.py
