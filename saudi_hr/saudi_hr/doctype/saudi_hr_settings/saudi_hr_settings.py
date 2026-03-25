from __future__ import annotations

from io import BytesIO

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.file_manager import save_file
from openpyxl import Workbook, load_workbook


class SaudiHRSettings(Document):
	pass


def _assert_settings_access():
	frappe.only_for(("System Manager", "HR Manager"))


def _get_employee_directory_rows():
	return frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		fields=["name", "employee_name", "user_id", "branch", "department", "company"],
		order_by="employee_name asc, name asc",
	)


def _sync_directory_table():
	settings = frappe.get_single("Saudi HR Settings")
	settings.set("branch_employee_directory", [])
	for row in _get_employee_directory_rows():
		settings.append(
			"branch_employee_directory",
			{
				"employee": row.name,
				"employee_name": row.employee_name,
				"user_id": row.user_id,
				"branch": row.branch,
				"department": row.department,
				"company": row.company,
			},
		)
	settings.save(ignore_permissions=True)
	frappe.db.commit()
	return settings


def _build_template_file():
	workbook = Workbook()
	assignments = workbook.active
	assignments.title = "Employees"
	assignments.append(["employee_id", "employee_name", "user_id", "current_branch", "target_branch"])
	for row in _get_employee_directory_rows():
		assignments.append([row.name, row.employee_name, row.user_id, row.branch or "", row.branch or ""])

	branches_sheet = workbook.create_sheet("Branches")
	branches_sheet.append(["branch_name"])
	for branch_name in frappe.get_all("Branch", fields=["name"], order_by="name asc"):
		branches_sheet.append([branch_name.name])

	for sheet in workbook.worksheets:
		sheet.freeze_panes = "A2"

	buffer = BytesIO()
	workbook.save(buffer)
	buffer.seek(0)
	return buffer.getvalue()


def _normalize_header(value):
	return str(value or "").strip().lower().replace(" ", "_")


def _get_file_bytes(file_url: str) -> bytes:
	file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not file_name:
		frappe.throw(_("Unable to find the uploaded Excel file."))
	file_doc = frappe.get_doc("File", file_name)
	return file_doc.get_content()


def _ensure_branch(branch_name: str) -> str:
	branch_name = (branch_name or "").strip()
	if not branch_name:
		return ""
	if not frappe.db.exists("Branch", branch_name):
		frappe.get_doc({"doctype": "Branch", "branch": branch_name}).insert(ignore_permissions=True)
	return branch_name


def _find_employee_for_import(employee_id: str, user_id: str, employee_name: str):
	if employee_id and frappe.db.exists("Employee", employee_id):
		return employee_id
	if user_id:
		name = frappe.db.get_value("Employee", {"user_id": user_id}, "name")
		if name:
			return name
	if employee_name:
		name = frappe.db.get_value("Employee", {"employee_name": employee_name}, "name")
		if name:
			return name
	return None


@frappe.whitelist()
def sync_branch_employee_directory():
	_assert_settings_access()
	settings = _sync_directory_table()
	return {"row_count": len(settings.branch_employee_directory or [])}


@frappe.whitelist()
def download_employee_branch_template():
	_assert_settings_access()
	file_doc = save_file(
		"employee-branch-template.xlsx",
		_build_template_file(),
		"Saudi HR Settings",
		"Saudi HR Settings",
		is_private=0,
	)
	return {"file_url": file_doc.file_url, "file_name": file_doc.file_name}


@frappe.whitelist()
def import_employee_branch_template(file_url: str | None = None):
	_assert_settings_access()
	if not file_url:
		frappe.throw(_("Attach the Excel template file first."))

	content = _get_file_bytes(file_url)
	workbook = load_workbook(BytesIO(content), data_only=True)
	worksheet = workbook[workbook.sheetnames[0]]
	rows = list(worksheet.iter_rows(values_only=True))
	if not rows:
		frappe.throw(_("The uploaded Excel file is empty."))

	headers = [_normalize_header(value) for value in rows[0]]
	updated_count = 0
	created_branch_count = 0
	skipped_count = 0
	errors = []

	for row in rows[1:]:
		payload = {headers[index]: row[index] for index in range(min(len(headers), len(row)))}
		employee_id = str(payload.get("employee_id") or "").strip()
		user_id = str(payload.get("user_id") or "").strip()
		employee_name = str(payload.get("employee_name") or "").strip()
		branch_name = str(payload.get("target_branch") or payload.get("branch") or payload.get("current_branch") or "").strip()

		if not any([employee_id, user_id, employee_name, branch_name]):
			continue
		if not branch_name:
			skipped_count += 1
			continue

		employee = _find_employee_for_import(employee_id, user_id, employee_name)
		if not employee:
			errors.append(_("Employee not found: {0}").format(employee_id or user_id or employee_name))
			continue

		if not frappe.db.exists("Branch", branch_name):
			_ensure_branch(branch_name)
			created_branch_count += 1

		current_branch = frappe.db.get_value("Employee", employee, "branch") or ""
		if current_branch == branch_name:
			skipped_count += 1
			continue

		frappe.db.set_value("Employee", employee, "branch", branch_name, update_modified=True)
		updated_count += 1

	frappe.db.commit()
	_sync_directory_table()
	return {
		"updated_count": updated_count,
		"created_branch_count": created_branch_count,
		"skipped_count": skipped_count,
		"errors": errors[:20],
	}
