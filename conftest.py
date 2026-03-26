import pytest


def pytest_report_teststatus(report, config):
    if report.when == "call":
        if report.passed:
            return report.outcome, "✅", "PASSED"
        elif report.failed:
            return report.outcome, "❌", "FAILED"
        elif report.skipped:
            return report.outcome, "⚠️", "SKIPPED"
