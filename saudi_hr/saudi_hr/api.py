"""
saudi_hr/api.py
Mobile attendance, employee insights, and self-service leave APIs.
"""

import base64
import calendar
import json
from pathlib import Path

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, get_first_day, get_last_day, get_url, getdate, now_datetime, nowdate, time_diff_in_hours
from frappe.utils.file_manager import save_file

from saudi_hr.saudi_hr.attendance_policy import (
	VOICE_POLICY_DISABLED,
	VOICE_POLICY_REQUIRED,
	calculate_attendance_variance,
	resolve_mobile_attendance_policy,
	summarize_schedule_status,
)
from saudi_hr.saudi_hr.doctype.maternity_paternity_leave.maternity_paternity_leave import LEAVE_DAYS
from saudi_hr.saudi_hr.location_utils import resolve_location_reference
from saudi_hr.saudi_hr.utils import assert_doctype_permissions, get_annual_leave_balance
from saudi_hr.saudi_hr.voice_verification import (
	VOICE_VERIFICATION_STATUS_NOT_REQUIRED,
	VOICE_VERIFICATION_STATUS_PASSED,
	enroll_employee_voice_profile,
	get_employee_voice_profile_status,
	get_voice_runtime_status,
	issue_voice_challenge,
	verify_checkin_voice,
)


SPECIAL_LEAVE_OPTIONS = [
	"Hajj Leave / إجازة حج (م.113 – 15 يوم)",
	"Bereavement Leave / إجازة وفاة (م.113 – 5 أيام)",
	"Marriage Leave / إجازة زواج (م.113 – 5 أيام)",
]

ELEVATED_ROLES = {"HR Manager", "HR User", "System Manager"}
ORG_TREE_GLOBAL_ROLES = {"HR Manager", "HR User", "System Manager"}
ORG_TREE_MANAGER_ROLES = {"Department Approver", "Leave Approver"}
ORG_TREE_ROOT_VALUE = "__org_root__"
ORG_TREE_UNASSIGNED_DEPARTMENT = "__unassigned_department__"
MAX_MOBILE_ATTACHMENTS = 3
MAX_MOBILE_ATTACHMENT_SIZE = 5 * 1024 * 1024

MOBILE_ATTENDANCE_API_ENDPOINTS = (
	{
		"key": "status",
		"http_method": "GET",
		"method": "saudi_hr.saudi_hr.api.mobile_attendance_api_status",
		"description": "Current employee attendance, leave, schedule, and voice verification snapshot.",
		"payload_fields": [],
	},
	{
		"key": "checkin",
		"http_method": "POST",
		"method": "saudi_hr.saudi_hr.api.mobile_attendance_api_checkin",
		"description": "Create mobile check-in or check-out with GPS and optional voice verification.",
		"payload_fields": [
			"latitude",
			"longitude",
			"verification_mode",
			"verification_note",
			"challenge_token",
			"voice_payload_json",
		],
	},
	{
		"key": "leave_request",
		"http_method": "POST",
		"method": "saudi_hr.saudi_hr.api.mobile_attendance_api_leave_request",
		"description": "Submit mobile leave requests with the same workflow and permission checks used inside Saudi HR.",
		"payload_fields": [
			"request_type",
			"start_date",
			"end_date",
			"reason",
			"leave_subtype",
			"relationship_to_deceased",
			"medical_certificate_no",
			"hospital_name",
			"expected_delivery_date",
			"actual_delivery_date",
			"half_day",
			"attachments_json",
		],
	},
	{
		"key": "locations",
		"http_method": "GET",
		"method": "saudi_hr.saudi_hr.api.mobile_attendance_api_locations",
		"description": "List attendance locations visible to the authenticated user.",
		"payload_fields": [],
	},
)

WORKFLOW_AUDIT_TARGETS = (
	{
		"key": "annual_leave",
		"workflow_name": "Annual Leave Approval Workflow",
		"fixture": "workflow/annual_leave_approval_workflow/annual_leave_approval_workflow.json",
	},
	{
		"key": "sick_leave",
		"workflow_name": "Sick Leave Approval Workflow",
		"fixture": "workflow/sick_leave_approval_workflow/sick_leave_approval_workflow.json",
	},
	{
		"key": "overtime",
		"workflow_name": "Overtime Approval Workflow",
		"fixture": "workflow/overtime_approval_workflow/overtime_approval_workflow.json",
	},
	{
		"key": "salary_adjustment",
		"workflow_name": "Salary Adjustment Workflow",
		"fixture": "workflow/salary_adjustment_workflow/salary_adjustment_workflow.json",
	},
	{
		"key": "termination",
		"workflow_name": "Termination Approval Workflow",
		"fixture": "workflow/termination_approval_workflow/termination_approval_workflow.json",
	},
)


def _distance_meters(lat1, lon1, lat2, lon2):
	from math import asin, cos, pi, sqrt

	r = 6_371_000
	p = pi / 180
	a = (
		0.5
		- cos((lat2 - lat1) * p) / 2
		+ cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
	)
	return 2 * r * asin(sqrt(a))


def _get_employee_for_user(user=None):
	user = user or frappe.session.user
	employee = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")
	if not employee:
		frappe.throw(_("لم يتم ربط حسابك بسجل موظف نشط. يرجى مراجعة مسؤول النظام."))
	return employee


def _get_employee_profile(employee):
	return frappe.db.get_value(
		"Employee",
		employee,
		["employee_name", "branch", "department", "image", "company", "designation"],
		as_dict=True,
	)


def _require_employee_context():
	if frappe.session.user == "Guest":
		frappe.throw(_("يجب تسجيل الدخول أولاً."), frappe.PermissionError)

	employee = _get_employee_for_user()
	return employee, _get_employee_profile(employee)


def _get_location_for_branch(branch):
	if not branch:
		return None
	return frappe.db.get_value(
		"Attendance Location",
		{"branch": branch, "is_active": 1},
		[
			"name",
			"location_name",
			"branch",
			"latitude",
			"longitude",
			"allowed_radius_meters",
			"plus_code",
			"location_source",
			"address_reference",
			"default_shift_type",
			"enforce_schedule",
			"voice_verification_policy",
			"voice_challenge_ttl_seconds",
			"voice_max_duration_seconds",
		],
		as_dict=True,
	)


def _get_todays_checkins(employee):
	return frappe.get_all(
		"Saudi Employee Checkin",
		filters={"employee": employee, "time": ["between", [nowdate() + " 00:00:00", nowdate() + " 23:59:59"]]},
		fields=["name", "log_type", "time", "latitude", "longitude", "verification_mode"],
		order_by="time asc",
	)


def _coerce_float(value):
	return flt(value) if value not in (None, "", "null", "undefined") else None


def _value_or_payload(explicit_value, payload, key, default=None):
	if explicit_value is not None:
		return explicit_value
	if isinstance(payload, dict):
		return payload.get(key, default)
	return default


def _load_json_param(value, default=None):
	if value in (None, "", "null", "undefined"):
		return default
	if isinstance(value, (dict, list)):
		return value
	return json.loads(value)


def _load_json_object_param(value, default=None):
	payload = _load_json_param(value, default=default or {})
	if payload in (None, ""):
		return default or {}
	if not isinstance(payload, dict):
		frappe.throw(_("يجب أن يكون الطلب بصيغة JSON object صحيحة."), frappe.ValidationError)
	return payload


def _get_active_employee_for_user(user=None):
	user = user or frappe.session.user
	return frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name") or frappe.db.get_value(
		"Employee", {"user_id": user}, "name"
	)


def _resolve_mobile_api_target_user(user=None):
	current_user = frappe.session.user
	target_user = (user or current_user or "").strip()
	if not target_user or target_user == "Guest":
		frappe.throw(_("يجب تسجيل الدخول أولاً قبل إصدار بيانات الربط."), frappe.PermissionError)

	if target_user == current_user:
		return target_user

	if "System Manager" not in set(frappe.get_roles(current_user)):
		frappe.throw(_("يمكن فقط لمسؤول النظام إصدار بيانات ربط لمستخدم آخر."), frappe.PermissionError)

	return target_user


def _rotate_user_api_credentials(user):
	user_doc = frappe.get_doc("User", user)
	if getattr(user_doc, "enabled", 1) == 0:
		frappe.throw(_("لا يمكن إصدار بيانات ربط لمستخدم غير مفعّل."), frappe.ValidationError)

	if not getattr(user_doc, "api_key", None):
		user_doc.api_key = frappe.generate_hash(length=15)

	api_secret = frappe.generate_hash(length=15)
	user_doc.api_secret = api_secret
	if not getattr(user_doc, "flags", None):
		user_doc.flags = frappe._dict()
	user_doc.flags.ignore_permissions = True
	user_doc.save()
	frappe.db.commit()
	return user_doc, api_secret


def _build_mobile_api_response(data, message=None):
	response = {
		"ok": True,
		"data": data,
		"meta": {
			"user": frappe.session.user,
			"generated_at": str(now_datetime()),
		},
	}
	if message:
		response["message"] = message
	return response


def _build_mobile_attendance_api_reference(base_url=None):
	base_url = (base_url or get_url()).rstrip("/")
	reference = []
	for endpoint in MOBILE_ATTENDANCE_API_ENDPOINTS:
		reference.append(
			{
				**endpoint,
				"path": f"{base_url}/api/method/{endpoint['method']}",
			}
		)
	return reference


def _workflow_fixture_path(relative_path):
	return Path(__file__).resolve().parent / relative_path


def _load_workflow_snapshot(config):
	workflow_name = config["workflow_name"]
	if frappe.db.exists("Workflow", workflow_name):
		doc = frappe.get_doc("Workflow", workflow_name)
		return {
			"workflow_name": doc.workflow_name,
			"document_type": doc.document_type,
			"states": [dict(row) for row in doc.states],
			"transitions": [dict(row) for row in doc.transitions],
			"source": "database",
		}

	with _workflow_fixture_path(config["fixture"]).open(encoding="utf-8") as handle:
		payload = json.load(handle)
	payload["source"] = "fixture"
	return payload


def _is_negative_workflow_transition(transition):
	text = " ".join(
		str(transition.get(field) or "").lower()
		for field in ("action", "next_state")
	)
	return any(keyword in text for keyword in ("reject", "rejected", "cancel", "cancelled", "reset", "return", "مرفوض", "ملغى"))


def _get_workflow_start_state(snapshot):
	states = [state.get("state") for state in snapshot.get("states") or [] if state.get("state")]
	if "Draft" in states:
		return "Draft"
	for state_name in states:
		if "draft" in state_name.lower() or "مسودة" in state_name:
			return state_name
	incoming_states = {transition.get("next_state") for transition in snapshot.get("transitions") or []}
	for state_name in states:
		if state_name not in incoming_states:
			return state_name
	return states[0] if states else None


def _build_workflow_route(snapshot):
	states = {state.get("state"): state for state in snapshot.get("states") or [] if state.get("state")}
	transitions = snapshot.get("transitions") or []
	current_state = _get_workflow_start_state(snapshot)
	route = []
	visited = set()

	while current_state and current_state not in visited:
		visited.add(current_state)
		state_meta = states.get(current_state) or {}
		candidate_transitions = [transition for transition in transitions if transition.get("state") == current_state]
		approval_candidates = [transition for transition in candidate_transitions if not _is_negative_workflow_transition(transition)]
		selected_transition = approval_candidates[0] if approval_candidates else None
		route.append(
			{
				"state": current_state,
				"doc_status": state_meta.get("doc_status"),
				"editable_by": state_meta.get("allow_edit"),
				"action": selected_transition.get("action") if selected_transition else None,
				"allowed_role": selected_transition.get("allowed") if selected_transition else None,
				"next_state": selected_transition.get("next_state") if selected_transition else None,
			}
		)
		if not selected_transition:
			break
		current_state = selected_transition.get("next_state")

	return route


def _build_workflow_route_audit_entry(config):
	snapshot = _load_workflow_snapshot(config)
	negative_transitions = [
		{
			"state": transition.get("state"),
			"action": transition.get("action"),
			"allowed_role": transition.get("allowed"),
			"next_state": transition.get("next_state"),
		}
		for transition in snapshot.get("transitions") or []
		if _is_negative_workflow_transition(transition)
	]
	return {
		"key": config["key"],
		"workflow_name": snapshot.get("workflow_name"),
		"document_type": snapshot.get("document_type"),
		"source": snapshot.get("source"),
		"approval_route": _build_workflow_route(snapshot),
		"alternate_transitions": negative_transitions,
	}


def _has_org_tree_global_access(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return bool(ORG_TREE_GLOBAL_ROLES.intersection(set(frappe.get_roles(user))))


def _has_org_tree_manager_scope(user=None):
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if ORG_TREE_MANAGER_ROLES.intersection(roles):
		return True

	return bool(
		frappe.db.sql(
			"""
			SELECT name
			FROM `tabEmployee`
			WHERE leave_approver = %(user)s OR expense_approver = %(user)s
			LIMIT 1
			""",
			{"user": user},
		)
	)


def _ensure_org_tree_access(user=None):
	if _has_org_tree_global_access(user) or _has_org_tree_manager_scope(user):
		return
	frappe.throw(_("Only HR or direct approvers can open the organization tree."), frappe.PermissionError)


def _get_org_tree_scope_rows(company=None, branch=None, department=None, user=None):
	user = user or frappe.session.user
	_ensure_org_tree_access(user)

	conditions = ["status = 'Active'"]
	values = {}

	if company:
		conditions.append("company = %(company)s")
		values["company"] = company
	if branch:
		conditions.append("branch = %(branch)s")
		values["branch"] = branch
	if department:
		conditions.append("department = %(department)s")
		values["department"] = department

	if not _has_org_tree_global_access(user):
		scope_conditions = ["leave_approver = %(review_user)s", "expense_approver = %(review_user)s"]
		values["review_user"] = user
		scope_employee = _get_active_employee_for_user(user)
		if scope_employee:
			scope_conditions.extend(["name = %(scope_employee)s", "reports_to = %(scope_employee)s"])
			values["scope_employee"] = scope_employee
		conditions.append("(" + " OR ".join(scope_conditions) + ")")

	where = " AND ".join(conditions)
	return frappe.db.sql(
		f"""
		SELECT
			name,
			employee_name,
			designation,
			department,
			branch,
			company,
			reports_to,
			user_id,
			leave_approver,
			expense_approver
		FROM `tabEmployee`
		WHERE {where}
		ORDER BY department ASC, employee_name ASC, name ASC
		""",
		values,
		as_dict=True,
	)


def _department_key(department_name):
	return f"department::{department_name or ORG_TREE_UNASSIGNED_DEPARTMENT}"


def _employee_key(employee_name):
	return f"employee::{employee_name}"


def _normalize_department_name(department_name):
	return department_name or ORG_TREE_UNASSIGNED_DEPARTMENT


def _department_label(department_name):
	return department_name or _("Unassigned Department / بدون قسم")


def _get_direct_reports(rows, employee_name, department_name=None):
	department_name = _normalize_department_name(department_name) if department_name is not None else None
	return [
		row
		for row in rows
		if row.reports_to == employee_name
		and (
			department_name is None
			or _normalize_department_name(row.department) == department_name
		)
	]


def _get_department_manager_count(rows, department_name):
	department_name = _normalize_department_name(department_name)
	count = 0
	for row in rows:
		if _normalize_department_name(row.department) != department_name:
			continue
		if _get_direct_reports(rows, row.name, department_name=department_name):
			count += 1
	return count


def _build_department_tree_node(department_name, rows):
	department_rows = [row for row in rows if _normalize_department_name(row.department) == department_name]
	approver_users = {
		user
		for row in department_rows
		for user in (row.leave_approver, row.expense_approver)
		if user
	}
	return {
		"value": _department_key(None if department_name == ORG_TREE_UNASSIGNED_DEPARTMENT else department_name),
		"title": _department_label(None if department_name == ORG_TREE_UNASSIGNED_DEPARTMENT else department_name),
		"expandable": bool(department_rows),
		"node_type": "department",
		"department": None if department_name == ORG_TREE_UNASSIGNED_DEPARTMENT else department_name,
		"department_label": _department_label(None if department_name == ORG_TREE_UNASSIGNED_DEPARTMENT else department_name),
		"employee_count": len(department_rows),
		"manager_count": _get_department_manager_count(rows, department_name),
		"approver_count": len(approver_users),
	}


def _build_employee_tree_node(row, rows):
	row_map = {employee.name: employee for employee in rows}
	department_name = _normalize_department_name(row.department)
	direct_reports = _get_direct_reports(rows, row.name, department_name=department_name)
	reference_manager = row_map.get(row.reports_to)
	return {
		"value": _employee_key(row.name),
		"title": row.employee_name or row.name,
		"expandable": bool(direct_reports),
		"node_type": "employee",
		"employee": row.name,
		"employee_name": row.employee_name,
		"designation": row.designation,
		"department": row.department,
		"department_label": _department_label(row.department),
		"branch": row.branch,
		"company": row.company,
		"reports_to": row.reports_to,
		"reports_to_name": reference_manager.employee_name if reference_manager else None,
		"user_id": row.user_id,
		"leave_approver": row.leave_approver,
		"expense_approver": row.expense_approver,
		"direct_report_count": len(direct_reports),
	}


def _get_department_root_employees(rows, department_name):
	department_name = _normalize_department_name(department_name)
	row_map = {employee.name: employee for employee in rows}
	department_rows = [row for row in rows if _normalize_department_name(row.department) == department_name]
	root_rows = []
	for row in department_rows:
		manager = row_map.get(row.reports_to)
		if not manager or _normalize_department_name(manager.department) != department_name:
			root_rows.append(row)
	return root_rows


@frappe.whitelist(methods=["GET", "POST"])
def get_employee_org_hierarchy_summary(company=None, branch=None, department=None):
	rows = _get_org_tree_scope_rows(company=company, branch=branch, department=department)
	approver_users = {
		user
		for row in rows
		for user in (row.leave_approver, row.expense_approver)
		if user
	}
	manager_count = sum(1 for row in rows if _get_direct_reports(rows, row.name))
	return {
		"root_label": company or _("Saudi HR Organization / الهيكل الإداري"),
		"scope_label": _("Organization-wide / كامل المؤسسة") if _has_org_tree_global_access() else _("Team scope / نطاق الفريق"),
		"employee_count": len(rows),
		"department_count": len({_normalize_department_name(row.department) for row in rows}),
		"manager_count": manager_count,
		"approver_count": len(approver_users),
	}


@frappe.whitelist(methods=["GET", "POST"])
def get_employee_org_tree_nodes(parent=None, is_root=False, company=None, branch=None, department=None):
	rows = _get_org_tree_scope_rows(company=company, branch=branch, department=department)
	if cint(is_root) or parent in (None, "", ORG_TREE_ROOT_VALUE):
		departments = sorted({_normalize_department_name(row.department) for row in rows}, key=lambda value: _department_label(None if value == ORG_TREE_UNASSIGNED_DEPARTMENT else value))
		return [_build_department_tree_node(department_name, rows) for department_name in departments]

	if parent and str(parent).startswith("department::"):
		department_name = str(parent).split("::", 1)[1] or ORG_TREE_UNASSIGNED_DEPARTMENT
		root_rows = sorted(
			_get_department_root_employees(rows, department_name),
			key=lambda row: ((row.employee_name or row.name or "").lower(), row.name),
		)
		return [_build_employee_tree_node(row, rows) for row in root_rows]

	if parent and str(parent).startswith("employee::"):
		employee_name = str(parent).split("::", 1)[1]
		parent_row = next((row for row in rows if row.name == employee_name), None)
		if not parent_row:
			return []
		direct_reports = sorted(
			_get_direct_reports(rows, employee_name, department_name=_normalize_department_name(parent_row.department)),
			key=lambda row: ((row.employee_name or row.name or "").lower(), row.name),
		)
		return [_build_employee_tree_node(row, rows) for row in direct_reports]

	return []


@frappe.whitelist(methods=["GET"])
def get_workflow_route_audit(workflow_key=None):
	if frappe.session.user == "Guest":
		frappe.throw(_("يجب تسجيل الدخول أولاً."), frappe.PermissionError)

	targets = WORKFLOW_AUDIT_TARGETS
	if workflow_key:
		targets = [config for config in WORKFLOW_AUDIT_TARGETS if config["key"] == workflow_key]
	return [_build_workflow_route_audit_entry(config) for config in targets]


def _decode_base64_content(content):
	if not content:
		return b""
	if "," in content and ";base64" in content.split(",", 1)[0]:
		content = content.split(",", 1)[1]
	return base64.b64decode(content)


def _attach_files(doc, attachments):
	if not attachments:
		return []

	if len(attachments) > MAX_MOBILE_ATTACHMENTS:
		frappe.throw(_("يمكن إرفاق ثلاثة ملفات كحد أقصى لكل عملية."))

	attached = []
	for index, attachment in enumerate(attachments, start=1):
		filename = (attachment or {}).get("filename") or f"{doc.name}-{index}"
		content = _decode_base64_content((attachment or {}).get("content"))
		if not content:
			continue
		if len(content) > MAX_MOBILE_ATTACHMENT_SIZE:
			frappe.throw(_("حجم الملف الواحد يجب ألا يتجاوز 5 ميجابايت."))

		file_doc = save_file(filename, content, doc.doctype, doc.name, is_private=1)
		attached.append({"file_name": file_doc.file_name, "file_url": file_doc.file_url})

	return attached


def _get_contract_hours_per_day(employee):
	working_hours = frappe.db.get_value(
		"Saudi Employment Contract",
		{"employee": employee, "contract_status": "Active / نشط"},
		"working_hours_per_day",
		order_by="start_date desc",
	)
	return flt(working_hours or 8)


def _get_period_bounds(month=None, year=None):
	today = getdate(nowdate())
	month_number = int(month or today.month)
	year_number = int(year or today.year)
	anchor = getdate(f"{year_number}-{month_number:02d}-01")
	return get_first_day(anchor), get_last_day(anchor), month_number, year_number


def _get_payroll_snapshot(employee):
	rows = frappe.db.sql(
		"""
		SELECT
			child.gosi_employee_deduction,
			child.sick_leave_deduction,
			child.loan_deduction,
			child.total_deductions,
			child.overtime_addition,
			child.net_salary,
			parent.month,
			parent.year,
			parent.status
		FROM `tabSaudi Monthly Payroll Employee` child
		INNER JOIN `tabSaudi Monthly Payroll` parent ON parent.name = child.parent
		WHERE child.employee = %s AND parent.docstatus = 1
		ORDER BY parent.year DESC, parent.modified DESC
		LIMIT 1
		""",
		employee,
		as_dict=True,
	)
	if not rows:
		return None

	row = rows[0]
	return {
		"period": f"{row.month} {row.year}",
		"status": row.status,
		"gosi_deduction": flt(row.gosi_employee_deduction),
		"sick_leave_deduction": flt(row.sick_leave_deduction),
		"loan_deduction": flt(row.loan_deduction),
		"total_deductions": flt(row.total_deductions),
		"overtime_addition": flt(row.overtime_addition),
		"net_salary": flt(row.net_salary),
	}


def _get_attendance_insights(employee, month=None, year=None):
	from_date, to_date, month_number, year_number = _get_period_bounds(month, year)
	working_hours_target = _get_contract_hours_per_day(employee)

	record = frappe.db.get_value(
		"Monthly Attendance Record",
		{"employee": employee, "year": year_number, "month": ["like", f"{calendar.month_name[month_number]}%"]},
		[
			"actual_present_days",
			"absent_days",
			"late_days",
			"late_minutes_total",
			"overtime_hours_total",
			"annual_leave_days",
			"sick_leave_days",
			"special_leave_days",
			"other_leave_days",
		],
		as_dict=True,
	)

	attendance_rows = frappe.get_all(
		"Saudi Daily Attendance",
		filters={"employee": employee, "attendance_date": ["between", [from_date, to_date]], "docstatus": 1},
		fields=["status", "working_hours", "late_entry", "early_exit"],
	)

	total_hours = round(sum(flt(row.working_hours) for row in attendance_rows), 2)
	recorded_days = len(attendance_rows)
	shortfall_days = sum(1 for row in attendance_rows if flt(row.working_hours) and flt(row.working_hours) < working_hours_target)
	early_exit_days = sum(1 for row in attendance_rows if row.early_exit)
	late_entry_days = sum(1 for row in attendance_rows if row.late_entry)

	return {
		"period_label": f"{calendar.month_name[month_number]} {year_number}",
		"present_days": int((record or {}).get("actual_present_days") or recorded_days),
		"absent_days": int((record or {}).get("absent_days") or 0),
		"late_days": int((record or {}).get("late_days") or late_entry_days),
		"late_minutes_total": int((record or {}).get("late_minutes_total") or 0),
		"overtime_hours_total": round(flt((record or {}).get("overtime_hours_total") or 0), 2),
		"recorded_days": recorded_days,
		"total_hours": total_hours,
		"average_hours": round(total_hours / recorded_days, 2) if recorded_days else 0,
		"shortfall_days": shortfall_days,
		"early_exit_days": early_exit_days,
		"target_hours_per_day": working_hours_target,
		"leave_days": {
			"annual": flt((record or {}).get("annual_leave_days") or 0),
			"sick": flt((record or {}).get("sick_leave_days") or 0),
			"special": flt((record or {}).get("special_leave_days") or 0),
			"other": flt((record or {}).get("other_leave_days") or 0),
		},
		"payroll": _get_payroll_snapshot(employee),
	}


def _get_leave_options(employee):
	annual_balance = get_annual_leave_balance(employee, nowdate())

	return {
		"annual": {
			"label": "Annual Leave / إجازة سنوية",
			"doctype": "Saudi Annual Leave",
			"balance": annual_balance.get("balance"),
			"entitled": annual_balance.get("entitled"),
			"taken": annual_balance.get("taken"),
		},
		"sick": {
			"label": "Sick Leave / إجازة مرضية",
			"doctype": "Saudi Sick Leave",
			"requires_attachments": True,
		},
		"special": {
			"label": "Special Leave / إجازة خاصة",
			"doctype": "Special Leave",
			"options": SPECIAL_LEAVE_OPTIONS,
			"requires_attachments": True,
		},
		"maternity_paternity": {
			"label": "Maternity / Paternity / أمومة وأبوة",
			"doctype": "Maternity Paternity Leave",
			"options": list(LEAVE_DAYS.keys()),
			"requires_attachments": True,
		},
	}


def _get_mobile_leave_base_fields(employee, profile):
	return {
		"employee": employee,
		"employee_name": profile.employee_name,
		"company": profile.company,
		"department": profile.department,
	}


def _build_mobile_leave_doc(employee, profile, request_type, attachments, payload):
	base_fields = _get_mobile_leave_base_fields(employee, profile)

	if request_type == "annual":
		return frappe.get_doc(
			{
				"doctype": "Saudi Annual Leave",
				**base_fields,
				"leave_start_date": payload["start_date"],
				"leave_end_date": payload["end_date"] or payload["start_date"],
				"half_day": int(payload.get("half_day") or 0),
				"description": payload.get("reason") or "",
			}
		)

	if request_type == "sick":
		return frappe.get_doc(
			{
				"doctype": "Saudi Sick Leave",
				**base_fields,
				"from_date": payload["start_date"],
				"to_date": payload["end_date"] or payload["start_date"],
				"medical_certificate_no": payload.get("medical_certificate_no"),
				"hospital_name": payload.get("hospital_name"),
				"medical_certificate_attached": 1 if attachments else 0,
			}
		)

	if request_type == "special":
		return frappe.get_doc(
			{
				"doctype": "Special Leave",
				**base_fields,
				"leave_type": payload.get("leave_subtype"),
				"leave_start_date": payload["start_date"],
				"leave_end_date": payload["end_date"] or payload["start_date"],
				"relationship_to_deceased": payload.get("relationship_to_deceased"),
				"documentation_attached": 1 if attachments else 0,
				"notes": payload.get("reason") or "",
			}
		)

	if request_type == "maternity_paternity":
		return frappe.get_doc(
			{
				"doctype": "Maternity Paternity Leave",
				**base_fields,
				"leave_type": payload.get("leave_subtype"),
				"leave_start_date": payload["start_date"],
				"expected_delivery_date": payload.get("expected_delivery_date"),
				"actual_delivery_date": payload.get("actual_delivery_date"),
				"hospital_name": payload.get("hospital_name"),
				"medical_certificate_attached": 1 if attachments else 0,
			}
		)

	frappe.throw(_("نوع طلب الإجازة غير مدعوم."))


def _docstatus_label(docstatus):
	if docstatus == 1:
		return "Submitted / مرسلة"
	if docstatus == 2:
		return "Cancelled / ملغاة"
	return "Draft / مسودة"


def _get_recent_leave_requests(employee, limit=8):
	rows = []

	for row in frappe.get_all(
		"Saudi Annual Leave",
		filters={"employee": employee},
		fields=["name", "status", "leave_start_date", "leave_end_date", "total_leave_days", "creation", "docstatus"],
		order_by="creation desc",
		limit=limit,
	):
		rows.append(
			{
				"name": row.name,
				"category": "Annual Leave / إجازة سنوية",
				"status": row.status,
				"from_date": row.leave_start_date,
				"to_date": row.leave_end_date,
				"days": flt(row.total_leave_days),
				"created_at": str(row.creation),
			}
		)

	for doctype, category, start_field, end_field, days_field, subtype_field, status_field in [
		("Saudi Sick Leave", "Sick Leave / إجازة مرضية", "from_date", "to_date", "total_days", None, None),
		("Special Leave", "Special Leave / إجازة خاصة", "leave_start_date", "leave_end_date", "actual_days", "leave_type", "status"),
		("Maternity Paternity Leave", "Maternity / Paternity / أمومة وأبوة", "leave_start_date", "leave_end_date", "entitled_days", "leave_type", None),
	]:
		fields = ["name", start_field, end_field, days_field, "creation", "docstatus"]
		if subtype_field:
			fields.append(subtype_field)
		if status_field:
			fields.append(status_field)

		for row in frappe.get_all(doctype, filters={"employee": employee}, fields=fields, order_by="creation desc", limit=limit):
			rows.append(
				{
					"name": row.name,
					"category": category,
					"subtype": getattr(row, subtype_field, None) if subtype_field else None,
					"status": getattr(row, status_field, None) if status_field else _docstatus_label(row.docstatus),
					"from_date": getattr(row, start_field, None),
					"to_date": getattr(row, end_field, None),
					"days": flt(getattr(row, days_field, 0) or 0),
					"created_at": str(row.creation),
				}
			)

	rows.sort(key=lambda item: item["created_at"], reverse=True)
	return rows[:limit]


def _build_verification_mode(raw_mode, has_voice=False):
	modes = [segment for segment in (raw_mode or "gps").split("+") if segment]
	if has_voice and "voice" not in modes:
		modes.append("voice")
	return "+".join(dict.fromkeys(modes)) or "gps"


@frappe.whitelist(methods=["GET"])
def get_mobile_attendance_api_contract():
	if frappe.session.user == "Guest":
		frappe.throw(_("يجب تسجيل الدخول أولاً."), frappe.PermissionError)

	current_user = frappe.session.user
	employee = _get_active_employee_for_user(current_user)
	return {
		"base_url": get_url(),
		"auth": {
			"scheme": "token",
			"header": "Authorization: token <api_key>:<api_secret>",
			"credential_method": "saudi_hr.saudi_hr.api.issue_mobile_attendance_api_credentials",
		},
		"actor": {
			"user": current_user,
			"employee": employee,
			"roles": frappe.get_roles(current_user),
		},
		"endpoints": _build_mobile_attendance_api_reference(),
	}


@frappe.whitelist(methods=["POST"])
def issue_mobile_attendance_api_credentials(user=None):
	target_user = _resolve_mobile_api_target_user(user)
	user_doc, api_secret = _rotate_user_api_credentials(target_user)
	employee = _get_active_employee_for_user(target_user)
	api_key = user_doc.api_key
	return {
		"user": target_user,
		"employee": employee,
		"api_key": api_key,
		"api_secret": api_secret,
		"authorization_header": f"token {api_key}:{api_secret}",
		"base_url": get_url(),
		"documentation_method": "saudi_hr.saudi_hr.api.get_mobile_attendance_api_contract",
		"message": _("تم إصدار بيانات الربط بنجاح. استخدمها في التطبيق الخارجي بصلاحيات نفس المستخدم."),
	}


@frappe.whitelist(methods=["GET"])
def mobile_attendance_api_status():
	return _build_mobile_api_response(get_attendance_status())


@frappe.whitelist(methods=["GET"])
def mobile_attendance_api_locations():
	return _build_mobile_api_response(get_available_locations())


@frappe.whitelist(methods=["POST"])
def mobile_attendance_api_checkin(
	payload_json=None,
	latitude=None,
	longitude=None,
	verification_mode=None,
	verification_note=None,
	attachments_json=None,
	challenge_token=None,
	voice_payload_json=None,
):
	payload = _load_json_object_param(payload_json, default={})
	result = do_mobile_checkin(
		latitude=_value_or_payload(latitude, payload, "latitude"),
		longitude=_value_or_payload(longitude, payload, "longitude"),
		verification_mode=_value_or_payload(verification_mode, payload, "verification_mode"),
		verification_note=_value_or_payload(verification_note, payload, "verification_note"),
		attachments_json=_value_or_payload(attachments_json, payload, "attachments_json"),
		challenge_token=_value_or_payload(challenge_token, payload, "challenge_token"),
		voice_payload_json=_value_or_payload(voice_payload_json, payload, "voice_payload_json"),
	)
	return _build_mobile_api_response(result)


@frappe.whitelist(methods=["POST"])
def mobile_attendance_api_leave_request(
	payload_json=None,
	request_type=None,
	start_date=None,
	end_date=None,
	reason=None,
	leave_subtype=None,
	relationship_to_deceased=None,
	medical_certificate_no=None,
	hospital_name=None,
	expected_delivery_date=None,
	actual_delivery_date=None,
	half_day=0,
	attachments_json=None,
):
	payload = _load_json_object_param(payload_json, default={})
	result = submit_mobile_leave_request(
		request_type=_value_or_payload(request_type, payload, "request_type"),
		start_date=_value_or_payload(start_date, payload, "start_date"),
		end_date=_value_or_payload(end_date, payload, "end_date"),
		reason=_value_or_payload(reason, payload, "reason"),
		leave_subtype=_value_or_payload(leave_subtype, payload, "leave_subtype"),
		relationship_to_deceased=_value_or_payload(relationship_to_deceased, payload, "relationship_to_deceased"),
		medical_certificate_no=_value_or_payload(medical_certificate_no, payload, "medical_certificate_no"),
		hospital_name=_value_or_payload(hospital_name, payload, "hospital_name"),
		expected_delivery_date=_value_or_payload(expected_delivery_date, payload, "expected_delivery_date"),
		actual_delivery_date=_value_or_payload(actual_delivery_date, payload, "actual_delivery_date"),
		half_day=cint(_value_or_payload(half_day, payload, "half_day", default=0) or 0),
		attachments_json=_value_or_payload(attachments_json, payload, "attachments_json"),
	)
	return _build_mobile_api_response(result)


@frappe.whitelist()
def get_employee_paid_payroll_history(employee, limit=10):
	if not employee:
		return []

	limit = max(1, min(int(limit or 10), 50))
	if not frappe.db.exists("Employee", employee):
		frappe.throw(_("Employee not found."))

	employee_doc = frappe.get_doc("Employee", employee)
	frappe.has_permission("Employee", "read", doc=employee_doc, throw=True)

	if not frappe.has_permission("Saudi Monthly Payroll", "read"):
		return []

	rows = frappe.db.sql(
		"""
		SELECT
			parent.name AS payroll,
			parent.period_label,
			parent.month,
			parent.year,
			parent.posting_date,
			parent.status,
			parent.payroll_journal_entry,
			child.gross_salary,
			child.total_deductions,
			child.net_salary,
			child.salary_mode
		FROM `tabSaudi Monthly Payroll Employee` child
		INNER JOIN `tabSaudi Monthly Payroll` parent ON parent.name = child.parent
		WHERE child.employee = %s
			AND parent.docstatus = 1
			AND IFNULL(parent.payroll_journal_entry, '') != ''
		ORDER BY parent.posting_date DESC, parent.modified DESC
		LIMIT %s
		""",
		(employee, limit),
		as_dict=True,
	)

	history = []
	for row in rows:
		period_label = row.period_label or f"{row.month} {row.year}"
		history.append(
			{
				"payroll": row.payroll,
				"period_label": period_label,
				"posting_date": str(row.posting_date) if row.posting_date else None,
				"status": row.status,
				"journal_entry": row.payroll_journal_entry,
				"gross_salary": flt(row.gross_salary),
				"total_deductions": flt(row.total_deductions),
				"net_salary": flt(row.net_salary),
				"salary_mode": row.salary_mode,
			}
		)

	return history


@frappe.whitelist()
def get_attendance_status():
	employee, profile = _require_employee_context()
	today_checkins = _get_todays_checkins(employee)
	location = _get_location_for_branch(profile.branch)
	voice_runtime = get_voice_runtime_status()
	voice_profile = get_employee_voice_profile_status(employee)

	last_log_type = None
	last_checkin_time = None
	if today_checkins:
		last = today_checkins[-1]
		last_log_type = last.log_type
		last_checkin_time = str(last.time)

	schedule = resolve_mobile_attendance_policy(employee, nowdate(), location)
	schedule["status"] = summarize_schedule_status(schedule, now_datetime(), last_log_type)

	today_attendance = frappe.db.get_value(
		"Saudi Daily Attendance",
		{"employee": employee, "attendance_date": nowdate(), "docstatus": 1},
		["name", "in_time", "out_time", "working_hours", "status", "late_entry", "early_exit"],
		as_dict=True,
	)

	return {
		"employee": employee,
		"employee_name": profile.employee_name,
		"department": profile.department,
		"designation": profile.designation,
		"image": profile.image,
		"branch": profile.branch,
		"last_log_type": last_log_type,
		"last_checkin_time": last_checkin_time,
		"today_checkins": today_checkins,
		"today_attendance": today_attendance,
		"location": location,
		"schedule": schedule,
		"voice_profile": voice_profile,
		"insights": _get_attendance_insights(employee),
		"leave_options": _get_leave_options(employee),
		"recent_leave_requests": _get_recent_leave_requests(employee),
		"verification_features": {
			"max_attachment_count": MAX_MOBILE_ATTACHMENTS,
			"max_attachment_size_mb": int(MAX_MOBILE_ATTACHMENT_SIZE / (1024 * 1024)),
			"voice_policy": schedule.get("voice_policy"),
			"voice_challenge_ttl_seconds": schedule.get("voice_challenge_ttl_seconds"),
			"voice_max_duration_seconds": schedule.get("voice_max_duration_seconds"),
			"voice_runtime_enabled": voice_runtime.get("enabled"),
			"voice_runtime_ready": voice_runtime.get("runtime_ready"),
			"voice_runtime_missing_dependencies": voice_runtime.get("missing_dependencies"),
			"voice_enrollment_required": bool(voice_runtime.get("enabled") and voice_profile.get("can_self_enroll")),
		},
	}


@frappe.whitelist()
def get_attendance_insights(month=None, year=None):
	employee, _profile = _require_employee_context()
	return _get_attendance_insights(employee, month=month, year=year)


@frappe.whitelist()
def issue_mobile_voice_challenge():
	employee, profile = _require_employee_context()
	location = _get_location_for_branch(profile.branch)
	policy = resolve_mobile_attendance_policy(employee, nowdate(), location)
	result = issue_voice_challenge(employee, policy.get("voice_challenge_ttl_seconds") or 300)
	result["voice_policy"] = policy.get("voice_policy")
	result["voice_max_duration_seconds"] = policy.get("voice_max_duration_seconds")
	result["has_voice_profile"] = get_employee_voice_profile_status(employee).get("has_voice_profile")
	return result


@frappe.whitelist()
def enroll_mobile_voice_profile(challenge_token=None, voice_payload_json=None):
	employee, _profile = _require_employee_context()
	voice_payload = _load_json_param(voice_payload_json, default=None)
	result = enroll_employee_voice_profile(employee, voice_payload, challenge_token)
	frappe.db.commit()
	return {
		**result,
		"message": _("تم تسجيل البصمة الصوتية بنجاح ويمكن استخدامها الآن في الحضور والانصراف."),
	}


@frappe.whitelist()
def do_mobile_checkin(
	latitude=None,
	longitude=None,
	verification_mode=None,
	verification_note=None,
	attachments_json=None,
	challenge_token=None,
	voice_payload_json=None,
):
	latitude = _coerce_float(latitude)
	longitude = _coerce_float(longitude)
	attachments = _load_json_param(attachments_json, default=[])
	voice_payload = _load_json_param(voice_payload_json, default=None)

	employee, profile = _require_employee_context()
	branch = profile.branch
	location = _get_location_for_branch(branch)
	voice_runtime = get_voice_runtime_status()
	voice_profile = get_employee_voice_profile_status(employee)
	if attachments:
		frappe.throw(_("مرفقات الحضور والانصراف أزيلت. استخدم الملاحظة أو التحقق الصوتي المخصص بدلاً منها."))
	if voice_runtime.get("enabled") and voice_profile.get("can_self_enroll"):
		message = _("يجب تسجيل البصمة الصوتية لأول مرة من صفحة الحضور قبل تسجيل أي حركة.")
		if not voice_runtime.get("runtime_ready"):
			message = _("تسجيل البصمة الصوتية الأولى مطلوب، لكن محرك التحقق الصوتي غير جاهز في البيئة الحالية.")
		frappe.throw(message, frappe.PermissionError)

	if location:
		if latitude is None or longitude is None:
			frappe.throw(_("تعذّر الحصول على إحداثيات GPS. يرجى السماح بإذن الموقع وإعادة المحاولة."))
		distance = _distance_meters(latitude, longitude, flt(location.latitude), flt(location.longitude))
		allowed = location.allowed_radius_meters or 100
		if distance > allowed:
			frappe.throw(
				_("أنت بعيد عن الفرع بمسافة {0} متر. الحد المسموح به هو {1} متر.").format(int(distance), int(allowed))
			)
	else:
		frappe.logger("saudi_hr").warning(
			f"GPS bypass: employee {employee} checked in without location validation (no Attendance Location for branch '{branch}')."
		)

	today_checkins = _get_todays_checkins(employee)
	last_log = today_checkins[-1] if today_checkins else None
	log_type = "OUT" if (last_log and last_log.log_type == "IN") else "IN"
	now = now_datetime()
	policy = resolve_mobile_attendance_policy(employee, nowdate(), location)
	variance = calculate_attendance_variance(log_type, now, policy)
	voice_status = VOICE_VERIFICATION_STATUS_NOT_REQUIRED
	voice_result = None
	voice_required = policy.get("voice_policy") == VOICE_POLICY_REQUIRED
	voice_enabled = policy.get("voice_policy") and policy.get("voice_policy") != VOICE_POLICY_DISABLED
	if voice_required and not voice_payload:
		frappe.throw(_("هذا الموقع يتطلب التحقق الصوتي قبل تسجيل الحركة."), frappe.PermissionError)
	if voice_payload:
		voice_result = verify_checkin_voice(employee, voice_payload, challenge_token)
		voice_status = VOICE_VERIFICATION_STATUS_PASSED

	checkin = frappe.new_doc("Saudi Employee Checkin")
	checkin.update(
		{
			"employee": employee,
			"log_type": log_type,
			"time": now,
			"latitude": latitude,
			"longitude": longitude,
			"device_id": "mobile-gps",
			"verification_mode": _build_verification_mode(verification_mode, bool(voice_result)),
			"verification_note": verification_note,
			"attendance_location": location.name if location else None,
			"shift_type": policy.get("shift_type"),
			"expected_start_time": policy.get("expected_start"),
			"expected_end_time": policy.get("expected_end"),
			"late_minutes": variance.get("late_minutes"),
			"early_exit_minutes": variance.get("early_exit_minutes"),
			"voice_verification_status": voice_status,
			"voice_challenge_text": (voice_result or {}).get("challenge_text"),
			"voice_transcript": (voice_result or {}).get("transcript"),
			"anti_spoof_score": (voice_result or {}).get("anti_spoof_score"),
			"speech_match_score": (voice_result or {}).get("speech_match_score"),
			"speaker_match_score": (voice_result or {}).get("speaker_match_score"),
		}
	)
	assert_doctype_permissions("Saudi Employee Checkin", "create", doc=checkin)
	checkin.insert()
	frappe.db.commit()

	result = {
		"success": True,
		"log_type": log_type,
		"checkin_name": checkin.name,
		"checkin_time": str(now),
		"attendance_name": None,
		"attached_files": [],
		"voice_verification": voice_result,
		"message": _("تم تسجيل الحضور بنجاح في {0}").format(now.strftime("%H:%M"))
		if log_type == "IN"
		else _("تم تسجيل الانصراف بنجاح في {0}").format(now.strftime("%H:%M")),
	}

	if log_type == "OUT":
		in_checkin = next((item for item in reversed(today_checkins) if item.log_type == "IN"), None)
		if in_checkin:
			in_time = get_datetime(in_checkin.time)
			out_time = now
			working_hours = time_diff_in_hours(out_time, in_time)
			out_variance = calculate_attendance_variance("OUT", out_time, policy)

			existing = frappe.db.get_value(
				"Saudi Daily Attendance",
				{"employee": employee, "attendance_date": nowdate(), "docstatus": 1},
				"name",
			)
			if not existing:
				attendance = frappe.new_doc("Saudi Daily Attendance")
				attendance.update(
					{
						"employee": employee,
						"attendance_date": nowdate(),
						"status": "Present / حاضر",
						"working_hours": round(working_hours, 2),
						"in_time": in_time,
						"out_time": out_time,
						"attendance_location": location.name if location else None,
						"shift_type": policy.get("shift_type"),
						"expected_start_time": policy.get("expected_start"),
						"expected_end_time": policy.get("expected_end"),
						"late_entry": variance.get("late_entry"),
						"late_minutes": variance.get("late_minutes"),
						"early_exit": out_variance.get("early_exit") or (1 if working_hours < _get_contract_hours_per_day(employee) else 0),
						"early_exit_minutes": out_variance.get("early_exit_minutes"),
					}
				)
				assert_doctype_permissions("Saudi Daily Attendance", ("create", "submit"), doc=attendance)
				attendance.insert()
				attendance.submit()

				all_log_names = [item.name for item in today_checkins] + [checkin.name]
				for log_name in all_log_names:
					frappe.db.set_value("Saudi Employee Checkin", log_name, "attendance", attendance.name)
				frappe.db.commit()

				result["attendance_name"] = attendance.name
				result["working_hours"] = round(working_hours, 2)
				result["message"] = _("تم تسجيل الانصراف. مجموع ساعات العمل: {0} ساعة.").format(
					round(working_hours, 2)
				)

	return result


@frappe.whitelist()
def submit_mobile_leave_request(
	request_type,
	start_date,
	end_date=None,
	reason=None,
	leave_subtype=None,
	relationship_to_deceased=None,
	medical_certificate_no=None,
	hospital_name=None,
	expected_delivery_date=None,
	actual_delivery_date=None,
	half_day=0,
	attachments_json=None,
):
	employee, profile = _require_employee_context()
	attachments = _load_json_param(attachments_json, default=[])
	request_type = (request_type or "").strip()
	doc = _build_mobile_leave_doc(
		employee,
		profile,
		request_type,
		attachments,
		{
			"start_date": start_date,
			"end_date": end_date,
			"reason": reason,
			"leave_subtype": leave_subtype,
			"relationship_to_deceased": relationship_to_deceased,
			"medical_certificate_no": medical_certificate_no,
			"hospital_name": hospital_name,
			"expected_delivery_date": expected_delivery_date,
			"actual_delivery_date": actual_delivery_date,
			"half_day": half_day,
		},
	)

	assert_doctype_permissions(doc.doctype, "create", doc=doc)
	doc.insert()
	attached_files = _attach_files(doc, attachments)
	frappe.db.commit()

	return {
		"doctype": doc.doctype,
		"name": doc.name,
		"attached_files": attached_files,
		"message": _("تم حفظ طلب الإجازة بنجاح وهو الآن بانتظار المراجعة."),
	}


@frappe.whitelist()
def resolve_location_reference_api(plus_code=None, latitude=None, longitude=None, geolocation=None, address_reference=None):
	_require_employee_context()

	return resolve_location_reference(
		plus_code=plus_code,
		latitude=latitude,
		longitude=longitude,
		geolocation=geolocation,
		address_reference=address_reference,
	)


@frappe.whitelist()
def get_available_locations():
	employee, profile = _require_employee_context()
	branch = profile.branch
	filters = {"is_active": 1}
	if not ELEVATED_ROLES.intersection(set(frappe.get_roles())):
		filters["branch"] = branch

	return frappe.get_all(
		"Attendance Location",
		filters=filters,
		fields=[
			"name",
			"location_name",
			"branch",
			"latitude",
			"longitude",
			"allowed_radius_meters",
			"plus_code",
			"location_source",
		],
		order_by="location_name asc",
	)


@frappe.whitelist()
def sync_branch_employee_directory():
	from saudi_hr.saudi_hr.doctype.saudi_hr_settings.saudi_hr_settings import sync_branch_employee_directory as _sync

	return _sync()


@frappe.whitelist()
def download_employee_branch_template():
	from saudi_hr.saudi_hr.doctype.saudi_hr_settings.saudi_hr_settings import (
		download_employee_branch_template as _download,
	)

	return _download()


@frappe.whitelist()
def import_employee_branch_template(file_url=None):
	from saudi_hr.saudi_hr.doctype.saudi_hr_settings.saudi_hr_settings import import_employee_branch_template as _import

	return _import(file_url=file_url)


# ─── Payroll Adjustment Items Helpers ─────────────────────────────────────────

@frappe.whitelist()
def fetch_approved_overtime_for_payroll(payroll_name):
	"""
	Fetches all approved, unlinked Overtime Requests for the payroll period
	and populates adjustment items on matching employee rows.
	جلب طلبات العمل الإضافي المعتمدة وغير المرتبطة بمسير رواتب وإضافتها كبنود تعديل.
	"""
	doc = frappe.get_doc("Saudi Monthly Payroll", payroll_name)
	frappe.has_permission("Saudi Monthly Payroll", "write", doc=doc, throw=True)

	month_map = {
		"January / يناير": 1, "February / فبراير": 2, "March / مارس": 3,
		"April / أبريل": 4, "May / مايو": 5, "June / يونيو": 6,
		"July / يوليو": 7, "August / أغسطس": 8, "September / سبتمبر": 9,
		"October / أكتوبر": 10, "November / نوفمبر": 11, "December / ديسمبر": 12,
	}
	month_num = month_map.get(doc.month, 0)
	if not month_num:
		frappe.throw(_("Invalid month in payroll"))

	import calendar as cal
	last_day = cal.monthrange(int(doc.year), month_num)[1]
	period_start = f"{doc.year}-{month_num:02d}-01"
	period_end = f"{doc.year}-{month_num:02d}-{last_day:02d}"

	overtime_requests = frappe.get_all(
		"Overtime Request",
		filters={
			"docstatus": 1,
			"approval_status": "Approved / موافق",
			"date": ["between", [period_start, period_end]],
			"payroll_period": ["in", ["", None]],
			"company": doc.company,
		},
		fields=["name", "employee", "employee_name", "overtime_hours", "overtime_amount", "date"],
	)

	if not overtime_requests:
		frappe.msgprint(_("No approved overtime requests found for this period. لا يوجد طلبات عمل إضافي معتمدة لهذه الفترة."))
		return {"added": 0}

	# Build employee lookup for rows included in this payroll
	payroll_employees = {row.employee for row in doc.employees if row.employee}

	added = 0
	for ot in overtime_requests:
		if ot.employee not in payroll_employees:
			continue

		# Check if already added
		already_exists = False
		for item in getattr(doc, "adjustment_items", []) or []:
			if item.reference_doctype == "Overtime Request" and item.reference_name == ot.name:
				already_exists = True
				break
		if already_exists:
			continue

		doc.append("adjustment_items", {
			"employee": ot.employee,
			"item_type": "Addition / إضافة",
			"description": _("Overtime {0}h on {1} / عمل إضافي {0} ساعة بتاريخ {1}").format(
				ot.overtime_hours, ot.date
			),
			"amount": flt(ot.overtime_amount),
			"reference_doctype": "Overtime Request",
			"reference_name": ot.name,
		})

		# Mark OT as linked
		frappe.db.set_value("Overtime Request", ot.name, "payroll_period", doc.name)
		added += 1

	if added:
		doc.save()
		frappe.msgprint(
			_("Added {0} overtime adjustment items. تمت إضافة {0} بنود عمل إضافي.").format(added),
			indicator="green",
		)

	return {"added": added}


@frappe.whitelist()
def add_payroll_adjustment_item(payroll_name, employee, item_type, description, amount):
	"""
	Add a single adjustment item to a payroll employee row.
	إضافة بند تعديل واحد لموظف في مسير الرواتب.
	"""
	doc = frappe.get_doc("Saudi Monthly Payroll", payroll_name)
	frappe.has_permission("Saudi Monthly Payroll", "write", doc=doc, throw=True)

	target_row = None
	for row in doc.employees:
		if row.employee == employee:
			target_row = row
			break

	if not target_row:
		frappe.throw(_("Employee {0} not found in payroll. الموظف {0} غير موجود في مسير الرواتب.").format(employee))

	doc.append("adjustment_items", {
		"employee": employee,
		"item_type": item_type,
		"description": description,
		"amount": flt(amount),
	})
	doc.save()

	return {"status": "ok"}
