from __future__ import annotations

import ast
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
	print(f"Saudi HR quality checks passed for version {version}")


def _read_app_version() -> str:
	module = ast.parse((ROOT / "saudi_hr" / "__init__.py").read_text())
	for node in module.body:
		if isinstance(node, ast.Assign):
			for target in node.targets:
				if isinstance(target, ast.Name) and target.id == "__version__":
					return ast.literal_eval(node.value)
	raise AssertionError("__version__ not found")


def _readme_contains_current_version(version: str) -> None:
	text = README.read_text()
	assert f"version-{version}" in text, "README badge does not contain current version"
	assert f"Saudi HR `{version}`" in text, "README verified stack does not contain current version"
	assert f"v{version}" in text, "README changelog does not contain current release heading"


def _required_apps_do_not_include_hrms() -> None:
	hooks = ast.parse((ROOT / "saudi_hr" / "hooks.py").read_text())
	required_apps = []
	for node in hooks.body:
		if isinstance(node, ast.Assign):
			for target in node.targets:
				if isinstance(target, ast.Name) and target.id == "required_apps":
					required_apps = [str(item).split("/")[-1] for item in ast.literal_eval(node.value)]
	assert "erpnext" in required_apps, "erpnext must remain a required app"
	assert "hrms" not in required_apps, "hrms must not be a required app"


def _license_metadata_is_aligned() -> None:
	hooks = ast.parse((ROOT / "saudi_hr" / "hooks.py").read_text())
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
		text = (ROOT / relative_path).read_text()
		assert "openpyxl>=3.1.0" in text, f"openpyxl missing from {relative_path}"
		assert "openlocationcode>=1.0.1" in text, f"openlocationcode missing from {relative_path}"


def _docs_exist() -> None:
	for relative_path in (
		"docs/installation.md",
		"docs/deployment.md",
		"docs/hrms-decoupling.md",
		"docs/visual-tour.md",
		"docs/demo-data.md",
		"DEPENDENCIES.md",
	):
		assert (ROOT / relative_path).is_file(), f"{relative_path} is missing"


def _referenced_images_exist() -> None:
	text = "\n".join(path.read_text() for path in [README, ROOT / "docs" / "visual-tour.md"])
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


if __name__ == "__main__":
	main()
