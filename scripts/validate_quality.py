from __future__ import annotations

import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def main() -> None:
	version = _read_app_version()
	_readme_contains_current_version(version)
	_required_apps_do_not_include_hrms()
	_license_metadata_is_aligned()
	_base_dependencies_are_declared()
	_docs_exist()
	_referenced_images_exist()
	_json_files_are_valid()
	_critical_legal_rules_are_present()
	_legal_catalog_is_consistent()
	_localized_product_assets_are_valid()
	_all_text_assets_are_valid_utf8()
	_demo_acceptance_scenarios_are_present()
	print(f"Saudi HR quality checks passed for version {version}")


def _read_app_version() -> str:
	module = ast.parse((ROOT / "saudi_hr" / "__init__.py").read_text(encoding="utf-8"))
	for node in module.body:
		if isinstance(node, ast.Assign):
			for target in node.targets:
				if isinstance(target, ast.Name) and target.id == "__version__":
					return ast.literal_eval(node.value)
	raise AssertionError("__version__ not found")


def _readme_contains_current_version(version: str) -> None:
	text = README.read_text(encoding="utf-8")
	assert f"version-{version}" in text, "README badge does not contain current version"
	assert f"Saudi HR `{version}`" in text, "README verified stack does not contain current version"
	assert f"v{version}" in text, "README changelog does not contain current release heading"


def _required_apps_do_not_include_hrms() -> None:
	hooks = ast.parse((ROOT / "saudi_hr" / "hooks.py").read_text(encoding="utf-8"))
	required_apps = []
	for node in hooks.body:
		if isinstance(node, ast.Assign):
			for target in node.targets:
				if isinstance(target, ast.Name) and target.id == "required_apps":
					required_apps = [str(item).split("/")[-1] for item in ast.literal_eval(node.value)]
	assert "erpnext" in required_apps, "erpnext must remain a required app"
	assert "hrms" not in required_apps, "hrms must not be a required app"


def _license_metadata_is_aligned() -> None:
	hooks = ast.parse((ROOT / "saudi_hr" / "hooks.py").read_text(encoding="utf-8"))
	app_license = None
	for node in hooks.body:
		if isinstance(node, ast.Assign):
			for target in node.targets:
				if isinstance(target, ast.Name) and target.id == "app_license":
					app_license = ast.literal_eval(node.value)
	assert app_license == "GPL-3.0", "Frappe hook license metadata should match README"
	assert (ROOT / "LICENSE").is_file(), "LICENSE file is missing"


def _base_dependencies_are_declared() -> None:
	for relative_path in ("setup.py", "pyproject.toml", "requirements.txt"):
		text = (ROOT / relative_path).read_text(encoding="utf-8")
		assert "openpyxl>=3.1.0" in text, f"openpyxl missing from {relative_path}"
		assert "openlocationcode>=1.0.1" in text, f"openlocationcode missing from {relative_path}"


def _docs_exist() -> None:
	for relative_path in (
		"docs/installation.md",
		"docs/deployment.md",
		"docs/hrms-decoupling.md",
		"docs/visual-tour.md",
		"docs/demo-data.md",
		"docs/LEGAL_COMPLIANCE_MATRIX.md",
		"docs/PRODUCT_COMPLETION_PLAN.md",
		"docs/RELEASE_READINESS.md",
		"docs/ENTERPRISE_PRODUCT_PHASE.md",
		"design-system/MASTER.md",
		"DEPENDENCIES.md",
	):
		assert (ROOT / relative_path).is_file(), f"{relative_path} is missing"


def _referenced_images_exist() -> None:
	text = "\n".join(path.read_text(encoding="utf-8") for path in [README, ROOT / "docs" / "visual-tour.md"])
	references = sorted(set(re.findall(r"docs/images/[^\"\\) ]+\.(?:png|gif)|images/[^\"\\) ]+\.(?:png|gif)", text)))
	assert references, "No image references found"
	for reference in references:
		path = ROOT / reference
		if reference.startswith("images/"):
			path = ROOT / "docs" / reference
		assert path.is_file(), f"{reference} is missing"
		assert path.stat().st_size > 0, f"{reference} is empty"
		if path.suffix == ".png":
			assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), f"{reference} is not a PNG"
		if path.suffix == ".gif":
			assert path.read_bytes().startswith((b"GIF87a", b"GIF89a")), f"{reference} is not a GIF"


def _json_files_are_valid() -> None:
	for path in ROOT.rglob("*.json"):
		json.loads(path.read_text(encoding="utf-8"))


def _critical_legal_rules_are_present() -> None:
	maternity = (ROOT / "saudi_hr" / "saudi_hr" / "doctype" / "maternity_paternity_leave" / "maternity_paternity_leave.py").read_text(encoding="utf-8")
	overtime = (ROOT / "saudi_hr" / "saudi_hr" / "doctype" / "overtime_request" / "overtime_request.py").read_text(encoding="utf-8")
	sick_leave = (ROOT / "saudi_hr" / "saudi_hr" / "doctype" / "saudi_sick_leave" / "saudi_sick_leave.py").read_text(encoding="utf-8")
	controls = (ROOT / "saudi_hr" / "saudi_hr" / "compliance_controls.py").read_text(encoding="utf-8")
	assert 'MATERNITY_LEAVE_TYPE: 84' in maternity, "Maternity entitlement must remain 84 days"
	assert 'actual_hourly_rate + overtime_premium_hourly' in overtime, "Article 107 overtime formula is missing"
	assert 'basic_hourly_rate * 0.5' in overtime, "Article 107 basic-wage premium is missing"
	assert 'return 7 if termination_initiated_by == "Employer / صاحب العمل" else 14' in controls, "Final-settlement SLA rule is missing"
	assert 'COMPENSATORY_LEAVE_FACTOR = 1.5' in overtime, "Compensatory-leave factor must remain 1.5"
	assert 'ANNUAL_OVERTIME_LIMIT_HOURS = 720' in overtime, "Annual overtime limit must remain 720 hours"
	assert 'calculate_compensatory_leave_exit_payout' in controls, "Unused compensatory-leave exit payout is missing"
	assert 'calculate_sick_leave_cycle' in sick_leave, "Rolling sick-leave benefit cycle is missing"
	assert 'calculate_sick_leave_pay_breakdown' in sick_leave, "Auditable sick-leave pay tiers are missing"
	assert 'Termination is permissible' not in sick_leave, "Sick-leave controls must not recommend automatic termination after 90 days"


def _legal_catalog_is_consistent() -> None:
	text = (ROOT / "saudi_hr" / "saudi_hr" / "legal_rule_catalog.py").read_text(encoding="utf-8")
	rule_ids = re.findall(r'^\s*_rule\("(SHR-[^"]+)"', text, flags=re.MULTILINE)
	matrix_text = (ROOT / "docs" / "LEGAL_COMPLIANCE_MATRIX.md").read_text(encoding="utf-8")
	matrix_ids = re.findall(r"^\| (SHR-[^ ]+) \|", matrix_text, flags=re.MULTILINE)
	required = {
		"SHR-REG-OT-720",
		"SHR-REG-OT-PAY",
		"SHR-REG-OT-LEAVE",
		"SHR-REG-OT-EXIT",
		"SHR-REG-EXIT-7",
		"SHR-REG-EXIT-14",
		"SHR-REG-027",
		"SHR-REG-027-B",
		"SHR-REG-027-C",
		"SHR-REG-MAT",
		"SHR-REG-041",
	}
	assert len(rule_ids) == len(set(rule_ids)), "Legal rule IDs must be unique"
	assert set(rule_ids) == set(matrix_ids), "The runtime legal catalog and documented compliance matrix must contain the same rule IDs"
	assert required.issubset(set(rule_ids)), "One or more critical legal rules are missing from the catalog"


def _localized_product_assets_are_valid() -> None:
	paths = (
		ROOT / "saudi_hr" / "saudi_hr" / "compliance_command_center.py",
		ROOT / "saudi_hr" / "saudi_hr" / "demo_lifecycle.py",
		ROOT / "saudi_hr" / "saudi_hr" / "legal_rule_catalog.py",
		ROOT / "saudi_hr" / "saudi_hr" / "page" / "saudi_compliance_command_center" / "saudi_compliance_command_center.js",
		ROOT / "saudi_hr" / "saudi_hr" / "page" / "professional_hr_hub" / "professional_hr_hub.js",
		ROOT / "saudi_hr" / "saudi_hr" / "enterprise_operations.py",
		ROOT / "saudi_hr" / "saudi_hr" / "page" / "saudi_enterprise_center" / "saudi_enterprise_center.js",
		ROOT / "saudi_hr" / "saudi_hr" / "page" / "saudi_self_service" / "saudi_self_service.js",
		ROOT / "saudi_hr" / "saudi_hr" / "page" / "saudi_hr_legal_guide" / "saudi_hr_legal_guide.js",
		ROOT / "saudi_hr" / "translations" / "ar.csv",
	)
	for path in paths:
		text = path.read_text(encoding="utf-8")
		assert not ({"Ø", "Ù", "Â", "�"} & set(text)), f"Possible Arabic encoding corruption in {path.relative_to(ROOT)}"
		assert any("\u0600" <= character <= "\u06ff" for character in text), f"Arabic content is missing from {path.relative_to(ROOT)}"

	command_center = paths[3].read_text(encoding="utf-8")
	translations = paths[-1].read_text(encoding="utf-8")
	assert 'dir="rtl"' in command_center, "The Arabic command center must render in RTL"
	assert ":focus-visible" in command_center, "The command center must expose keyboard focus"
	assert "prefers-reduced-motion" in command_center, "The command center must respect reduced-motion preferences"
	for page in paths[6:9]:
		page_text = page.read_text(encoding="utf-8")
		assert 'dir="rtl"' in page_text, f"Enterprise page must render in RTL: {page.relative_to(ROOT)}"
		assert ":focus-visible" in page_text, f"Enterprise page must expose keyboard focus: {page.relative_to(ROOT)}"
		assert "prefers-reduced-motion" in page_text, f"Enterprise page must respect reduced motion: {page.relative_to(ROOT)}"
	assert "Termination is permissible per Art. 117" not in translations, "Arabic translations must not recommend automatic termination after 90 sick-leave days"


def _demo_acceptance_scenarios_are_present() -> None:
	text = (ROOT / "saudi_hr" / "saudi_hr" / "demo_lifecycle.py").read_text(encoding="utf-8")
	for marker in (
		"DEMO-FLEX-120",
		"DEMO-FLEX-160",
		"Rejected / مرفوض",
		"DEMO-OVERDUE-EVIDENCE",
		"DEMO-SICK-MIXED-10",
		"unused_compensatory_leave_hours",
		"DEMO:QIWA",
		"DEMO-IBAN-MISSING",
		"2026.1-DEMO",
	):
		assert marker in text, f"Demo acceptance scenario is missing: {marker}"


def _all_text_assets_are_valid_utf8() -> None:
	text_extensions = {".py", ".js", ".json", ".csv", ".md", ".html", ".css", ".txt", ".yml", ".yaml"}
	validator_path = Path(__file__).resolve()
	for path in ROOT.rglob("*"):
		if not path.is_file() or path.suffix.lower() not in text_extensions or path.resolve() == validator_path:
			continue
		try:
			text = path.read_text(encoding="utf-8")
		except UnicodeDecodeError as exc:
			raise AssertionError(f"Text asset is not valid UTF-8: {path.relative_to(ROOT)}") from exc
		assert not ({"Ø", "Ù", "Â", "�"} & set(text)), f"Possible encoding corruption in {path.relative_to(ROOT)}"


if __name__ == "__main__":
	main()
