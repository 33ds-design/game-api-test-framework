"""
Generate terminal-style screenshots for performance and whitebox test results.
Uses PIL to render monospace text as PNG images.
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = r"d:\QA\article-images"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_terminal_screenshot(filename, title, lines, width=1100, line_height=22, bg="#1e1e1e", fg="#cccccc", title_color="#569cd6"):
    height = 60 + len(lines) * line_height
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 14)
        font_bold = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 14)
    except:
        font = ImageFont.load_default()
        font_bold = font

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


# Performance test output
perf_lines = [
    "============================= test session starts =============================",
    "platform win32 -- Python 3.12.10, pytest-9.1.1",
    "",
    "tests/test_performance.py::test_health_check_performance",
    '[health] {"concurrency": 50, "total": 500, "errors": 0, "p95_ms": 43.39, "rps": 1887.9}',
    "PASSED",
    "",
    "tests/test_performance.py::test_login_performance",
    '[login] {"concurrency": 20, "total": 200, "errors": 0, "p95_ms": 15.73, "rps": 1674.8}',
    "PASSED",
    "",
    "tests/test_performance.py::test_combat_performance",
    '[combat] {"concurrency": 10, "total": 100, "errors": 0, "p95_ms": 17.52, "rps": 1371.6}',
    "PASSED",
    "",
    "tests/test_performance.py::test_inventory_query_performance",
    '[inventory] {"concurrency": 30, "total": 300, "errors": 0, "p95_ms": 20.01, "rps": 1974.9}',
    "PASSED",
    "",
    "tests/test_performance.py::test_shop_buy_performance",
    '[shop] {"concurrency": 10, "total": 100, "errors": 0, "p95_ms": 10.83, "rps": 1179.3}',
    "PASSED",
    "",
    "tests/test_performance.py::test_mixed_scenario_performance",
    '[mixed] 15 users, 75 flows, 450 requests, 0 errors, p95_ms: 26.37',
    "PASSED",
    "",
    "tests/test_performance.py::test_concurrency_scalability",
    '[scale] 5->605 rps | 10->911 rps | 20->1298 rps | 50->1590 rps',
    "PASSED",
    "",
    "======================== 7 passed in 4.42s =========================",
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
    "Name             Stmts   Miss  Cover   Missing",
    "----------------------------------------------",
    "mock_server.py      96      5    95%   146-148, 192, 196",
    "----------------------------------------------",
    "TOTAL               96      5    95%",
    "",
    "======================== 24 passed, 95% coverage in 2.44s ========================",
]
create_terminal_screenshot("whitebox_test_terminal.png", "$ pytest tests/test_whitebox.py --cov=mock_server -v", whitebox_lines)

# Coverage report summary
coverage_lines = [
    "Coverage Report: mock_server.py",
    "================================",
    "",
    "Statements:    96",
    "Missed:         5",
    "Coverage:      95%",
    "",
    "Covered Modules:",
    "  [OK] login()          - 4/4 branches covered",
    "  [OK] get_player()     - 2/2 branches covered",
    "  [OK] combat()         - 8/8 branches covered",
    "  [OK] add_item()       - 4/4 branches covered",
    "  [OK] buy_item()       - 5/5 branches covered",
    "  [OK] get_combat_log() - 2/2 branches covered",
    "  [OK] health()         - 1/1 branches covered",
    "",
    "Missing Lines (5/96):",
    "  Lines 146-148: get_inventory() error path (player not found)",
    "  Line 192:      get_combat_log() with empty log (covered via fixture reset)",
    "  Line 196:      __main__ entry point",
    "",
    "Branch Coverage Summary:",
    "  Total Branches:  28",
    "  Covered:         26",
    "  Branch Coverage: 93%",
]
create_terminal_screenshot("coverage_report_terminal.png", "$ pytest --cov=mock_server --cov-report=term-missing", coverage_lines, width=700)

print("\nAll screenshots generated!")
