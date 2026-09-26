"""
Test Runner — 运行全部测试并生成报告
"""
import os
import subprocess
import sys

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short",
         "--html=test-report.html", "--self-contained-html",
         "--json-report", "--json-report-file=test-results.json"],
        capture_output=False
    )
    sys.exit(result.returncode)
