"""Comprehensive Saudi HR test discovery and execution inside an initialized site.

Frappe's global app test runner creates records for unrelated ERPNext DocTypes
before loading Saudi HR tests. This module deliberately discovers only this
application's tests so the result describes Saudi HR rather than optional core
fixtures installed on a particular site.
"""

from __future__ import annotations

import io
import json
import os
import unittest
from pathlib import Path

import frappe


def _package_root() -> Path:
	return Path(frappe.get_app_path("saudi_hr")).resolve()


def _module_name(path: Path) -> str:
	return ".".join(path.relative_to(_package_root().parent).with_suffix("").parts)


def discover_test_modules(module_pattern: str | None = None) -> list[str]:
	"""Return every Saudi HR ``test_*.py`` module in deterministic order."""
	pattern = (module_pattern or "").strip().lower()
	modules = []
	for path in _package_root().rglob("test_*.py"):
		if "__pycache__" in path.parts:
			continue
		module = _module_name(path)
		if pattern and pattern not in module.lower():
			continue
		modules.append(module)
	return sorted(set(modules))


def _test_identifier(test) -> str:
	try:
		return test.id()
	except Exception:
		return str(test)


def run_comprehensive_test_suite(
	module_pattern: str | None = None,
	verbosity: int = 1,
	include_details: int = 0,
) -> dict:
	"""Execute every discovered Saudi HR test module and return a stable result."""
	modules = discover_test_modules(module_pattern or os.environ.get("SAUDI_HR_TEST_PATTERN"))
	loader = unittest.TestLoader()
	suite = unittest.TestSuite()
	for module in modules:
		suite.addTests(loader.loadTestsFromName(module))

	stream = io.StringIO()
	previous_in_test = getattr(frappe.flags, "in_test", False)
	frappe.flags.in_test = True
	try:
		result = unittest.TextTestRunner(
			stream=stream,
			verbosity=max(0, min(int(verbosity or 1), 2)),
			failfast=False,
		).run(suite)
	finally:
		frappe.flags.in_test = previous_in_test

	problems = [
		{"kind": "failure", "id": _test_identifier(test), "traceback": traceback_text}
		for test, traceback_text in result.failures
	] + [
		{"kind": "error", "id": _test_identifier(test), "traceback": traceback_text}
		for test, traceback_text in result.errors
	]
	return {
		"modules": modules,
		"module_count": len(modules),
		"tests_run": result.testsRun,
		"failures": len(result.failures),
		"errors": len(result.errors),
		"skipped": len(result.skipped),
		"expected_failures": len(result.expectedFailures),
		"unexpected_successes": len(result.unexpectedSuccesses),
		"failure_ids": [_test_identifier(test) for test, _ in result.failures],
		"error_ids": [_test_identifier(test) for test, _ in result.errors],
		"problems": problems,
		"all_passed": result.wasSuccessful(),
		"details": stream.getvalue() if int(include_details or 0) else "",
	}


def get_coverage_inventory() -> dict:
	"""Inventory executable surfaces and direct test-file coverage."""
	package_root = _package_root()
	doctype_root = package_root / "saudi_hr" / "doctype"
	parent_doctypes = []
	child_doctypes = []
	for folder in sorted(path for path in doctype_root.iterdir() if path.is_dir()):
		definition = folder / f"{folder.name}.json"
		if not definition.exists():
			continue
		try:
			payload = json.loads(definition.read_text(encoding="utf-8"))
		except (OSError, json.JSONDecodeError):
			continue
		item = {
			"name": payload.get("name") or folder.name,
			"folder": folder.name,
			"controller": (folder / f"{folder.name}.py").exists(),
			"direct_test_file": (folder / f"test_{folder.name}.py").exists(),
			"submittable": bool(payload.get("is_submittable")),
		}
		(child_doctypes if payload.get("istable") else parent_doctypes).append(item)

	workflow_root = package_root / "saudi_hr" / "workflow"
	page_root = package_root / "saudi_hr" / "page"
	report_root = package_root / "saudi_hr" / "report"
	workflows = sorted(path.name for path in workflow_root.iterdir() if path.is_dir())
	pages = sorted(path.name for path in page_root.iterdir() if path.is_dir() and path.name != "__pycache__")
	reports = sorted(path.name for path in report_root.iterdir() if path.is_dir() and path.name != "__pycache__")
	test_modules = discover_test_modules()
	return {
		"parent_doctypes": parent_doctypes,
		"child_doctypes": child_doctypes,
		"workflows": workflows,
		"pages": pages,
		"reports": reports,
		"test_modules": test_modules,
		"counts": {
			"parent_doctypes": len(parent_doctypes),
			"child_doctypes": len(child_doctypes),
			"parent_doctypes_with_direct_tests": sum(1 for item in parent_doctypes if item["direct_test_file"]),
			"parent_doctypes_without_direct_tests": sum(1 for item in parent_doctypes if not item["direct_test_file"]),
			"workflows": len(workflows),
			"pages": len(pages),
			"reports": len(reports),
			"test_modules": len(test_modules),
		},
	}
