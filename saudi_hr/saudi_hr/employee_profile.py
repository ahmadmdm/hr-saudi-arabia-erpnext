from __future__ import annotations

from collections.abc import Iterable

import frappe
from frappe import _
from frappe.utils import date_diff, flt, get_first_day, getdate, now_datetime, nowdate

from saudi_hr.saudi_hr.utils import (
	can_access_complete_employee_file,
	get_annual_leave_balance,
	get_employee_nationality,
	is_saudi_nationality,
)


PROFILE_SCHEMA_VERSION = "2026.1"
EXPIRY_WARNING_DAYS = 60


def _as_date(value):
	return str(value) if value else None


def _as_datetime(value):
	return str(value) if value else None


def _doctype_exists(doctype: str) -> bool:
	return bool(frappe.db.exists("DocType", doctype))


def _can_read(doctype: str) -> bool:
	return _doctype_exists(doctype) and bool(frappe.has_permission(doctype, "read"))


def _available_fields(doctype: str, requested: Iterable[str]) -> list[str]:
	if not _doctype_exists(doctype):
		return []
	meta = frappe.get_meta(doctype)
	return [fieldname for fieldname in requested if fieldname == "name" or meta.has_field(fieldname)]


def _visible_rows(
	doctype: str,
	filters: dict,
	fields: Iterable[str],
	*,
	order_by: str = "modified desc",
	limit: int = 20,
) -> list[frappe._dict]:
	if not _can_read(doctype):
		return []
	available = _available_fields(doctype, fields)
	if not available:
		return []
	return frappe.get_list(
		doctype,
		filters=filters,
		fields=available,
		order_by=order_by,
		limit_page_length=limit,
	)


def _first_visible(
	doctype: str,
	filters: dict,
	fields: Iterable[str],
	*,
	order_by: str = "modified desc",
) -> frappe._dict | None:
	rows = _visible_rows(doctype, filters, fields, order_by=order_by, limit=1)
	return rows[0] if rows else None


def _days_remaining(value, reference_date=None) -> int | None:
	if not value:
		return None
	reference = getdate(reference_date or nowdate())
	return date_diff(getdate(value), reference)


def _expiry_state(value, reference_date=None) -> str:
	remaining = _days_remaining(value, reference_date)
	if remaining is None:
		return "missing"
	if remaining < 0:
		return "expired"
	if remaining <= EXPIRY_WARNING_DAYS:
		return "expiring"
	return "valid"


def _check(code: str, status: str, weight: int, detail=None, route=None) -> dict:
	return {
		"code": code,
		"status": status,
		"weight": weight,
		"detail": detail,
		"route": route,
	}


def calculate_employee_readiness(context: dict) -> dict:
	"""Calculate an operational data-readiness score, not a legal-compliance opinion."""
	employee = context.get("employee") or {}
	visibility = context.get("visibility") or {}
	contract = context.get("contract")
	permit = context.get("permit")
	attendance_setup = context.get("attendance_setup") or {}
	leave = context.get("leave") or {}
	nationality = context.get("nationality")

	missing_profile = [
		fieldname
		for fieldname in ("department", "designation", "branch")
		if not employee.get(fieldname)
	]
	if not (employee.get("company_email") or employee.get("personal_email") or employee.get("cell_number")):
		missing_profile.append("contact")

	checks = [
		_check(
			"employment_status",
			"complete" if employee.get("status") == "Active" else "action",
			10,
			employee.get("status"),
			["Form", "Employee", employee.get("name")],
		),
		_check(
			"profile_details",
			"complete" if not missing_profile else ("warning" if len(missing_profile) <= 2 else "action"),
			15,
			missing_profile,
			["Form", "Employee", employee.get("name")],
		),
		_check(
			"user_access",
			"complete" if employee.get("user_id") and context.get("user_enabled") else "action",
			10,
			employee.get("user_id"),
			["Form", "Employee", employee.get("name")],
		),
	]

	if not visibility.get("contract", False):
		checks.append(_check("contract", "hidden", 20))
	elif not contract:
		checks.append(
			_check(
				"contract",
				"action",
				20,
				None,
				["new", "Saudi Employment Contract", employee.get("name")],
			)
		)
	else:
		contract_state = _expiry_state(contract.get("end_date"))
		status = "complete"
		if contract_state == "expired":
			status = "action"
		elif contract_state == "expiring":
			status = "warning"
		checks.append(
			_check(
				"contract",
				status,
				20,
				{
					"name": contract.get("name"),
					"end_date": _as_date(contract.get("end_date")),
					"days_remaining": _days_remaining(contract.get("end_date")),
				},
				["Form", "Saudi Employment Contract", contract.get("name")],
			)
		)

	if not visibility.get("leave", True):
		checks.append(_check("leave_policy", "hidden", 15))
	else:
		leave_status = "complete" if leave.get("assignment") else "warning"
		checks.append(
			_check(
				"leave_policy",
				leave_status,
				15,
				{
					"policy": leave.get("policy_name"),
					"source_type": leave.get("source_type"),
				},
				["List", "Saudi Leave Policy Assignment"],
			)
		)

	has_location = bool(attendance_setup.get("location"))
	has_shift = bool(attendance_setup.get("shift_type"))
	attendance_status = "complete" if has_location and has_shift else ("warning" if has_location or has_shift else "action")
	if not visibility.get("attendance_setup", True):
		checks.append(_check("attendance_setup", "hidden", 15))
	else:
		checks.append(
			_check(
				"attendance_setup",
				attendance_status,
				15,
				attendance_setup,
				["List", "Saudi Shift Assignment"],
			)
		)

	if is_saudi_nationality(nationality):
		checks.append(_check("permit", "not_applicable", 15, nationality))
	elif not visibility.get("permit", False):
		checks.append(_check("permit", "hidden", 15))
	elif not permit:
		checks.append(
			_check(
				"permit",
				"action",
				15,
				None,
				["new", "Work Permit Iqama", employee.get("name")],
			)
		)
	else:
		iqama_state = _expiry_state(permit.get("iqama_expiry_date"))
		work_permit_state = _expiry_state(permit.get("work_permit_expiry_date"))
		if "expired" in {iqama_state, work_permit_state}:
			permit_status = "action"
		elif "expiring" in {iqama_state, work_permit_state} or "missing" in {
			iqama_state,
			work_permit_state,
		}:
			permit_status = "warning"
		else:
			permit_status = "complete"
		checks.append(
			_check(
				"permit",
				permit_status,
				15,
				{
					"name": permit.get("name"),
					"iqama_days_remaining": _days_remaining(permit.get("iqama_expiry_date")),
					"work_permit_days_remaining": _days_remaining(
						permit.get("work_permit_expiry_date")
					),
				},
				["Form", "Work Permit Iqama", permit.get("name")],
			)
		)

	applicable = [row for row in checks if row["status"] not in {"hidden", "not_applicable"}]
	possible = sum(row["weight"] for row in applicable)
	earned = sum(
		row["weight"] if row["status"] == "complete" else row["weight"] * 0.5
		for row in applicable
		if row["status"] in {"complete", "warning"}
	)
	score = round((earned / possible) * 100) if possible else 0
	state = "ready" if score >= 90 else ("review" if score >= 70 else "incomplete")

	return {
		"score": score,
		"state": state,
		"completed": sum(1 for row in applicable if row["status"] == "complete"),
		"total": len(applicable),
		"checks": checks,
		"attention": [row for row in checks if row["status"] in {"action", "warning"}],
		"notice": _(
			"Operational data-readiness indicator only; it is not a legal-compliance certification."
		),
	}


def _employee_payload(employee_doc) -> dict:
	fieldnames = (
		"name",
		"employee_name",
		"first_name",
		"status",
		"company",
		"department",
		"designation",
		"branch",
		"reports_to",
		"user_id",
		"date_of_joining",
		"date_of_birth",
		"company_email",
		"personal_email",
		"cell_number",
		"image",
	)
	return {fieldname: employee_doc.get(fieldname) for fieldname in fieldnames}


def _contract(employee: str):
	rows = _visible_rows(
		"Saudi Employment Contract",
		{
			"employee": employee,
			"docstatus": 1,
			"contract_status": "Active / نشط",
			"start_date": ["<=", nowdate()],
		},
		(
			"name",
			"contract_type",
			"contract_status",
			"start_date",
			"end_date",
			"probation_end_date",
			"basic_salary",
			"housing_allowance",
			"transport_allowance",
			"other_allowances",
			"total_salary",
			"working_hours_per_day",
		),
		order_by="start_date desc, modified desc",
		limit=50,
	)
	row = next(
		(
			candidate
			for candidate in rows
			if not candidate.get("end_date") or getdate(candidate.end_date) >= getdate(nowdate())
		),
		None,
	)
	if not row:
		return None
	row["start_date"] = _as_date(row.get("start_date"))
	row["end_date"] = _as_date(row.get("end_date"))
	row["probation_end_date"] = _as_date(row.get("probation_end_date"))
	row["days_remaining"] = _days_remaining(row.get("end_date"))
	return row


def _permit(employee: str):
	row = _first_visible(
		"Work Permit Iqama",
		{"employee": employee, "docstatus": ["<", 2]},
		(
			"name",
			"iqama_number",
			"iqama_expiry_date",
			"iqama_status",
			"work_permit_number",
			"work_permit_expiry_date",
			"work_permit_status",
		),
		order_by="iqama_expiry_date desc, modified desc",
	)
	if not row:
		return None
	row["iqama_expiry_date"] = _as_date(row.get("iqama_expiry_date"))
	row["work_permit_expiry_date"] = _as_date(row.get("work_permit_expiry_date"))
	row["iqama_days_remaining"] = _days_remaining(row.get("iqama_expiry_date"))
	row["work_permit_days_remaining"] = _days_remaining(row.get("work_permit_expiry_date"))
	return row


def _attendance_setup(employee_doc):
	location = None
	if employee_doc.get("branch"):
		location = _first_visible(
			"Attendance Location",
			{"branch": employee_doc.branch, "is_active": 1},
			(
				"name",
				"location_name",
				"branch",
				"default_shift_type",
				"allowed_radius_meters",
				"voice_verification_policy",
			),
			order_by="modified desc",
		)

	assignment = _first_visible(
		"Saudi Shift Assignment",
		{
			"employee": employee_doc.name,
			"status": "Active",
			"docstatus": 1,
			"start_date": ["<=", nowdate()],
		},
		("name", "shift_type", "start_date", "end_date", "status"),
		order_by="start_date desc",
	)
	if assignment and assignment.get("end_date") and getdate(assignment.end_date) < getdate(nowdate()):
		assignment = None

	return {
		"location": location.get("name") if location else None,
		"location_name": location.get("location_name") if location else None,
		"shift_assignment": assignment.get("name") if assignment else None,
		"shift_type": (
			assignment.get("shift_type")
			if assignment
			else (location.get("default_shift_type") if location else None)
		),
		"voice_policy": location.get("voice_verification_policy") if location else None,
	}


def _attendance(employee: str):
	today_row = _first_visible(
		"Saudi Daily Attendance",
		{"employee": employee, "attendance_date": nowdate(), "docstatus": 1},
		(
			"name",
			"status",
			"attendance_date",
			"in_time",
			"out_time",
			"working_hours",
			"late_entry",
			"late_minutes",
			"early_exit",
			"early_exit_minutes",
		),
	)
	last_checkin = _first_visible(
		"Saudi Employee Checkin",
		{"employee": employee},
		("name", "log_type", "time", "attendance", "verification_mode"),
		order_by="time desc",
	)
	month_rows = _visible_rows(
		"Saudi Daily Attendance",
		{
			"employee": employee,
			"attendance_date": ["between", [str(get_first_day(nowdate())), nowdate()]],
			"docstatus": 1,
		},
		("name", "working_hours", "late_entry", "early_exit"),
		limit=62,
	)

	if today_row:
		today_row["attendance_date"] = _as_date(today_row.get("attendance_date"))
		today_row["in_time"] = _as_datetime(today_row.get("in_time"))
		today_row["out_time"] = _as_datetime(today_row.get("out_time"))
	if last_checkin:
		last_checkin["time"] = _as_datetime(last_checkin.get("time"))

	return {
		"today": today_row,
		"last_checkin": last_checkin,
		"month": {
			"days": len(month_rows),
			"working_hours": round(sum(flt(row.get("working_hours")) for row in month_rows), 2),
			"late_days": sum(1 for row in month_rows if row.get("late_entry")),
			"early_exit_days": sum(1 for row in month_rows if row.get("early_exit")),
		},
	}


def _leave(employee: str):
	try:
		balance = get_annual_leave_balance(employee, nowdate())
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Saudi Employee Profile Leave Summary")
		return {
			"entitled": 0,
			"taken": 0,
			"balance": 0,
			"policy": None,
			"policy_name": None,
			"assignment": None,
			"source_type": None,
			"year": getdate(nowdate()).year,
		}

	return {
		"entitled": flt(balance.get("entitled")),
		"taken": flt(balance.get("taken")),
		"balance": flt(balance.get("balance")),
		"policy": balance.get("policy"),
		"policy_name": balance.get("policy_name"),
		"assignment": balance.get("assignment"),
		"source_type": balance.get("source_type"),
		"year": balance.get("year"),
		"years_of_service": balance.get("years_of_service"),
	}


def _latest_payroll(employee: str, company: str | None):
	if not _can_read("Saudi Monthly Payroll") or not _doctype_exists("Saudi Monthly Payroll Employee"):
		return None

	parents = frappe.get_list(
		"Saudi Monthly Payroll",
		filters={"docstatus": 1},
		fields=[
			"name",
			"company",
			"period_label",
			"month",
			"year",
			"posting_date",
			"status",
			"payroll_journal_entry",
		],
		order_by="posting_date desc, modified desc",
		limit_page_length=50,
	)
	for parent in parents:
		if not parent.payroll_journal_entry:
			continue
		row = frappe.db.get_value(
			"Saudi Monthly Payroll Employee",
			{"parent": parent.name, "employee": employee},
			[
				"gross_salary",
				"total_deductions",
				"net_salary",
				"salary_mode",
			],
			as_dict=True,
		)
		if not row:
			continue
		currency = (
			frappe.db.get_value("Company", parent.company or company, "default_currency")
			if parent.company or company
			else None
		)
		return {
			"name": parent.name,
			"period_label": parent.period_label or f"{parent.month or ''} {parent.year or ''}".strip(),
			"posting_date": _as_date(parent.posting_date),
			"status": parent.status,
			"journal_entry": parent.payroll_journal_entry,
			"paid": bool(parent.payroll_journal_entry),
			"currency": currency or "SAR",
			"gross_salary": flt(row.gross_salary),
			"total_deductions": flt(row.total_deductions),
			"net_salary": flt(row.net_salary),
			"salary_mode": row.salary_mode,
		}
	return None


def _visible_count(doctype: str, employee: str, filters=None) -> int | None:
	if not _can_read(doctype):
		return None
	query_filters = {"employee": employee}
	query_filters.update(filters or {})
	return len(
		frappe.get_list(
			doctype,
			filters=query_filters,
			fields=["name"],
			limit_page_length=500,
		)
	)


def build_employee_profile(employee: str) -> dict:
	if not employee or not frappe.db.exists("Employee", employee):
		frappe.throw(_("Employee not found."))

	employee_doc = frappe.get_doc("Employee", employee)
	frappe.has_permission("Employee", "read", doc=employee_doc, throw=True)
	employee_data = _employee_payload(employee_doc)
	nationality = get_employee_nationality(employee)
	visibility = {
		"contract": _can_read("Saudi Employment Contract"),
		"permit": _can_read("Work Permit Iqama"),
		"attendance": _can_read("Saudi Daily Attendance"),
		"attendance_setup": _can_read("Attendance Location")
		or _can_read("Saudi Shift Assignment"),
		"leave": _can_read("Saudi Annual Leave"),
		"payroll": _can_read("Saudi Monthly Payroll"),
		"documents": _can_read("Employee Document Custody Log"),
		"relations": _can_read("Employee Grievance"),
		"complete_file": can_access_complete_employee_file(employee_doc.name),
	}
	contract = _contract(employee) if visibility["contract"] else None
	permit = _permit(employee) if visibility["permit"] and not is_saudi_nationality(nationality) else None
	attendance_setup = _attendance_setup(employee_doc)
	attendance = _attendance(employee) if visibility["attendance"] else None
	leave = (
		_leave(employee)
		if visibility["leave"]
		else {
			"entitled": 0,
			"taken": 0,
			"balance": 0,
			"policy": None,
			"policy_name": None,
			"assignment": None,
			"source_type": None,
			"year": getdate(nowdate()).year,
		}
	)
	payroll = _latest_payroll(employee, employee_doc.company) if visibility["payroll"] else None
	user_enabled = bool(
		employee_doc.user_id
		and frappe.db.get_value("User", employee_doc.user_id, "enabled")
	)

	context = {
		"employee": employee_data,
		"user_enabled": user_enabled,
		"nationality": nationality,
		"contract": contract,
		"permit": permit,
		"attendance_setup": attendance_setup,
		"leave": leave,
		"visibility": visibility,
	}
	readiness = calculate_employee_readiness(context)

	return {
		"schema_version": PROFILE_SCHEMA_VERSION,
		"generated_on": _as_datetime(now_datetime()),
		"employee": employee_data,
		"manager_name": (
			frappe.db.get_value("Employee", employee_doc.reports_to, "employee_name")
			if employee_doc.reports_to
			else None
		),
		"nationality": nationality,
		"currency": (
			frappe.db.get_value("Company", employee_doc.company, "default_currency")
			if employee_doc.company
			else "SAR"
		)
		or "SAR",
		"readiness": readiness,
		"contract": contract,
		"permit": permit,
		"attendance_setup": attendance_setup,
		"attendance": attendance,
		"leave": leave,
		"payroll": payroll,
		"visibility": visibility,
		"counts": {
			"pending_leave": _visible_count(
				"Saudi Annual Leave",
				employee,
				{"docstatus": 0, "workflow_state": ["not in", ["Rejected", "Approved"]]},
			),
			"policy_acknowledgements": _visible_count(
				"Policy Acknowledgement",
				employee,
				{"acknowledgement_status": ["like", "Pending%"]},
			),
			"document_custody": _visible_count("Employee Document Custody Log", employee),
			"grievances": _visible_count("Employee Grievance", employee),
			"warnings": _visible_count("Employee Warning Notice", employee),
		},
	}


@frappe.whitelist(methods=["GET", "POST"])
def get_employee_profile(employee: str):
	return build_employee_profile(employee)
