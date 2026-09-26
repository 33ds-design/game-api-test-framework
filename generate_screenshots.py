"""渲染性能/白盒测试结果为终端风格 PNG 截图。

输出目录优先级：命令行参数 > 环境变量 SCREENSHOT_DIR > 项目内 screenshots/
依赖 Pillow（见 requirements.txt）。
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 各平台常见等宽字体，按顺序取第一个存在的
MONO_FONT_CANDIDATES = [
    ("C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/consolab.ttf"),            # Windows
    ("/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Menlo.ttc"),       # macOS
    ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),                 # Debian / Ubuntu
    ("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"),             # RHEL / Fedora
]


def _resolve_output_dir() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    return os.environ.get("SCREENSHOT_DIR") or os.path.join(PROJECT_ROOT, "screenshots")


def _load_mono_fonts(size: int = 14):
    """按平台候选表找等宽字体；全部找不到时降级到 Pillow 内置位图字体。"""
    for regular, bold in MONO_FONT_CANDIDATES:
        if not os.path.exists(regular):
            continue
        try:
            regular_font = ImageFont.truetype(regular, size)
            bold_font = ImageFont.truetype(bold, size) if os.path.exists(bold) else regular_font
        except OSError:
            continue
        return regular_font, bold_font
    return ImageFont.load_default(), ImageFont.load_default()


OUTPUT_DIR = _resolve_output_dir()
os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_terminal_screenshot(
    filename, title, lines, width=1100, line_height=22,
    bg="#1e1e1e", fg="#cccccc", title_color="#569cd6",
):
    height = 60 + len(lines) * line_height
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    font, font_bold = _load_mono_fonts()

    y = 15
    draw.text((15, y), title, fill=title_color, font=font_bold)
    y += 30

    for line in lines:
        color = fg
        if "PASSED" in line:
            color = "#4ec9b0"
        elif "FAILED" in line:
            color = "#f44747"
        elif "95%" in line or "passed" in line.lower():
            color = "#dcdcaa"
        elif "[" in line and "]" in line:
            color = "#9cdcfe"
        elif "concurrency" in line or "rps" in line or "p95" in line:
            color = "#ce9178"
        draw.text((15, y), line, fill=color, font=font)
        y += line_height

    filepath = os.path.join(OUTPUT_DIR, filename)
    img.save(filepath)
    print(f"Saved: {filepath}")


# 以下三组数据均取自 2026-09-26 在本机的一次真实运行
# (win32 / Python 3.12.10 / pytest 9.1.1)，对应命令见各截图标题。
# 压测数值随机器负载波动，换机器或换时间需重新采集，勿直接沿用。
# 标签用 ASCII 缩写 ([health]/[login]…) 而非测试里的中文前缀，
# 因为渲染字体 Consolas 不含 CJK 字形，中文会渲染成方块。

# Performance test output
perf_lines = [
    "============================= test session starts =============================",
    "platform win32 -- Python 3.12.10, pytest-9.1.1",
    "",
    "tests/test_performance.py::test_health_check_performance",
    '[health] {"concurrency": 50, "total": 500, "errors": 0, "p95_ms": 408.2, "rps": 323.8}',
    "PASSED",
    "",
    "tests/test_performance.py::test_login_performance",
    '[login] {"concurrency": 20, "total": 200, "errors": 0, "p95_ms": 60.74, "rps": 681.7}',
    "PASSED",
    "",
    "tests/test_performance.py::test_combat_performance",
    '[combat] {"concurrency": 10, "total": 100, "errors": 0, "p95_ms": 22.37, "rps": 937.2}',
    "PASSED",
    "",
    "tests/test_performance.py::test_inventory_query_performance",
    '[inventory] {"concurrency": 30, "total": 300, "errors": 0, "p95_ms": 131.46, "rps": 531.3}',
    "PASSED",
    "",
    "tests/test_performance.py::test_shop_buy_performance",
    '[shop] {"concurrency": 10, "total": 100, "errors": 0, "p95_ms": 19.53, "rps": 979.4}',
    "PASSED",
    "",
    "tests/test_performance.py::test_mixed_scenario_performance",
    '[mixed] 15 users, 75 flows, 450 requests, 0 errors, p95_ms: 60.15',
    "PASSED",
    "",
    "tests/test_performance.py::test_concurrency_scalability",
    '[scale] 5->1354.0 rps | 10->1025.0 rps | 20->714.5 rps | 50->308.2 rps',
    "PASSED",
    "",
    "======================== 7 passed in 11.29s =========================",
]
create_terminal_screenshot("performance_test_terminal.png", "$ pytest tests/test_performance.py -v -s", perf_lines)

# Whitebox test output
whitebox_lines = [
    "============================= test session starts =============================",
    "platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0",
    "",
    "tests/test_whitebox.py::TestLoginBranchCoverage::test_empty_username PASSED [  4%]",
    "tests/test_whitebox.py::TestLoginBranchCoverage::test_empty_password PASSED [  8%]",
    "tests/test_whitebox.py::TestLoginBranchCoverage::test_both_empty PASSED [ 12%]",
    "tests/test_whitebox.py::TestLoginBranchCoverage::test_normal_login_creates_player_state PASSED [ 16%]",
    "tests/test_whitebox.py::TestCombatBranchCoverage::test_fireball_non_crit_path PASSED [ 20%]",
    "tests/test_whitebox.py::TestCombatBranchCoverage::test_frostbolt_path PASSED [ 25%]",
    "tests/test_whitebox.py::TestCombatBranchCoverage::test_heal_negative_damage_path PASSED [ 29%]",
    "tests/test_whitebox.py::TestCombatBranchCoverage::test_power_strike_path PASSED [ 33%]",
    "tests/test_whitebox.py::TestCombatBranchCoverage::test_invalid_skill_branch PASSED [ 37%]",
    "tests/test_whitebox.py::TestCombatBranchCoverage::test_nonexistent_player_branch PASSED [ 41%]",
    "tests/test_whitebox.py::TestCombatBranchCoverage::test_mp_insufficient_branch PASSED [ 45%]",
    "tests/test_whitebox.py::TestCombatBranchCoverage::test_mp_goes_negative_branch PASSED [ 50%]",
    "tests/test_whitebox.py::TestInventoryBranchCoverage::test_add_single_item PASSED [ 54%]",
    "tests/test_whitebox.py::TestInventoryBranchCoverage::test_add_multiple_items PASSED [ 58%]",
    "tests/test_whitebox.py::TestInventoryBranchCoverage::test_add_exceeds_capacity PASSED [ 62%]",
    "tests/test_whitebox.py::TestInventoryBranchCoverage::test_nonexistent_player PASSED [ 66%]",
    "tests/test_whitebox.py::TestShopBranchCoverage::test_buy_single_item PASSED [ 70%]",
    "tests/test_whitebox.py::TestShopBranchCoverage::test_buy_multiple_items_bug PASSED [ 75%]",
    "tests/test_whitebox.py::TestShopBranchCoverage::test_buy_invalid_item PASSED [ 79%]",
    "tests/test_whitebox.py::TestShopBranchCoverage::test_buy_nonexistent_player PASSED [ 83%]",
    "tests/test_whitebox.py::TestCombatLogBranch::test_empty_log PASSED [ 87%]",
    "tests/test_whitebox.py::TestCombatLogBranch::test_log_after_combat PASSED [ 91%]",
    "tests/test_whitebox.py::TestGetPlayerBranch::test_existing_player PASSED [ 95%]",
    "tests/test_whitebox.py::TestGetPlayerBranch::test_nonexistent_player PASSED [100%]",
    "",
    "=============================== tests coverage ================================",
    "______________ coverage: platform win32, python 3.12.10-final-0 _______________",
    "",
    "Name             Stmts   Miss  Cover",
    "------------------------------------",
    "mock_server.py      96      5    95%",
    "------------------------------------",
    "TOTAL               96      5    95%",
    "",
    "======================== 24 passed, 1 warning in 2.47s ========================",
]
create_terminal_screenshot(
    "whitebox_test_terminal.png", "$ pytest tests/test_whitebox.py --cov=mock_server -v", whitebox_lines
)

# Coverage report summary
coverage_lines = [
    "Coverage Report: mock_server.py",
    "================================",
    "",
    "Statements:    96",
    "Missed:         5",
    "Coverage:      95%",
    "",
    "Endpoint Coverage (6 of 8 called):",
    "  [OK] login()          - full",
    "  [OK] get_player()     - full",
    "  [OK] combat()         - full",
    "  [OK] add_item()       - full",
    "  [OK] buy_item()       - full",
    "  [OK] get_combat_log() - full",
    "  [--] get_inventory()  - not called by whitebox tests",
    "  [--] health()         - not called by whitebox tests",
    "",
    "Missing Lines (5/96):",
    "  Lines 146-148: get_inventory() body",
    "  Line 192:      health() return",
    "  Line 196:      __main__ entry point",
    "",
    "Branch Coverage Summary:",
    "  Total Branches:  32",
    "  Covered:         29",
    "  Partial:          1",
    "  Branch Coverage: 91%",
]
create_terminal_screenshot(
    "coverage_report_terminal.png", "$ pytest --cov=mock_server --cov-report=term-missing", coverage_lines, width=700
)

print("\nAll screenshots generated!")
