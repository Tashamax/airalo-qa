import pytest


def pytest_report_teststatus(report, config):
    if report.when == "call":
        if report.passed:
            return report.outcome, "✅", "PASSED"
        elif report.failed:
            return report.outcome, "❌", "FAILED"
        elif report.skipped:
            return report.outcome, "⚠️", "SKIPPED"


def pytest_collection_modifyitems(items):
    for item in items:
        parts = item.nodeid.split("::")
        class_name = parts[-2] if len(parts) > 2 else ""
        test_name = parts[-1].replace("test_", "").replace("_", " ")
        item._nodeid = f"{class_name} → {test_name}"
